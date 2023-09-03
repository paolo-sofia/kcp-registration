from datetime import datetime

from sqlalchemy import (
    Column,
    Date,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
)
from sqlalchemy.orm import relationship

from database.database import Base, local_timezone


class User(Base):
    __tablename__ = "users"
    __table_args__ = (
        Index("idx_codice_fiscale", "codice_fiscale"),
        Index("idx_name_surname", "nome", "cognome")
        )

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    nome = Column(String(50), index=True)
    cognome = Column(String(50), index=True)
    data_nascita = Column(Date)
    luogo_nascita = Column(String(100), nullable=True)
    codice_fiscale = Column(String(16), index=True)
    data_registrazione = Column(Date, default=datetime.today)

    utente_genitore = relationship("Child", back_populates="genitore")
    utente_figlio = relationship("Child", back_populates="figlio")
    utente_gruppo_fk = relationship("UserGroup", back_populates="utente_gruppo")

class Child(Base):
    __tablename__ = "children"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    id_genitore = Column(Integer, ForeignKey("users.id", onupdate='CASCADE', ondelete='CASCADE'), nullable=True)
    id_figlio = Column(Integer, ForeignKey("users.id", onupdate='CASCADE', ondelete='CASCADE'), nullable=True)

    genitore = relationship("User", back_populates="utente_genitore")
    figlio = relationship("User", back_populates="utente_figlio")


class Group(Base):
    __tablename__ = "groups"
    __table_args__ = (
        Index("idx_id", "id"),
        Index("idx_ticket_data", "id_ticket", "data_assegnazione"),
    )

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    id_ticket = Column(Integer, index=True)
    nome = Column(String(50))
    data_assegnazione = Column(DateTime, default=datetime.now(local_timezone), index=True)

    gruppo = relationship("UserGroup", back_populates="gruppo_fk")

class UserGroup(Base):
    __tablename__ = "user_groups"
    group_id = Column(Integer, ForeignKey("groups.id", onupdate='CASCADE', ondelete='CASCADE'), primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id", onupdate='CASCADE', ondelete='CASCADE'), primary_key=True)
    assignment_date = Column(DateTime, default=datetime.now(local_timezone))

    gruppo_fk = relationship("Group", back_populates="gruppo")
    utente_gruppo = relationship("User", back_populates="utente_gruppo_fk")


