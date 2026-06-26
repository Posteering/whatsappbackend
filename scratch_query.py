from app.database.session import engine
from sqlalchemy import text
with engine.connect() as conn:
    res = conn.execute(text("SELECT role, content FROM messages ORDER BY created_at DESC LIMIT 5")).fetchall()
    for r in res:
        print(f"[{r[0].upper()}] {r[1]}")
