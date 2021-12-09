from app import db


class Trainer(db.Model):
    """This class represents the pokemon trainer table."""

    __tablename__ = "trainer"

    id = db.Column(db.String(255), primary_key=True)
    firstName = db.Column(db.String(255))
    lastName = db.Column(db.String(255))
    dateOfBirth = db.Column(db.DateTime, default=db.func.current_timestamp())

    def __init__(self, name):
        """initialize with name."""
        self.name = name

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

    def __init__(self, name):
        """initialize with name."""
        self.name = name

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
