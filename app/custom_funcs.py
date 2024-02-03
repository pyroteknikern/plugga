from app.models import User
from sqlalchemy import text
from sqlalchemy.future import select


async def get_user_by_username(db, user: str):
    sql_statement = text(f"SELECT * FROM users WHERE username='{user}'")
    res = await db.scalars(select(User).from_statement(sql_statement))
    result = res.all()

    if not len(result):
        return None

    return result[0]
