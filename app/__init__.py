import csv
import io
import datetime
import json

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
                    except:
                        message = "Unable to save data"

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
                        history=[v["owner"]],
                    )

                    try:
                        pokemon.save()
                    except:
                        message = "Unable to save data"

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

    @app.route("/trainer/", methods=["GET", "PUT", "DELETE"])
    def get_trainers():
        trainer_id = request.args.get("trainerId", default=None, type=str)
        if request.method == "GET":
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
            trainers = Trainer.get_all()
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

        elif request.method == "PUT":
            trainer_id = request.args.get("trainerId", default=None, type=str)
            firstName = request.args.get("firstName", default=None, type=str)
            lastName = request.args.get("lastName", default=None, type=str)
            dateOfBirth = request.args.get("dateOfBirth", default=None, type=str)

            if trainer_id is None:
                response = jsonify({"success": False, "error": "No trainers found"})
                response.status_code = 404

                return response

            trainer = Trainer.get_trainer(trainer_id)

            if firstName is not None:
                trainer.firstName = firstName
            if lastName is not None:
                trainer.lastName = lastName
            if dateOfBirth is not None:
                trainer.dateOfBirth = dateOfBirth

            try:
                "trying to save"
                trainer.save()
            except:
                message = f"Unable to update {trainer_id}"
                response = jsonify({"success": False, "error": message})
                response.status_code = 400

                return response

            response = jsonify({"success": True})
            response.status_code = 200

            return response
        elif request.method == "DELETE":
            # trainer = Trainer.query.filter(Trainer.id == id).first()
            trainer = Trainer.get_trainer(trainer_id)
            if not trainer:
                abort(404)

            try:
                trainer.delete()
            except:
                response = jsonify(
                    {"success": False, "error": "Unable to delete trainer"}
                )
                response.status_code = 400

                return response

            response = jsonify({"success": True})
            response.status_code = 200

            return response

    @app.route("/trainer/create/", methods=["POST"])
    def create_trainer():
        if request.method == "POST":
            trainer_id = request.args.get("trainerId", default=None, type=str)
            firstName = request.args.get("firstName", default=None, type=str)
            lastName = request.args.get("lastName", default=None, type=str)
            dateOfBirth = request.args.get("dateOfBirth", default=None, type=str)

            # check if payload is valid
            if None in [trainer_id, firstName, lastName, dateOfBirth]:
                response = jsonify({"success": False, "error": "Invalid payload"})
                response.status_code = 400

                return response

            trainer = Trainer(
                id=trainer_id,
                firstName=firstName,
                lastName=lastName,
                dateOfBirth=dateOfBirth,
            )

            try:
                trainer.save()
            except:
                response = jsonify(
                    {"success": False, "error": "Unable to create trainer"}
                )
                response.status_code = 400

                return response

            response = jsonify({"success": True})
            response.status_code = 201

            return response

    @app.route("/pokemon/", methods=["GET"])
    def get_pokemon():
        if request.method == "GET":
            pokemon_id = request.args.get("pokemonId", default=None, type=str)
            if pokemon_id is not None:
                obj = Pokemon.get_pokemon(pokemon_id)

                if len(obj) == 0:
                    response = jsonify("No Pokemon found")
                    response.status_code = 404

                    return response

                poke_obj = {
                    "id": obj.id,
                    "nickname": obj.nickname,
                    "species": obj.species,
                    "level": obj.level,
                    "owner": obj.owner,
                    "dateOfOwnership": obj.dateOfOwnership,
                }

                response = jsonify(poke_obj)
                response.status_code = 200

                return response

            page = request.args.get("page", default=1, type=int)
            limit = request.args.get("limit", default=5, type=int)
            pokemons = Pokemon.get_all()
            total_pages = len(pokemons) // limit
            results = []
            start = 0 + page * limit
            end = min(start + limit, len(pokemons))

            for pokemon in pokemons:
                obj = {
                    "id": pokemon.id,
                    "nickname": pokemon.nickname,
                    "species": pokemon.species,
                    "level": pokemon.level,
                    "owner": pokemon.owner,
                    "dateOfOwnership": pokemon.dateOfOwnership,
                }
                results.append(obj)

            results = results[start:end]

            response = jsonify(
                {"pokemons": results, "page": page, "total_page": total_pages}
            )

            response.status_code = 200

            return response

    @app.route("/exchange/", methods=["POST"])
    def exchange():
        if request.method == "POST":
            trainerA = request.args.get("trainerA", default=None, type=str)
            trainerB = request.args.get("trainerB", default=None, type=str)
            pokemonsA = request.args.get("pokemonsA", default=None, type=str).split(",")
            pokemonsB = request.args.get("pokemonsB", default=None, type=str).split(",")

        if None in [trainerA, trainerB, pokemonsA, pokemonsB]:
            response = jsonify(
                {
                    "success": False,
                    "error": "Invalid input data",
                }
            )
            response.status_code = 400

            return response

        trainer_obj_a = Trainer.get_trainer(trainerA)
        trainer_obj_b = Trainer.get_trainer(trainerB)

        for i in pokemonsA:
            pokemon_obj_a = Pokemon.get_pokemon(i)
            pokemon_obj_a.owner = trainer_obj_b.id
            pokemon_obj_a.history.append(trainer_obj_b.id)
            pokemon_obj_a.save()

        for i in pokemonsB:
            pokemon_obj_b = Pokemon.get_pokemon(i)
            pokemon_obj_b.owner = trainer_obj_a.id
            pokemon_obj_b.history.append(trainer_obj_a.id)
            pokemon_obj_b.save()

        response = jsonify({"success": True})
        response.status_code = 200

        return response

    return app


from app import models
