import os

from flask_migrate import Migrate
from app import db, create_app
from app import models


app = create_app(config_name=os.getenv("APP_SETTINGS"))
migrate = Migrate(app, db)
migrate.init_app(app, db)
