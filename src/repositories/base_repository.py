
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

    @contextmanager
    def connection_scope(self, existing_connection=None):
        """
        Reuse an existing transaction connection when supplied.
        Otherwise, open a normal repository connection.
        """
        if existing_connection is not None:
            yield existing_connection
            return

        with self.connection() as connection:
            yield connection
