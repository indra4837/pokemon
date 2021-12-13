import os

from flask_migrate import Migrate
from app import db, create_app
from app import models
from flask_apidoc.commands import GenerateApiDoc


app = create_app(config_name=os.getenv("APP_SETTINGS"))
app.cli.add_command(GenerateApiDoc(), "apidoc")
migrate = Migrate(app, db)
migrate.init_app(app, db)
