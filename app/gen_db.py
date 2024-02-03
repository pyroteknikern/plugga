from sqlalchemy.ext.asyncio import (create_async_engine,
                                    async_sessionmaker)
from app.models import Base

engine = create_async_engine("sqlite+aiosqlite:///db.sqlite3",
                             connect_args={"check_same_thread": False})
SessionLocal = async_sessionmaker(engine)


async def gen_db():
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)
    db = SessionLocal()
    return db
