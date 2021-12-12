from re import M
import unittest
import os
import json
import io
import csv
from datetime import datetime

from app import create_app, db
from app.models import Trainer


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

    def tearDown(self):
        """teardown all initialized variables."""
        with self.app.app_context():
            # drop all tables
            db.session.remove()
            db.drop_all()

    # def test_trainer_creation(self):
    #     """Test API can create a trainer (POST request)"""
    #     res = self.client().post("/trainers/", data=self.trainer)
    #     self.assertEqual(res.status_code, 201)
    #     self.assertIn("Go to Borabora", str(res.data))

    # def test_api_can_get_all_trainers(self):
    #     """Test API can get a trainer (GET request)."""
    #     res = self.client().post("/trainers/", data=self.trainer)
    #     self.assertEqual(res.status_code, 201)
    #     res = self.client().get("/trainers/")
    #     self.assertEqual(res.status_code, 200)
    #     self.assertIn("Go to Borabora", str(res.data))

    # def test_api_can_get_trainer_by_id(self):
    #     """Test API can get a single trainer by using it's id."""
    #     rv = self.client().post("/trainers/", data=self.trainer)
    #     self.assertEqual(rv.status_code, 201)
    #     result_in_json = json.loads(rv.data.decode("utf-8").replace("'", '"'))
    #     result = self.client().get("/trainers/{}".format(result_in_json["id"]))
    #     self.assertEqual(result.status_code, 200)
    #     self.assertIn("Go to Borabora", str(result.data))

    # def test_trainer_can_be_edited(self):
    #     """Test API can edit an existing trainer. (PUT request)"""
    #     rv = self.client().post("/trainers/", data={"name": "Eat, pray and love"})
    #     self.assertEqual(rv.status_code, 201)
    #     rv = self.client().put(
    #         "/trainers/1", data={"name": "Dont just eat, but also pray and love :-)"}
    #     )
    #     self.assertEqual(rv.status_code, 200)
    #     results = self.client().get("/trainers/1")
    #     self.assertIn("Dont just eat", str(results.data))

    # def test_trainer_deletion(self):
    #     """Test API can delete an existing trainer. (DELETE request)."""
    #     rv = self.client().post("/trainers/", data={"name": "Eat, pray and love"})
    #     self.assertEqual(rv.status_code, 201)
    #     res = self.client().delete("/trainers/1")
    #     self.assertEqual(res.status_code, 200)
    #     # Test to see if it exists, should return a 404
    #     result = self.client().get("/trainers/1")
    #     self.assertEqual(result.status_code, 404)


# Make the tests conveniently executable
if __name__ == "__main__":
    unittest.main()
