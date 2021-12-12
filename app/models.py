from sqlalchemy.ext.mutable import MutableList

from app import db


class Trainer(db.Model):
    """This class represents the pokemon trainer table."""

    __tablename__ = "trainer"

    id = db.Column(db.String(255), primary_key=True)
    firstName = db.Column(db.String(255))
    lastName = db.Column(db.String(255))
    dateOfBirth = db.Column(db.Date)

    def __init__(self, id, firstName, lastName, dateOfBirth):
        """Initialize with trainer details"""
        self.id = id
        self.firstName = firstName
        self.lastName = lastName
        self.dateOfBirth = dateOfBirth

    def save(self):
        # check if row exists
        # if exists, update. else, insert
        exists = (
            db.session.query(Trainer).filter(Trainer.id == self.id).first() is not None
        )

        if exists:
            trainer = db.session.query(Trainer).filter(Trainer.id == self.id).one()
            trainer.firstName = self.firstName
            trainer.lastName = self.lastName
            trainer.dateOfBirth = self.dateOfBirth
        else:
            db.session.add(self)
        db.session.commit()

    @staticmethod
    def get_all():
        return Trainer.query.order_by(Trainer.id).all()

    @staticmethod
    def get_trainer(id):
        return Trainer.query.filter(Trainer.id == id).first()

    def delete(self):
        db.session.delete(self)
        db.session.commit()

    def __repr__(self):
        return "".format(self.id)


class Pokemon(db.Model):
    """This class represents the pokemon table."""

    __tablename__ = "pokemon"

    id = db.Column(db.String(255), primary_key=True)
    nickname = db.Column(db.String(255))
    species = db.Column(db.String(255))
    level = db.Column(db.Integer)
    owner = db.Column(db.String(255), db.ForeignKey("trainer.id"))
    dateOfOwnership = db.Column(db.Date)
    history = db.Column(MutableList.as_mutable(db.ARRAY(db.String)))

    def __init__(self, id, nickname, species, level, owner, dateOfOwnership, history):
        """initialize with pokemon details."""
        self.id = id
        self.nickname = nickname
        self.species = species
        self.level = level
        self.owner = owner
        self.dateOfOwnership = dateOfOwnership
        self.history = history

    def save(self):
        # check if row exists
        # if exists, update. else, insert
        exists = (
            db.session.query(Pokemon).filter(Pokemon.id == self.id).first() is not None
        )

        if exists:
            pokemon = db.session.query(Pokemon).filter(Pokemon.id == self.id).one()
            pokemon.nickname = self.nickname
            pokemon.species = self.species
            pokemon.level = self.level
            pokemon.owner = self.owner
            pokemon.dateOfOwnership = self.dateOfOwnership
            pokemon.history = self.history
        else:
            db.session.add(self)
        db.session.commit()

    @staticmethod
    def get_all():
        return Pokemon.query.order_by(Pokemon.id).all()

    @staticmethod
    def get_trainer(id):
        return Pokemon.query.filter(Pokemon.owner == id).all()

    @staticmethod
    def get_pokemon(id):
        return Pokemon.query.filter(Pokemon.id == id).first()

    def delete(self):
        db.session.delete(self)
        db.session.commit()

    def __repr__(self):
        return "".format(self.id)
