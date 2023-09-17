from datetime import datetime

import pendulum
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

from database.database import Base

DEFAULT_TIMEZONE: str = "Europe/Rome"


class User(Base):
    __tablename__ = "users"
    __table_args__ = (
        Index("idx_codice_fiscale", "codice_fiscale"),
        Index("idx_name_surname", "nome", "cognome"),
    )

    id: Column = Column(Integer, primary_key=True, index=True, autoincrement=True)
    nome: Column = Column(String(50), index=True, nullable=False)
    cognome: Column = Column(String(50), index=True, nullable=False)
    data_nascita: Column = Column(Date, nullable=False)
    luogo_nascita: Column = Column(String(100), nullable=True)
    luogo_residenza: Column = Column(String(100), nullable=True)
    via_residenza: Column = Column(String(100), nullable=True)
    codice_fiscale: Column = Column(String(16), index=True, nullable=False)
    telefono: Column = Column(String(30), nullable=True)
    data_registrazione: Column = Column(Date, default=datetime.today, nullable=False)

    utente_gruppo_fk = relationship("UserGroup", back_populates="utente_gruppo")


class Child(Base):
    __tablename__ = "children"

    id: Column = Column(Integer, primary_key=True, index=True, autoincrement=True)
    id_genitore: Column = Column(Integer, ForeignKey("users.id", onupdate="CASCADE", ondelete="CASCADE"),
                                 nullable=False)
    id_figlio: Column = Column(Integer, ForeignKey("users.id", onupdate="CASCADE", ondelete="CASCADE"), nullable=False)

    genitore = relationship("User", foreign_keys=[id_genitore])
    figlio = relationship("User", foreign_keys=[id_figlio])


class Group(Base):
    __tablename__ = "groups"
    __table_args__ = (
        Index("idx_id", "id"),
        Index("idx_ticket_data", "id_ticket", "data_assegnazione"),
    )

    id: Column = Column(Integer, primary_key=True, index=True, autoincrement=True)
    id_ticket: Column = Column(Integer, index=True)
    nome: Column = Column(String(50))
    data_assegnazione: Column = Column(DateTime, default=pendulum.now(DEFAULT_TIMEZONE), index=True)

    gruppo = relationship("UserGroup", back_populates="gruppo_fk")


class UserGroup(Base):
    __tablename__ = "user_groups"
    group_id: Column = Column(Integer, ForeignKey("groups.id", onupdate="CASCADE", ondelete="CASCADE"),
                              primary_key=True)
    user_id: Column = Column(Integer, ForeignKey("users.id", onupdate="CASCADE", ondelete="CASCADE"), primary_key=True)
    assignment_date: Column = Column(DateTime, default=pendulum.now(tz=DEFAULT_TIMEZONE))

    gruppo_fk = relationship("Group", back_populates="gruppo")
    utente_gruppo = relationship("User", back_populates="utente_gruppo_fk")
