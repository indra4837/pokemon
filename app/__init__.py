import csv
from datetime import date
import io

from flask_api import FlaskAPI
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask import request, jsonify, abort

# local import
from instance.config import app_config

# initialize sql-alchemy
db = SQLAlchemy()


def create_app(config_name):
    from app.models import Trainer, Pokemon

    app = FlaskAPI(__name__, instance_relative_config=True)
    app.config.from_object(app_config[config_name])
    app.config.from_pyfile("config.py")
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    db.init_app(app)
    migrate = Migrate(app, db)

    @app.route("/upload/", methods=["POST"])
    def seeding():
        if request.method == "POST":
            dataType = request.data.get("type", "")
            f = request.files["data"]
            stream = io.StringIO(f.stream.read().decode("utf-8"), newline=None)
            # print(f"Type: {type}, Filename: {stream.read()}")

            if dataType == "trainer":
                overallData = []
                success = True

                reader = csv.reader(stream)
                _ = next(reader)

                for id, firstName, lastName, dateOfBirth in reader:
                    # print(id, firstName, lastName, dateOfBirth)

                    if None in (id, firstName, lastName, dateOfBirth):
                        # TODO: handle incomplete data (Current: Method 1)
                        # 1. Skip this row
                        # 2. Dont accept entire csv file
                        continue

                    trainer = Trainer(
                        id=id,
                        firstName=firstName,
                        lastName=lastName,
                        dateOfBirth=dateOfBirth,
                    )

                    # TODO: implement redis cache to preload csv before saving whole item
                    overallData.append(trainer)

                    # response = jsonify(
                    #     {
                    #         "id": id,
                    #         "firstName": firstName,
                    #         "lastName": lastName,
                    #         "dob": dateOfBirth,
                    #     }
                    # )
                    success = True

                # TODO: Pop from redis cache and save update table
                # for i in overallData:
                #     i.save()
                #     success = True

                response = jsonify({"success": success})
                response.status_code = 201 if success else 400

                return response
            elif dataType == "pokemon":
                overallData = []
                success = True

                reader = csv.reader(stream)
                _ = next(reader)

                for id, nickname, species, level, owner, dateOfOwnership in reader:
                    # print(id, nickname, species, level, owner, dateOfOwnership)

                    if None in (id, nickname, species, level, owner, dateOfOwnership):
                        # TODO: handle incomplete data (Current: Method 1)
                        # 1. Skip this row
                        # 2. Dont accept entire csv file
                        continue

                    pokemon = Pokemon(
                        id=id,
                        nickname=nickname,
                        species=species,
                        level=level,
                        owner=owner,
                        dateOfOwnership=dateOfOwnership,
                    )

                    # TODO: implement redis cache to preload csv before saving whole item
                    overallData.append(pokemon)

                    success = True

                # TODO: Pop from redis cache and save update table
                # for i in overallData:
                #     i.save()
                #     success = True

                response = jsonify({"success": success})
                response.status_code = 201 if success else 400

                return response

        else:
            response = jsonify({"success": False})
            response.status_code = 400

            return response

    return app


from app import models
