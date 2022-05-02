import pandas as pd
from sqlalchemy import create_engine
from decouple import config
from sqlConnexion import SqlConnexionClient


class SqLiteClient(SqlConnexionClient):
    def __init__(self):
        super().__init__()

    def _get_engine(self):
        db_uri = f"{self.dialect}:///{self.db_name}"
        if not self._engine:
            self._engine = create_engine(db_uri)
        return self._engine


# if __name__ == "__main__":
#    # db = "/tmp/sqlite_default.db"
#    sqlite_cli = SqLiteClient()
#    print(sqlite_cli.to_frame("SELECT * FROM stocks_daily"))
