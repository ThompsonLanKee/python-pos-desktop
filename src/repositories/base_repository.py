

from contextlib import contextmanager

from src.core.database import Database


class BaseRepository:

    def __init__(self, database: Database):
        self.database = database

    @contextmanager
    def connection(self):

        connection = self.database.connect()

        try:
            yield connection
            connection.commit()

        except Exception:
            connection.rollback()
            raise

        finally:
            connection.close()
