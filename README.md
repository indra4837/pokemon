# Pokemon

<!-- <div id="top"></div>
<h1 align="center">Pokemon</h3>
 -->
<!--   <p align="center">
    API Endpoints for Trainer and Pokemon
    <br />
    <a href="./docs/index.html"><strong>Explore the docs »</strong></a>
</div>
 -->
<!-- ABOUT THE PROJECT -->

## About The Project

API Endpoints for Trainer and Pokemon to perform basic CRUD operations and exchange pokemons

## API Endpoints documentation
```
# open docs/index.html with your favourite browser
$ firefox docs/index/html
```

## Tech Used

- FlaskAPI as RESTful API endpoints
- Postgres as relational database
- SQLAlchemy as ORM
- Redis as Cache

Since trainer and pokemon are related via owner variable, we use relational database to map this relation. Redis caching mechanism is used to cache rows of data that are read from the CSV after validation. This allows us to perform the upload as a transaction after validating all the rows in the CSV.

### Architecture

Current architecture with single server and single master db.

NOTE: Cache is only used to implement upload as a transaction. Future plans to use cache to improve query speed

![Arch](images/systemArch.png)

## DB Schema Design

![Screenshot](images/dbSchema.png)

<!-- GETTING STARTED -->

## Getting Started

1. Clone the repo

```
$ git clone https://github.com/indra4837/pokemon.git

```

2. Create python virtualenv

```
# install virtualenv
$ pip install virtualenv

$ python3 -m venv venv
$ source venv/bin/activate
```

2. Install dependencies for this project

```
$ pip install -r requirements.txt
```

3. Place the following variables in `.env` file

```
source venv/bin/activate
export FLASK_APP="run.py"
export SECRET="any-long-string"
export APP_SETTINGS="development"
export DATABASE_URL="postgresql:///poke_db"
```

4. Source environment variable

```
$ source .env
```

5. Create test db and production db

```
# testing
$ createdb test_db

# production
$ createdb poke_db
```

6. Migrate db model schema into database

```
$ flask db init
$ flask db migrate
$ flask db upgrade
```

7. Start redis-server and run flask app

```
# In another terminal
$ redis-server

$ flask run
```

<!-- USAGE EXAMPLES -->

## Usage

After running the API endpoints, you can test them via the browser by visiting the routes or using [Postman](http://postman.com).

## Screenshot of documentation

![Screenshot](images/documentation.png)

<!-- ROADMAP -->

## Roadmap

1. Containerize solution into Docker
2. Refactor codebase into Divisional Structure
3. Implement Caching to improve query speed for scalability
    * Cache results of queries for faster future read speeds
    * Implement caching eviction policies to prevent bloated cache
4. Horizontal scaling with more servers, load balances and master-slave DB

## Future Architecture Revamp

<!-- ### Back of envolope calculation

- Max 1GB file size for each upload transaction
- 1 million DAU with 10 queries / day
- Queries / day: 1x10<sup>7</sup> queries
- Peak / day: 2x10<sup>7</sup> queries -->


- Horizontal scaling of servers with load balancer to redirect traffic
- Master - Slave DB. Write operations only done on master db and read from slave db
- Data replication between master and slave db to ensure consistency

![Arch](images/systemArchFuture.png)

<!-- LICENSE -->

## License

Distributed under the MIT License. See `LICENSE` for more information.
