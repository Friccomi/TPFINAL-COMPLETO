import pandas as pd
from sqlalchemy import create_engine, inspect
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import scoped_session, sessionmaker
from decouple import config


class SqlConnexionClient:
    """The SqlConnexionClient is a parent class to be used in the other child
         connexion classes
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
        self.db_name = config("DB_NAME")
        self.dialect = config("DB_DIALECT")
        self.engine = None

    def _get_engine(self):
        pass

    def _connect(self):
        return self._get_engine().connect()

    @staticmethod
    def _cursor_columns(cursor):
        if hasattr(cursor, "keys"):
            return cursor.keys()
        else:
            return [c[0] for c in cursor.description]

    def execute(self, sql, connection=None):
        if connection is None:
            connection = self._connect()
        return connection.execute(sql)

    def insert_from_frame(self, df, table, if_exists="append", index=False, **kwargs):
        connection = self._connect()

        with connection:
            print("antes de grabar")
            print(df)
            print(table)
            df.to_sql(table, connection, if_exists=if_exists, index=index, **kwargs)

    def to_frame(self, *args, **kwargs):
        cursor = self.execute(*args, **kwargs)
        if not cursor:
            return
        data = cursor.fetchall()
        if data:
            df = pd.DataFrame(data, columns=self._cursor_columns(cursor))
        else:
            df = pd.DataFrame()
        return df
