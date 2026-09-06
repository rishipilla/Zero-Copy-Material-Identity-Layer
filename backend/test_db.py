from app.db.database import engine

try:
    with engine.connect() as connection:
        print("SUCCESS: Connected to PostgreSQL!")
except Exception as e:
    print("ERROR:", e)