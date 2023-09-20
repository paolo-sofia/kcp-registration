import logging
from typing import Dict, List, Union

import uvicorn
from fastapi import Depends, FastAPI
from sqlalchemy.orm import Session

from database import crud, models, schemas
from database.database import SessionLocal, engine
from database.schemas import Group

logger = next(logging.getLogger(name) for name in logging.root.manager.loggerDict)
models.Base.metadata.create_all(bind=engine)

app = FastAPI()


# Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@app.post("/users/")
async def sign_up(user: schemas.UserCreate, db: Session = Depends(get_db)):
    try:
        return crud.add_user(db=db, user=user)
    except Exception as e:
        return {"message": "Data not found", "data": f"{e}", "original": user.model_dump()}


@app.get("/users/{fiscal_code}")
async def get_user(fiscal_code: str, db: Session = Depends(get_db)):
    try:
        return crud.get_user_by_codice_fiscale(db=db, codice_fiscale=fiscal_code)
    except Exception as e:
        return {"message": "Data not found", "data": f"{e}"}


@app.get("/users/")
async def get_user(db: Session = Depends(get_db)):
    try:
        return crud.get_users(db=db)
    except Exception as e:
        return {"message": "Data not found", "data": f"{e}"}


@app.delete("/childrens/")
async def remove_children(children_id: List[int], db: Session = Depends(get_db)) -> Union[bool, Dict[str, str]]:
    try:
        crud.remove_children_by_id(db, children_id)
        return True
    except Exception as e:
        return {"message": "Data not found", "data": f"{e}"}


@app.post("/childrens/{parent_id}")
async def add_children(parent_id: int, children: List[schemas.UserCreate], db: Session = Depends(get_db)) -> \
        Dict[str, str] | List[int]:
    try:
        return crud.add_children(db=db, children=children, parent_id=parent_id)
    except Exception as e:
        return {"message": f"Failed to execute query: {e}", "data": ""}


@app.post("/groups/")
async def add_group(users: List[schemas.User], group_name: str, ticket_id: int, db: Session = Depends(get_db)) \
        -> Group | Dict[str, str]:
    try:
        return crud.add_group(db=db, users=users, group_name=group_name, ticket_id=ticket_id)
    except Exception as e:
        return {"message": f"Failed to execute query: {e}", "data": ""}


@app.put("/users/")
async def update_user(user: schemas.UserBase, db: Session = Depends(get_db)) -> int | Dict[str, str]:
    logger.warning(f"data received by fast api update_user {user}")
    try:
        return crud.update_user(db=db, user=user).id
    except Exception as e:
        return {"message": f"Failed to execute query: {e}", "data": ""}


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
