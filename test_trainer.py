from re import M
import unittest
import os
import json
import io
import csv
from datetime import datetime

from app import create_app, db
from app.models import Trainer, Pokemon


class TrainerTestCase(unittest.TestCase):
    """This class represents the trainer test case"""

    def setUp(self):
        """Define test variables and initialize app."""
        self.app = create_app(config_name="testing")
        self.client = self.app.test_client
        self.trainer_csv = "tests/trainer.csv"

        # binds the app to the current context
        with self.app.app_context():
            # create all tables
            db.create_all()

    def test_upload_trainer_data(self):
        """Test API can upload Trainer CSV (POST request)"""
        with open(self.trainer_csv, "rb") as f:
            res = self.client().post(
                "/upload/",
                content_type="multipart/form-data",
                data={"data": f, "type": "trainer"},
            )

        data = json.loads(res.get_data(as_text=True))

        self.assertEqual(res.status_code, 201)
        self.assertTrue(data["success"])

    def test_get_list_trainers_data(self):
        """Test API can list all trainers (GET request)"""
        # preload db with trainer data
        with open(self.trainer_csv, "rb") as f:
            res = self.client().post(
                "/upload/",
                content_type="multipart/form-data",
                data={"data": f, "type": "trainer"},
            )

        self.assertEqual(res.status_code, 201)

        page, limit = 3, 5

        # FIXME: use query params instead of formatting url
        # NOTE: maybe use url slugs to pass params?
        res = self.client().get(f"/trainer/?page={page}&limit={limit}")

        data = json.loads(res.get_data(as_text=True))

        self.assertEqual(res.status_code, 200)
        self.assertIn("page", str(data))
        self.assertIn("total_page", str(data))
        self.assertIn("trainers", str(data))
        self.assertEqual(len(data["trainers"]), 5)
        self.assertEqual(data["page"], page)

    def test_get_trainer_data(self):
        """Test API can get Trainer by ID (GET request)"""
        # preload db with trainer data
        with open(self.trainer_csv, "rb") as f:
            res = self.client().post(
                "/upload/",
                content_type="multipart/form-data",
                data={"data": f, "type": "trainer"},
            )

        self.assertEqual(res.status_code, 201)
        res = self.client().get(
            "/trainer/",
            data={"trainerId": "trainer1"},
        )
        data = json.loads(res.get_data(as_text=True))
        self.assertEqual(res.status_code, 200)
        self.assertIn("id", str(data))
        self.assertIn("firstName", str(data))
        self.assertIn("lastName", str(data))
        self.assertIn("dateOfBirth", str(data))

    def test_create_trainer_data(self):
        """Test API can create Trainer data (POST request)"""
        with open(self.trainer_csv, "rb") as f:
            res = self.client().post(
                "/upload/",
                content_type="multipart/form-data",
                data={"data": f, "type": "trainer"},
            )
        valid_data = {
            "trainerId": "trainer20",
            "firstName": "test",
            "lastName": "test",
            "dateOfBirth": "19-10-2000",
        }

        # check creation using valid data
        res = self.client().post(
            f"/trainer/create/?trainerId={valid_data['trainerId']}&firstName={valid_data['firstName']}&lastName={valid_data['lastName']}&dateOfBirth={valid_data['dateOfBirth']}",
        )

        data = json.loads(res.get_data(as_text=True))

        self.assertEqual(res.status_code, 201)
        self.assertTrue(data["success"])

        invalid_data = {
            "trainerId": "trainer20",
            "firstName": "test",
            "lastName": "test",
        }

        # check creation using invalid data
        res = self.client().post(
            f"/trainer/create/?trainerId={invalid_data['trainerId']}&firstName={invalid_data['firstName']}&lastName={invalid_data['lastName']}",
        )

        data = json.loads(res.get_data(as_text=True))

        self.assertEqual(res.status_code, 400)
        self.assertFalse(data["success"])

    def test_update_trainer_data(self):
        """Test API can update Trainer data (PUT request)"""
        with open(self.trainer_csv, "rb") as f:
            res = self.client().post(
                "/upload/",
                content_type="multipart/form-data",
                data={"data": f, "type": "trainer"},
            )

        data = {
            "trainerId": "trainer1",
            "firstName": "test",
        }

        res = self.client().put(
            f"/trainer/?trainerId={data['trainerId']}&firstName={data['firstName']}"
        )

        self.assertEqual(res.status_code, 200)
        res_data = json.loads(res.get_data(as_text=True))
        self.assertTrue(res_data["success"])

        with self.app.app_context():
            trainer = (
                db.session.query(Trainer)
                .filter(Trainer.id == data["trainerId"])
                .first()
            )
        res_data = json.loads(res.get_data(as_text=True))
        self.assertEqual("test", trainer.firstName)

    def test_delete_trainer_data(self):
        """Test API can delete Trainer data (DELETE request)"""
        with open(self.trainer_csv, "rb") as f:
            res = self.client().post(
                "/upload/",
                content_type="multipart/form-data",
                data={"data": f, "type": "trainer"},
            )

        data = {
            "trainerId": "trainer1",
        }

        res = self.client().delete(
            f"/trainer/?trainerId={data['trainerId']}",
        )

        self.assertEqual(res.status_code, 200)
        res = self.client().get(f"/trainer/?trainerId={data['trainerId']}")
        # data = json.loads(res.get_data(as_text=True))
        self.assertEqual(res.status_code, 404)

    def tearDown(self):
        """teardown all initialized variables."""
        with self.app.app_context():
            # drop all tables
            db.session.remove()
            db.drop_all()


