import pandas as pd

from sqlalchemy import create_engine, inspect
from decouple import config

import sqlalchemy

import sqlConnexion as con
from sqlalchemy.ext.declarative import declarative_base


class SqlPostgresClient(con.SqlConnexionClient):
    """SqlPostgresClient is a class to connect to a postgresql database

    parameter are taken from the .env file

    Functions:
    ---------
     _get_engine,

     _connect,

     _cursor_columns,

     execute,

     insert_from_frame,

     to_frame


    """

    def __init__(self):

        super().__init__()

        self.user = config("DB_USER")
        self.password = config("DB_PASSWORD")
        self.host = config("DB_HOST")
        self.port = config("DB_PORT")
        self.schema = config("DB_SCHEMA")
        print(config("DB_HOST"))
        self.autocommit = config("DB_AUTOCOMMIT", cast=bool)
        self.db = f"{self.user}:{self.password}@{self.host}:{self.port}/{self.db_name}"
        print("en postgresCli")
        print(f"{self.dialect}://{self.db}")

    def _get_engine(self):
        db_uri = f"{self.dialect}://{self.db}"
        if not self.engine:
            self.engine = create_engine(
                db_uri, connect_args={"options": "-csearch_path={}".format(self.schema)}
            )
        return self.engine


# if __name__ == "__main__":
#   connect_cli = SqlPostgresClient()
#  print(connect_cli.to_frame("select * from avg_delays"))
