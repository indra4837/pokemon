import csv
import io
import datetime
import json

import redis

from flask_api import FlaskAPI
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask import request, jsonify

from sqlalchemy.sql import text
from sqlalchemy import column

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
                r = redis.StrictRedis(db=0, encoding="utf-8", decode_responses=True)

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
                r = redis.StrictRedis(db=1, encoding="utf-8", decode_responses=True)

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

    @app.route("/trainer/", methods=["GET"])
    def get_trainers():
        if request.method == "GET":
            trainer_id = request.args.get("trainerId", default=None, type=str)
            if trainer_id is not None:
                pokemon_objs, trainer_obj = Pokemon.get_trainer(
                    trainer_id
                ), Trainer.get_trainer(trainer_id)

                pokemons = []

                if len(pokemon_objs) == 0:
                    response = jsonify("No trainer found")
                    response.status_code = 404

                    return response

                for obj in pokemon_objs:
                    poke_obj = {
                        "id": obj.id,
                        "nickname": obj.nickname,
                        "species": obj.species,
                        "level": obj.level,
                        "owner": obj.owner,
                        "dateOfOwnership": obj.dateOfOwnership,
                    }
                    # trainer_obj = {
                    #     "id": i.owner,
                    #     "firstName": i.firstName,
                    # }
                    pokemons.append(poke_obj)

                trainer = {
                    "firstName": trainer_obj.firstName,
                    "lastName": trainer_obj.lastName,
                }

                response = jsonify(
                    {
                        "firstName": trainer_obj.firstName,
                        "lastName": trainer_obj.lastName,
                        "pokemons": pokemons,
                    }
                )
                response.status_code = 200

                return response

            page = request.args.get("page", default=1, type=int)
            limit = request.args.get("limit", default=5, type=int)
            # page = request.data.get("page", default=1, type=int)
            # limit = request.data.get("limit", default=5, type=int)
            # print(page, limit)
            trainers = Trainer.get_all()
            # print(trainers)
            total_pages = len(trainers) // limit
            results = []
            start = 0 + page * limit
            end = min(start + limit, len(trainers))

            for trainer in trainers:
                obj = {
                    "id": trainer.id,
                    "firstName": trainer.firstName,
                    "lastName": trainer.lastName,
                    "dateOfBirth": trainer.dateOfBirth,
                }
                results.append(obj)

            results = results[start:end]

            response = jsonify(
                {"trainers": results, "page": page, "total_page": total_pages}
            )

            response.status_code = 200

            return response

    return app


from app import models