class PokemonTestCase(unittest.TestCase):
    """This class represents the pokemon test case"""

    def setUp(self):
        """Define test variables and initialize app."""
        self.app = create_app(config_name="testing")
        self.client = self.app.test_client
        self.pokemon_csv = "tests/pokemon.csv"
        self.trainer_csv = "tests/trainer.csv"

        # binds the app to the current context
        with self.app.app_context():
            # create all tables
            db.create_all()
            self._add_trainer()

    def _add_trainer(self, commit=True):
        """Setup trainer data inside test_db"""
        with open(self.trainer_csv, "r") as f:
            reader = csv.reader(f)
            _ = next(reader)
            for id, firstName, lastName, dateOfBirth in reader:
                trainer = Trainer(
                    id=id,
                    firstName=firstName,
                    lastName=lastName,
                    dateOfBirth=dateOfBirth,
                )

                trainer.save()

    def test_upload_pokemon_data(self):
        """Test API can upload Pokemon CSV (POST request)"""
        with open(self.pokemon_csv, "rb") as f:
            res = self.client().post(
                "/upload/",
                content_type="multipart/form-data",
                data={"data": f, "type": "pokemon"},
            )

        data = json.loads(res.get_data(as_text=True))

        self.assertEqual(res.status_code, 201)
        self.assertTrue(data["success"])

    def test_get_pokemon(self):
        """Test API can get Pokemon by id (GET request)"""
        with open(self.pokemon_csv, "rb") as f:
            res = self.client().post(
                "/upload/",
                content_type="multipart/form-data",
                data={"data": f, "type": "pokemon"},
            )

        res = self.client().get(
            "/pokemon/",
            data={"pokemonId": "pikachu1"},
        )

        data = json.loads(res.get_data(as_text=True))

        self.assertEqual(res.status_code, 200)
        self.assertIn("name", str(data))
        self.assertIn("species", str(data))
        self.assertIn("level", str(data))
        self.assertIn("owner", str(data))
        self.assertIn("dateOfOwnership", str(data))

    def test_get_list_pokemon_data(self):
        """Test API can list all Pokemons (GET request)"""
        # preload db with pokemon data
        with open(self.pokemon_csv, "rb") as f:
            res = self.client().post(
                "/upload/",
                content_type="multipart/form-data",
                data={"data": f, "type": "pokemon"},
            )

        self.assertEqual(res.status_code, 201)

        page, limit = 1, 5

        # FIXME: use query params instead of formatting url
        res = self.client().get(f"/pokemon/?page={page}&limit={limit}")

        data = json.loads(res.get_data(as_text=True))

        self.assertEqual(res.status_code, 200)
        self.assertIn("page", str(data))
        self.assertIn("total_page", str(data))
        self.assertIn("pokemons", str(data))
        self.assertEqual(len(data["pokemons"]), 5)
        self.assertEqual(data["page"], page)

    def test_exchange_pokemon(self):
        """Test API can exchange Pokemons (POST request)"""
        with open(self.pokemon_csv, "rb") as f:
            res = self.client().post(
                "/upload/",
                content_type="multipart/form-data",
                data={"data": f, "type": "pokemon"},
            )

        self.assertEqual(res.status_code, 201)

        page, limit = 1, 5

        # FIXME: use query params instead of formatting url
        data = {
            "trainerA": "trainer1",
            "trainerB": "trainer2",
            "pokemonsA": "pikachu4,pikachu3,pikachu2",
            "pokemonsB": "pikachu5,pikachu6",
        }

        res = self.client().post(
            f"/exchange/?trainerA={data['trainerA']}&trainerB={data['trainerB']}&pokemonsA={data['pokemonsA']}&pokemonsB={data['pokemonsB']}",
        )

        res_data = json.loads(res.get_data(as_text=True))

        # query pokemon table to check if exchange works
        with self.app.app_context():
            pokemonsA = data["pokemonsA"].split(",")
            pokemonsB = data["pokemonsB"].split(",")

            for a in pokemonsA:
                pokemon_obj_a = (
                    db.session.query(Pokemon).filter(Pokemon.id == a).first()
                )
                self.assertEqual(pokemon_obj_a.owner, data["trainerB"])

            for b in pokemonsB:
                pokemon_obj_b = (
                    db.session.query(Pokemon).filter(Pokemon.id == b).first()
                )
                self.assertEqual(pokemon_obj_b.owner, data["trainerA"])

        self.assertEqual(res.status_code, 200)
        self.assertTrue(res_data["success"])

    def tearDown(self):
        """teardown all initialized variables."""
        with self.app.app_context():
            # drop all tables
            db.session.remove()
            db.drop_all()


# Make the tests conveniently executable
if __name__ == "__main__":
    unittest.main()
