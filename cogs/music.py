import asyncio
import discord
import requests
import youtube_dl
import cogs.utilities as utilities
from discord.ext import commands

FFMPEG_OPTIONS = {'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5', 'options': '-vn'}

sessions = []


def check_session(self, ctx):
    if len(sessions) > 0:
        for i in sessions:
            if i.guild == ctx.guild and i.channel == ctx.author.voice.channel:
                return i
        session = utilities.Session(
            ctx.guild, ctx.author.voice.channel, id=len(sessions))
        sessions.append(session)
        return session
    else:
        session = utilities.Session(ctx.guild, ctx.author.voice.channel, id=0)
        sessions.append(session)
        return session


class Music(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

    def prepare_continue_queue(self, ctx):
        fut = asyncio.run_coroutine_threadsafe(self.continue_queue(ctx), self.bot.loop)
        try:
            fut.result()
        except Exception as e:
            print(e)

    async def continue_queue(self, ctx):
        session = check_session(self, ctx)
        if not session.q.theres_next():
            await ctx.send("Queue finished")
            return

        session.q.next()

        voice = discord.utils.get(self.bot.voice_clients, guild=session.guild)
        source = await discord.FFmpegOpusAudio.from_probe(session.q.current_music.url, **FFMPEG_OPTIONS)

        if voice.is_playing():
            voice.stop()

        voice.play(source, after=lambda e: self.prepare_continue_queue(self, ctx))
        await ctx.send(session.q.current_music.thumb)
        await ctx.send(f"Playing: {session.q.current_music.title}")

    @commands.command(name='play')
    async def play(self, ctx, *, arg):
        try:
            voice_channel = ctx.author.voice.channel
        except AttributeError as e:
            print(e)
            await ctx.send("You're not connected to a voice channel, idiot")
            return
        session = check_session(self, ctx)
        with youtube_dl.YoutubeDL({'format': 'bestaudio/best', 'noplaylist': 'True'}) as ydl:
            try:
                requests.get(arg)
            except Exception as e:
                print(e)
                info = ydl.extract_info(f"ytsearch:{arg}", download=False)[
                    'entries'][0]
            else:
                info = ydl.extract_info(arg, download=False)
        url = info['formats'][0]['url']
        thumb = info['thumbnails'][0]['url']
        title = info['title']
        session.q.enqueue(title, url, thumb)
        voice = discord.utils.get(self.bot.voice_clients, guild=ctx.guild)
        if not voice:
            await voice_channel.connect()
            voice = discord.utils.get(self.bot.voice_clients, guild=ctx.guild)
        if voice.is_playing():
            await ctx.send(thumb)
            await ctx.send(f"Added to queue: {title}")
            return
        else:
            await ctx.send(thumb)
            await ctx.send(f"Playing: {title}")
            session.q.set_last_as_current()
            voice = discord.utils.get(self.bot.voice_clients, guild=ctx.guild)
            source = await discord.FFmpegOpusAudio.from_probe(url, **FFMPEG_OPTIONS)
            voice.play(source, after=lambda ee: self.prepare_continue_queue(self, ctx))

    @commands.command(name='next', aliases=['skip'])
    async def skip(self, ctx):
        session = check_session(self, ctx)
        if not session.q.theres_next():
            await ctx.send("Queue is empty, idiot")
            return
        voice = discord.utils.get(self.bot.voice_clients, guild=session.guild)
        if voice.is_playing():
            voice.stop()
            return
        else:
            session.q.next()
            source = await discord.FFmpegOpusAudio.from_probe(session.q.current_music.url, **FFMPEG_OPTIONS)
            voice.play(source, after=lambda e: self.prepare_continue_queue(self, ctx))
            return

    @commands.command(name='print')
    async def print_info(self, ctx):
        session = check_session(self, ctx)
        await ctx.send(f"Session ID: {session.id}")
        await ctx.send(f"Current: {session.q.current_music.title}")
        queue = [q[0] for q in session.q.queue]
        await ctx.send(f"Queue: {queue}")

    @commands.command(name='leave')
    async def leave(self, ctx):
        voice = discord.utils.get(self.bot.voice_clients, guild=ctx.guild)
        if voice.is_connected:
            check_session(self, ctx).q.clear_queue()
            await voice.disconnect()
        else:
            await ctx.send("I am not connected to a voice channel, idiot")

    @commands.command(name='pause')
    async def pause(self, ctx):
        voice = discord.utils.get(self.bot.voice_clients, guild=ctx.guild)
        if voice.is_playing():
            voice.pause()
        else:
            await ctx.send("No music playing, idiot")

    @commands.command(name='resume')
    async def resume(self, ctx):
        voice = discord.utils.get(self.bot.voice_clients, guild=ctx.guild)
        if voice.is_paused:
            voice.resume()
        else:
            await ctx.send("No music i paused, idiot")

    @commands.command(name='stop')
    async def stop(self, ctx):
        session = check_session(self, ctx)
        voice = discord.utils.get(self.bot.voice_clients, guild=ctx.guild)
        if voice.is_playing:
            voice.stop()
            session.q.clear_queue()
        else:
            await ctx.send("No music playing, idiot")


async def setup(bot):
    await bot.add_cog(Music(bot))
