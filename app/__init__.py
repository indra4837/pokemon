import csv
import io
from datetime import datetime
import json

import redis

from flask_apidoc import ApiDoc
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
    doc = ApiDoc(app=app, folder_path="/home/indra/pokemon/docs")
    db.init_app(app)
    migrate = Migrate(app, db)

    def validate_date(date_text):
        """Helper function to validate date format"""
        try:
            datetime.strptime(date_text, "%d-%m-%Y")
        except:
            return False

        return True

    def validate_input_format(inputList, dataType):
        """Helper function to validate input format"""

        return all([isinstance(i, dataType) for i in inputList])

    @app.route("/upload/", methods=["POST"])
    def seeding():
        """
        @api {post} /upload Uploads file
        @apiVersion 1.0.0
        @apiName upload
        @apiGroup Trainer

        @apiParam {String}      type        Type of data uploaded
        @apiParam {Object}      data        UTF8 encoded CSV file

        @apiSuccess (201 Created) {String}    success     True of False
        @apiSuccess (201 Created) {String}    error       Error message

        @apiSuccessExample {json} Success-Response:
            HTTP/1.1 201 Created
            {
                "success": True
            }
        """
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
        """
        @api {get} /trainer Gets trainer
        @apiVersion 1.0.0
        @apiName GetTrainer
        @apiGroup Trainer

        @apiParam {String}      trainerId       Id of trainer

        @apiSuccess (200 OK) {String}    firstName       True of False
        @apiSuccess (200 OK) {String}    error           Error message

        @apiSuccessExample Success-Response:
            HTTP/1.1 {json} 200 OK
            {
                "firstName": "Ash",
                "lastName": "Ketchum",
                "pokemons": [{"id": "pika1",
                            "nickname": "pikapika",
                            "species": "pikachu",
                            "level": 10,
                            "owner": "trainer1",
                            "dateOfOwnership": "25-12-2021"}]
            }
        """
        """
        @api {get} /trainer Gets list of trainers
        @apiVersion 1.0.0
        @apiName GetTrainers
        @apiGroup Trainer

        @apiParam {String}      [page=1]          Page number
        @apiParam {String}      [limit=5]         Results limit per page

        @apiSuccess (200 OK) {Object}    trainers        Trainer object
        @apiSuccess (200 OK) {String}    page            Page Number
        @apiSuccess (200 OK) {String}    total_page      Total Page Number

        @apiSuccessExample Success-Response:
            HTTP/1.1 {json} 200 OK
            {
                "page": "1",
                "total_page": "4",
                "trainers": [{"id": "pika1",
                            "firstName": "pikapika",
                            "lastName": "pikachu",
                            "dateOfBirth": "25-12-2021"}]
            }
        """
        """
        @api {put} /trainer Updates trainer data
        @apiVersion 1.0.0
        @apiName UpdateTrainer
        @apiGroup Trainer

        @apiParam {String}      trainerId     ID of trainer

        @apiSuccess (200 OK) {Boolean}   success         True of False

        @apiSuccessExample Success-Response:
            HTTP/1.1 {json} 200 OK
            {
                "success": True,
            }
        """
        """
        @api {delete} /trainer Delete trainer data
        @apiVersion 1.0.0
        @apiName DeleteTrainer
        @apiGroup Trainer

        @apiParam {String}      trainerId     ID of trainer

        @apiSuccess (200 OK) {Boolean}   success         True of False

        @apiSuccessExample Success-Response:
            HTTP/1.1 {json} 200 OK
            {
                "success": True,
            }
        """
        trainer_id = request.args.get("trainerId", default=None, type=str)
        if request.method == "GET":
            if trainer_id is not None:
                pokemon_objs, trainer_obj = Pokemon.get_trainer(
                    trainer_id
                ), Trainer.get_trainer(trainer_id)

                pokemons = []

                if trainer_obj is None:
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
                        "dateOfOwnership": obj.dateOfOwnership.strftime("%d-%m-%Y"),
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
                    "dateOfBirth": trainer.dateOfBirth.strftime("%d-%m-%Y"),
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
                response = jsonify(
                    {"success": False, "error": "Trainer not found in database"}
                )
                response.status_code = 400

                return response

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
        """
        @api {post} /trainer/create Create new trainer
        @apiVersion 1.0.0
        @apiName CreateTrainer
        @apiGroup Trainer

        @apiParam {String}      trainerId     ID of trainer
        @apiParam {String}      firstName     First name of trainer
        @apiParam {String}      lastName      Last Name of trainer
        @apiParam {String}      dateOfBirth   Date of birth of trainer

        @apiSuccess (201 Created) {Boolean}   success         True of False

        @apiSuccessExample Success-Response:
            HTTP/1.1 {json} 201 OK
            {
                "success": True,
            }
        """
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

    @app.route("/pokemon/create/", methods=["POST"])
    def create_pokemon():
        """
        @api {post} /pokemon/create Create new Pokemon
        @apiVersion 1.0.0
        @apiName CreatePokemon
        @apiGroup Pokemon

        @apiParam {String}      pokemonId           ID of pokemon
        @apiParam {String}      nickname            Nickname of pokemon
        @apiParam {String}      species             Species of pokemon
        @apiParam {String}      level               Level of pokemon
        @apiParam {String}      owner               Owner of pokemon
        @apiParam {String}      dateOfOwnership     Date of ownership of pokemon

        @apiSuccess (201 Created) {Boolean}   success         True of False

        @apiSuccessExample Success-Response:
            HTTP/1.1 {json} 201 OK
            {
                "success": True,
            }
        """
        if request.method == "POST":
            pokemon_id = request.args.get("pokemonId", default=None, type=str)
            nickname = request.args.get("nickname", default=None, type=str)
            species = request.args.get("species", default=None, type=str)
            level = request.args.get("level", default=None, type=str)
            owner = request.args.get("owner", default=None, type=str)
            dateOfOwnership = request.args.get(
                "dateOfOwnership", default=None, type=str
            )

            # check if payload is valid
            if None in [pokemon_id, nickname, species, level, owner, dateOfOwnership]:
                response = jsonify({"success": False, "error": "Invalid payload"})
                response.status_code = 400

                return response

            pokemon = Pokemon(
                id=pokemon_id,
                nickname=nickname,
                species=species,
                level=level,
                owner=owner,
                dateOfOwnership=dateOfOwnership,
                history=[owner],
            )

            try:
                pokemon.save()
            except:
                response = jsonify(
                    {"success": False, "error": "Unable to create pokemon"}
                )
                response.status_code = 400

                return response

            response = jsonify({"success": True})
            response.status_code = 201

            return response

    @app.route("/pokemon/", methods=["GET", "PUT", "DELETE"])
    def get_pokemon():
        """
        @api {get} /pokemon Gets list of pokemon
        @apiVersion 1.0.0
        @apiName GetPokemons
        @apiGroup Pokemon

        @apiParam {String}               [page=1]          Page number
        @apiParam {String}               [limit=5]         Results limit per page


        @apiSuccess (200 OK) {String}    page            Page Number
        @apiSuccess (200 OK) {String}    total_page      Total Page Number
        @apiSuccess (200 OK) {Object}    pokemons        Pokemon object

        @apiSuccessExample Success-Response:
            HTTP/1.1 {json} 200 OK
            {
                "page": "1",
                "total_page": "4",
                "pokemons": [
                    {"id": "pika1",
                    "nickname": "pikapika",
                    "species": "pikachu",
                    "level": 10,
                    "owner": "trainer1",
                    "dateOfOwnership": "25-12-2021"}
                ]
            }
        """
        """
        @api {get} /pokemon Get a pokemon
        @apiVersion 1.0.0
        @apiName GetPokemon
        @apiGroup Pokemon

        @apiParam {String}               pokemonId           Id of Pokemon

        @apiSuccess (200 OK) {String}    id                  Id of Pokemon
        @apiSuccess (200 OK) {String}    nickname            Nickname of Pokemon
        @apiSuccess (200 OK) {String}    species             species of Pokemon
        @apiSuccess (200 OK) {String}    level               level of Pokemon
        @apiSuccess (200 OK) {String}    owner               owner of Pokemon
        @apiSuccess (200 OK) {String}    dateOfOwnership     dateOfOwnership of Pokemon

        @apiSuccessExample Success-Response:
            HTTP/1.1 {json} 200 OK
            {
                "page": "1",
                "total_page": "4",
                "pokemons": [
                    {"id": "pika1",
                    "nickname": "pikapika",
                    "species": "pikachu",
                    "level": "1",
                    "owner": "pikachu",
                    "dateOfOwnership": "25-12-2021"}
                ]
            }
        """
        """
        @api {put} /pokemon Updates pokemon data
        @apiVersion 1.0.0
        @apiName UpdatePokemon
        @apiGroup Pokemon

        @apiParam {String}               pokemonId       ID of pokemon

        @apiSuccess (200 OK) {Boolean}   success         True of False

        @apiSuccessExample Success-Response:
            HTTP/1.1 {json} 200 OK
            {
                "success": True,
            }
        """
        """
        @api {delete} /pokemon Delete pokemon data
        @apiVersion 1.0.0
        @apiName DeletePokemon
        @apiGroup Pokemon

        @apiParam {String}               pokemonId       ID of pokemon

        @apiSuccess (200 OK) {Boolean}   success         True of False

        @apiSuccessExample Success-Response:
            HTTP/1.1 {json} 200 OK
            {
                "success": True,
            }
        """
        pokemon_id = request.args.get("pokemonId", default=None, type=str)
        if request.method == "GET":
            if pokemon_id is not None:
                pokemon = Pokemon.get_pokemon(pokemon_id)
                if not pokemon:
                    response = jsonify("No Pokemon found")
                    response.status_code = 404

                    return response

                # date_object = datetime.strptime(date_string, "%d %B, %Y")

                poke_obj = {
                    "id": pokemon.id,
                    "nickname": pokemon.nickname,
                    "species": pokemon.species,
                    "level": pokemon.level,
                    "owner": pokemon.owner,
                    "dateOfOwnership": pokemon.dateOfOwnership.strftime("%d-%m-%Y"),
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
                    "dateOfOwnership": pokemon.dateOfOwnership.strftime("%d-%m-%Y"),
                }
                results.append(obj)

            results = results[start:end]

            response = jsonify(
                {"pokemons": results, "page": page, "total_page": total_pages}
            )

            response.status_code = 200

            return response

        elif request.method == "PUT":
            nickname = request.args.get("nickname", default=None, type=str)
            species = request.args.get("species", default=None, type=str)
            level = request.args.get("level", default=None, type=str)
            owner = request.args.get("owner", default=None, type=str)
            dateOfOwnership = request.args.get(
                "dateOfOwnership", default=None, type=str
            )

            if pokemon_id is None:
                response = jsonify(
                    {"success": False, "error": "Invalid payload (No id found)"}
                )
                response.status_code = 404

                return response

            pokemon = Pokemon.get_pokemon(pokemon_id)

            if nickname is not None:
                pokemon.nickname = nickname
            if species is not None:
                pokemon.species = species
            if level is not None:
                pokemon.level = level
            if owner is not None:
                pokemon.owner = owner
            if dateOfOwnership is not None:
                pokemon.dateOfOwnership = dateOfOwnership

            try:
                pokemon.save()
            except:
                message = f"Unable to update {pokemon_id}"
                response = jsonify({"success": False, "error": message})
                response.status_code = 400

                return response

            response = jsonify({"success": True})
            response.status_code = 200

            return response

        elif request.method == "DELETE":
            # trainer = Trainer.query.filter(Trainer.id == id).first()
            pokemon = Pokemon.get_pokemon(pokemon_id)
            if not pokemon:
                response = jsonify(
                    {"success": False, "error": "Pokemon not found in database"}
                )
                response.status_code = 400

                return response

            try:
                pokemon.delete()
            except:
                response = jsonify(
                    {"success": False, "error": "Unable to delete pokemon"}
                )
                response.status_code = 400

                return response

            response = jsonify({"success": True})
            response.status_code = 200

            return response

    @app.route("/exchange/", methods=["POST"])
    def exchange():
        """
        @api {post} /exchange Exchange pokemons between 2 trainers
        @apiSampleRequest http://pokemons.com/api/exchange/?trainerA=trainer1&trainerB=trainer2&pokemonsA=pika1,pika2,pika3&pokemonsB=pikapika1,pikapika2
        @apiVersion 1.0.0
        @apiName ExchangePokemons
        @apiGroup Pokemon

        @apiParam {String}      trainerA     ID of trainer A
        @apiParam {String}      trainerB     ID of trainer B
        @apiParam {String}      pokemonsA    List of pokemons from trainer A
        @apiParam {String}      pokemonsB    List of pokemons from trainer B

        @apiSuccess (200 OK) {Boolean}   success         True of False

        @apiSuccessExample Success-Response:
            HTTP/1.1 {json} 200 OK
            {
                "success": True,
            }
        """
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
