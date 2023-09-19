from datetime import datetime
from typing import Optional

from pydantic import BaseModel


## User part
class UserBase(BaseModel):
    codice_fiscale: str
    nome: str
    cognome: str
    data_nascita: str
    luogo_nascita: Optional[str] = ''
    luogo_residenza: Optional[str] = ''
    via_residenza: Optional[str] = ''
    telefono: Optional[str] = ''
    tipo_utente: Optional[str] = ''
    attivita_utente: Optional[str] = ''

class UserCreate(UserBase):
    pass

class User(UserBase):
    id: int
    data_registrazione: str

    class Config:
        orm_mode = True


## Child part
class ChildBase(BaseModel):
    id_genitore: int
    id_figlio: int

class ChildCreate(ChildBase):
    pass

class Child(ChildBase):
    id: int

    class Config:
        orm_mode = True


## Group part
class GroupBase(BaseModel):
    id_ticket: int
    nome: str
    data_assegnazione: datetime

class GroupCreate(GroupBase):
    pass

class Group(GroupCreate):
    id: int

    class Config:
        orm_mode = True


## UserGroup part
class UserGroupBase(BaseModel):
    group_id: int
    user_id: int
    assignment_date: datetime

class UserGroupCreate(UserGroupBase):
    pass

class UserGroup(UserGroupCreate):
    class Config:
        orm_mode = True
