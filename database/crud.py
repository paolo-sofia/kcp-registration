from datetime import date, datetime, timedelta
from typing import List

from sqlalchemy import func
from sqlalchemy.orm import Session

from database import models, schemas
from database.database import local_timezone


def get_user_by_codice_fiscale(db: Session, codice_fiscale: str) -> schemas.User:
    return db.query(models.User).filter(models.User.codice_fiscale == codice_fiscale).first()


def get_user_by_id(db: Session, user_id: int) -> schemas.User:
    return db.query(models.User).filter(models.User.id == user_id).first()

def get_users(db: Session, skip: int = 0, limit: int = 100) -> List[schemas.User]:
    return db.query(models.User).offset(skip).limit(limit).all()


def add_user(db: Session, user: schemas.UserCreate, renew: bool) -> schemas.User:
    if not renew:
        db_user = schemas.UserCreate(**user.model_dump())
        db.add(db_user)
        db.commit()
        db.refresh(db_user)
        return db_user.id

    return db.query(models.User).filter(models.User.codice_fiscale == user.codice_fiscale).first()


def add_child(db: Session, child: schemas.UserCreate, parent_id: int) -> int:
    db_child = schemas.UserCreate(**child.model_dump())
    db.add(db_child)
    db.commit()
    db.refresh(db_child)

    child_user = schemas.ChildCreate(**{
        models.Child.id_figlio  : db_child.id,
        models.Child.id_genitore: parent_id
    })
    db.add(child_user)
    db.commit()
    db.refresh(child_user)

    return db_child.id

def add_children(db: Session, children: List[schemas.UserCreate], parent_id: int) -> List[int]:
    children_ids: List[int] = []

    for child in children:
        db_child = schemas.UserCreate(**child.model_dump())
        db.add(db_child)
        db.commit()
        db.refresh(db_child)

        children_ids.append(db_child.id)

        child_user = schemas.ChildCreate(**{
            models.Child.id_figlio  : db_child.id,
            models.Child.id_genitore: parent_id
        })
        db.add(child_user)
        db.commit()
        db.refresh(child_user)

    return children_ids

def remove_children_by_id(db: Session, children_ids: List[int]):
    for child_id in children_ids:
        if result := db.query(models.User).filter(models.User.id == child_id).first():
            db.delete(result)
    db.commit()

def remove_child_by_id(db: Session, child_id: int):
    if result := db.query(models.User).filter(models.User.id == child_id).first():
        db.delete(result)
        db.commit()


def add_group(db: Session, users: List[schemas.User], group_name: str) -> int:
    now: datetime = datetime.now(tz=local_timezone)
    max_group_id = db.query(func.max(models.Group.id)).filter(models.Group.data_assegnazione == now.today()).scalar()
    days_behind: int = 0
    while not max_group_id:
        days_behind += 1
        other_day: date = (now - timedelta(days=days_behind)).date()
        max_group_id = db.query(func.max(models.Group.id)).filter(models.Group.data_assegnazione == other_day).scalar()

    max_group_id = (max_group_id + 1) % 101
    db_group = schemas.GroupCreate(**{
        models.Group.id_ticket.name        : max_group_id,
        models.Group.data_assegnazione.name: now,
        models.Group.nome.name             : group_name
    })
    db.add(db_group)
    db.commit()
    db.refresh(db_group)

    for user in users:
        db_user_group = schemas.UserGroupCreate(**{
            models.UserGroup.group_id.name       : db_group.id,
            models.UserGroup.user_id.name        : user.id,
            models.UserGroup.assignment_date.name: now
        }
                                  )
        db.add(db_user_group)
        db.commit()
        db.refresh(db_user_group)

    return db_group.id
