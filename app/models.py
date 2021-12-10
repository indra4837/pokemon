from datetime import date
from sqlalchemy.dialects.postgresql import UUID

from app import db
import uuid


class Trainer(db.Model):
    """This class represents the pokemon trainer table."""

    __tablename__ = "trainer"

    id = db.Column(db.String(255), primary_key=True)
    firstName = db.Column(db.String(255))
    lastName = db.Column(db.String(255))
    dateOfBirth = db.Column(db.DateTime, default=db.func.current_timestamp())

    def __init__(self, id, firstName, lastName, dateOfBirth):
        """Initialize with trainer details"""
        self.id = id
        self.firstName = firstName
        self.lastName = lastName
        self.dateOfBirth = dateOfBirth

    def save(self):
        db.session.add(self)
        db.session.commit()

    @staticmethod
    def get_all():
        return Trainer.query.all()

    def delete(self):
        db.session.delete(self)
        db.session.commit()

    def __repr__(self):
        return "".format(self.name)


class Pokemon(db.Model):
    """This class represents the pokemon table."""

    __tablename__ = "pokemon"

    id = db.Column(db.String(255), primary_key=True)
    nickname = db.Column(db.String(255))
    species = db.Column(db.String(255))
    level = db.Column(db.Integer)
    owner = db.Column(db.String(255), db.ForeignKey("trainer.id"))
    dateOfOwnership = db.Column(db.DateTime, default=db.func.current_timestamp())

    def __init__(self, id, nickname, species, level, owner, dateOfOwnership):
        """initialize with pokemon details."""
        self.id = id
        self.nickname = nickname
        self.species = species
        self.level = level
        self.owner = owner
        self.dateOfOwnership = dateOfOwnership

    def save(self):
        db.session.add(self)
        db.session.commit()

    @staticmethod
    def get_all():
        return Pokemon.query.all()

    def delete(self):
        db.session.delete(self)
        db.session.commit()

    def __repr__(self):
        return "".format(self.name)
