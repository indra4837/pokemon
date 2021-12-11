import csv
import io
import datetime

import redis

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

    def validate_date(date_text):
        """Helper function to validate date format"""
        try:
            datetime.datetime.strptime(date_text, "%d-%m-%Y")
        except:
            return False

        return True

    def validate_input_format(inputList, dataType):
        """Helper function to validate input format"""

        return all([isinstance(i, dataType) for i in inputList])

    @app.route("/upload/", methods=["POST"])
    def seeding():
        if request.method == "POST":
            dataType = request.data.get("type", "")
            f = request.files["data"]
            stream = io.StringIO(f.stream.read().decode("utf-8"), newline=None)
            # print(f"Type: {type}, Filename: {stream.read()}")

            if dataType == "trainer":
                message = "Input data not valid"  # base error message
                success = True
                r = redis.StrictRedis(db=0, charset="utf-8", decode_responses=True)

                reader = csv.reader(stream)
                _ = next(reader)

                for id, firstName, lastName, dateOfBirth in reader:
                    # print(id, firstName, lastName, dateOfBirth)

                    if None in (id, firstName, lastName, dateOfBirth):
                        # NOTE: handle incomplete data (Current: Method 2)
                        # 1. Skip this row
                        # 2. Dont accept entire csv file
                        success = False
                        message = "Missing values in input data"
                        break

                    if not validate_input_format([id, firstName, lastName], str):
                        success = False
                        message = "Input data format not correct"
                        break

                    if not validate_date(dateOfBirth):
                        success = False
                        message = "Input date format incorrect, should be DD-MM-YYYY"
                        break

                    if not success:
                        response = jsonify(
                            {
                                "success": success,
                                "error": message,
                            }
                        )
                        response.status_code = 400

                        return response

                    # TODO: implement redis cache to preload csv before saving whole item
                    r.hset(
                        id,
                        mapping={
                            "firstName": firstName,
                            "lastName": lastName,
                            "dateOfBirth": dateOfBirth,
                        },
                    )

                # retrieve all keys from redis cache and update database
                keys = r.keys()

                for key in keys:
                    v = r.hgetall(key)
                    trainer = Trainer(
                        id=key,
                        firstName=v["firstName"],
                        lastName=v["lastName"],
                        dateOfBirth=v["dateOfBirth"],
                    )

                    try:
                        trainer.save()
                    except Exception as e:
                        message = e.orig.args[0]
                        print(message)
                        success = False

                        response = jsonify(
                            {
                                "success": success,
                                "error": message,
                            }
                        )
                        response.status_code = 400

                        return response

                response = jsonify({"success": success})
                response.status_code = 201

                return response

            elif dataType == "pokemon":
                message = "Input data not valid"  # base error message
                success = True
                r = redis.StrictRedis(db=1, charset="utf-8", decode_responses=True)

                reader = csv.reader(stream)
                _ = next(reader)

                for id, nickname, species, level, owner, dateOfOwnership in reader:
                    # print(id, nickname, species, level, owner, dateOfOwnership)

                    if None in (id, nickname, species, level, owner, dateOfOwnership):
                        # NOTE: handle incomplete data (Current: Method 2)
                        # 1. Skip this row
                        # 2. Dont accept entire csv file
                        success = False
                        message = "Missing values in input data"
                        break

                    if not validate_input_format([id, nickname, species, owner], str):
                        success = False
                        message = "Input data format not correct"
                        break

                    if not validate_date(dateOfOwnership):
                        success = False
                        message = "Input date format incorrect, should be DD-MM-YYYY"
                        break

                    if not success:
                        response = jsonify(
                            {
                                "success": success,
                                "error": message,
                            }
                        )
                        response.status_code = 400

                        return response

                    r.hset(
                        id,
                        mapping={
                            "nickname": nickname,
                            "species": species,
                            "level": level,
                            "owner": owner,
                            "dateOfOwnership": dateOfOwnership,
                        },
                    )

                # retrieve all keys from redis cache and update database
                keys = r.keys()

                for key in keys:
                    v = r.hgetall(key)
                    pokemon = Pokemon(
                        id=key,
                        nickname=v["nickname"],
                        species=v["species"],
                        level=v["level"],
                        owner=v["owner"],
                        dateOfOwnership=v["dateOfOwnership"],
                    )

                    # try saving as new entry
                    try:
                        pokemon.save()
                    except Exception as e:
                        message = e.orig.args[0]
                        print(message)
                    # try updating table if key exists
                    try:
                        pokemon.update()
                    except:
                        success = False

                        response = jsonify(
                            {
                                "success": success,
                                "error": message,
                            }
                        )
                        response.status_code = 400

                        return response

                response = jsonify({"success": success})
                response.status_code = 201

                return response

        else:
            response = jsonify({"success": False, "error": "No valid payload"})
            response.status_code = 400

            return response

    return app


from app import models
