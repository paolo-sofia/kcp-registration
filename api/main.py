from typing import Dict, List, Union

import uvicorn
from fastapi import Depends, FastAPI, HTTPException
from sqlalchemy.orm import Session

from database import crud, models, schemas
from database.database import SessionLocal, engine

models.Base.metadata.create_all(bind=engine)

app = FastAPI()

# Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@app.post("/signup/")
async def sign_up(user: schemas.UserCreate, renew: bool, db: Session = Depends(get_db)):
    if not user.accept_policy:
        raise HTTPException(status_code=400, detail="You must accept the privacy policy")
    try:
        return crud.add_user(db=db, user=user, renew=renew)
    except Exception:
        return {"message": "Data not found", "data": ""}

@app.post("/user/")
async def get_user(codicefiscale: str, db: Session = Depends(get_db)):
    try:
        return crud.get_user_by_codice_fiscale(db=db, codice_fiscale=codicefiscale)
    except Exception:
        return {"message": "Data not found", "data": ""}

@app.post("/remove_children/")
async def remove_children(children_id: List[int], db: Session = Depends(get_db)) -> Union[bool, Dict[str, str]]:
    try:
        crud.remove_children_by_id(db, children_id)
        return True
    except Exception:
        return  {'data': 'children_removed'}

@app.post("/add_children/")
async def add_children(children: List[schemas.UserCreate], parent_id: int, db: Session = Depends(get_db)) -> \
        Dict[str, str] | List[int]:
    try:
        return crud.add_children(db=db, children=children, parent_id=parent_id)
    except Exception as e:
        return {'message': f'Failed to execute query: {e}','data': ''}


@app.post("/add_group/")
async def add_group(users: List[schemas.User], group_name: str, db: Session = Depends(get_db)) -> Dict[str, str] | int:
    try:
        return crud.add_group(db=db, users=users, group_name=group_name)
    except Exception as e:
        return {'message': f'Failed to execute query: {e}', 'data': ''}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
