import praw
import random
import os
import logging


meme_max = 200
link_list = []


def get_link() -> str:
    global link_list
    if link_list == []:
        scrape("memes")
    link = random.choice(link_list)
    link_list.remove(link)
    return link


def scrape(subreddit_name: str):
    global link_list
    posturl_list = []
    posttitle_list = []
    filetypes = ["png", "jpg", "jpeg", "gif"]
    clientSecret = os.getenv("clientSecret")
    clientId = os.getenv("clientId")
    reddit = praw.Reddit(client_id=clientId,
                         client_secret=clientSecret,
                         user_agent=os.getenv("userAgent"))
    subreddit = reddit.subreddit(subreddit_name)
    top_post = subreddit.top("week", limit=meme_max)
    for post in top_post:
        for sufix in filetypes:
            if post.url.endswith(sufix):
                posturl = post.url
                posttitle = post.title
                posturl_list.append(posturl)
                posttitle_list.append(posttitle)
                break
    logging.info("Scrape successful. " + str(len(posturl_list)))
    link_list = posturl_list
