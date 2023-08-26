from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime

app = FastAPI()

DATABASE_URL = "postgresql://username:password@localhost/dbname"
SECRET_KEY = "your-secret-key"

Base = declarative_base()

class UserDB(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    surname = Column(String, index=True)
    birth_date = Column(String)
    birth_place = Column(String)
    fiscal_code = Column(String, index=True)
    # hashed_password = Column(String)

engine = create_engine(DATABASE_URL, pool_pre_ping=True)
Base.metadata.create_all(bind=engine)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# password_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

class UserCreate(BaseModel):
    name: str
    surname: str
    birth_date: str
    birth_place: str
    fiscal_code: str
    hashed_password: str
    accept_policy: bool

# def get_password_hash(password):
#     return password_context.hash(password)
#
# def verify_password(plain_password, hashed_password):
#     return password_context.verify(plain_password, hashed_password)

def is_user_adult(birth_date: str) -> bool:
    birth_date = datetime.strptime(birth_date, "%Y-%m-%d")
    today = datetime.now()
    age = today.year - birth_date.year - ((today.month, today.day) < (birth_date.month, birth_date.day))
    return age >= 18

@app.post("/signup/")
async def sign_up(user: UserCreate):
    if not user.accept_policy:
        raise HTTPException(status_code=400, detail="You must accept the privacy policy")

    if not is_user_adult(user.birth_date):
        parent_user = UserCreate(
            name="Parent",
            surname="",
            birth_date="",
            birth_place="",
            fiscal_code="parent_fiscal_code",
            # hashed_password=get_password_hash("parent_password"),
            accept_policy=True
        )
        session = SessionLocal()
        db_user = UserDB(**parent_user.dict())
        session.add(db_user)
        session.commit()
        session.refresh(db_user)
        session.close()

    db_user = UserDB(**user.dict(),
                     # hashed_password=get_password_hash(user.hashed_password)
                     )
    session = SessionLocal()
    session.add(db_user)
    session.commit()
    session.refresh(db_user)
    session.close()

    return {"message": "User signed up successfully"}

# OAuth2 and token handling...

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
