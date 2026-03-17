import asyncio
from app.core.database import AsyncSessionLocal
from app.models.user import User
from app.core.security import hash_password  # <--- Deenni marchu
from sqlalchemy import select

async def create_initial_user():
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(User).where(User.username == "narasimha"))
        if result.scalar_one_or_none():
            print("Bava, User already exists!")
            return

        # hash_password vadu (as per your security.py)
        hashed = hash_password("password123") 
        new_user = User(username="narasimha", hashed_password=hashed)
        
        session.add(new_user)
        await session.commit()
        print("Bava, 'narasimha' user created successfully!")

if __name__ == "__main__":
    asyncio.run(create_initial_user())