import logging
from datetime import datetime
from typing import Any, List, Type

from sqlalchemy.orm import Session

from database import models, schemas
from database.database import local_timezone

logger = next(logging.getLogger(name) for name in logging.root.manager.loggerDict)

def add_object(db: Session, obj: Any) -> Any:
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj

def get_user_by_codice_fiscale(db: Session, codice_fiscale: str) -> Type[schemas.User]:
    return db.query(models.User).filter(models.User.codice_fiscale == codice_fiscale.upper()).first()

def get_user_by_id(db: Session, user_id: int) -> Type[schemas.User]:
    return db.query(models.User).filter(models.User.id == user_id).first()

def get_users(db: Session, skip: int = 0, limit: int = 100) -> List[Type[schemas.User]]:
    return db.query(models.User).offset(skip).limit(limit).all()

def add_user(db: Session, user: schemas.UserCreate) -> Type[schemas.User]:
    if user_db := get_user_by_codice_fiscale(db, user.codice_fiscale.upper()):
        return user_db

    db_user = models.User(**user.model_dump())
    return add_object(db, db_user)

def add_child(db: Session, child: schemas.UserCreate, parent_id: int) -> schemas.User:

    db_child = get_user_by_codice_fiscale(db, child.codice_fiscale)
    if not db_child:
        db_child = models.User(**child.model_dump())
        db_child = add_object(db, db_child)

    child_user = models.Child(**{
        models.Child.id_figlio  : db_child.id,
        models.Child.id_genitore: parent_id
    })

    add_object(db, child_user)

    return db_child

def add_children(db: Session, children: List[schemas.UserCreate], parent_id: int) -> List[int]:
    children_ids: List[int] = []

    for child in children:
        logger.warning(f'child {child}')
        db_child = get_user_by_codice_fiscale(db, child.codice_fiscale)
        logger.warning(f'child query return {db_child}')
        if not db_child:
            db_child = models.User(**child.model_dump())
            db_child = add_object(db, db_child)
            logger.warning('child added to db')

        children_ids.append(db_child.id)

        child_user = models.Child(**{
            models.Child.id_figlio.name   : db_child.id,
            models.Child.id_genitore.name : parent_id
        })
        add_object(db, child_user)

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

def add_group(db: Session, users: List[schemas.User], group_name: str, ticket_id: int) -> schemas.Group:
    now: datetime = datetime.now(tz=local_timezone)

    if ticket_id > 100:
        ticket_id %= 101

    db_group = models.Group(**{
        models.Group.id_ticket.name        : ticket_id,
        models.Group.data_assegnazione.name: now,
        models.Group.nome.name             : group_name
    })
    db.add(db_group)
    db.commit()
    db.refresh(db_group)

    for user in users:
        db_user_group = models.UserGroup(**{
            models.UserGroup.group_id.name       : db_group.id,
            models.UserGroup.user_id.name        : user.id,
            models.UserGroup.assignment_date.name: now
        }
                                  )
        add_object(db, db_user_group)

    return db_group

def update_user(db: Session, user: schemas.UserBase) -> Type[models.User]:
    db_user = get_user_by_codice_fiscale(db, user.codice_fiscale.upper())
    if not db_user:
        raise Exception('User not present in the db')

    update_dict = {
        models.User.codice_fiscale.name: user.codice_fiscale.upper(),
        models.User.nome.name: user.nome,
        models.User.cognome.name: user.cognome,
        models.User.data_nascita.name: user.data_nascita,
        models.User.luogo_nascita.name: user.luogo_nascita,
        models.User.luogo_residenza.name: user.luogo_residenza,
        models.User.via_residenza.name: user.via_residenza,
        models.User.telefono.name: user.telefono,
        models.User.data_registrazione.name: datetime.today().date()
    }
    matched_rows: int = db.query(models.User).filter(models.User.id == db_user.id).update(update_dict)
    db.commit()
    db.refresh(db_user)

    if matched_rows == 1:
        return db_user
    else:
        raise Exception(f'Error while updating user {db_user.nome} {db_user.cognome}')

def renew_user(db: Session, fiscal_code: str) -> bool:
    db_user = get_user_by_codice_fiscale(db, fiscal_code)
    if not db_user:
        raise Exception('User not present in the db')

    update_dict = {schemas.User.data_registrazione: datetime.now(tz=local_timezone)}

    return db.query(models.User).filter(models.User.codice_fiscale == db_user.codice_fiscale).update(update_dict) == 1
