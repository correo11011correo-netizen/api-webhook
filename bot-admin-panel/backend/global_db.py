# -*- coding: utf-8 -*-
import os
import logging
from psycopg2 import pool, extras

class GlobalDatabaseManager:
    """
    Gestor de la base de datos maestra de Stock Pro.
    Permite la autenticacion compartida y gestion de sesiones.
    """
    def __init__(self):
        self.logger = logging.getLogger("GlobalDatabaseManager")
        self.db_url = os.environ.get("DATABASE_URL")
        if not self.db_url:
            self.logger.critical("DATABASE_URL no encontrada en el entorno.")
            raise Exception("Error: Railway DATABASE_URL no configurada.")

        try:
            self.pool = pool.ThreadedConnectionPool(1, 20, dsn=self.db_url)
            self.logger.info("Pool de DB Global (Stock Pro) inicializado.")
        except Exception as e:
            self.logger.critical(f"Error inicializando el pool de la DB global: {e}")
            raise e

    def _get_connection(self):
        return self.pool.getconn()

    def _return_connection(self, conn):
        self.pool.putconn(conn)

    def execute(self, query, params=()):
        try:
            conn = self._get_connection()
            with conn.cursor() as cursor:
                cursor.execute(query, params)
                conn.commit()
            self._return_connection(conn)
            return True
        except Exception as e:
            self.logger.error(f"Global execute error: {e}")
            return None

    def fetch_one(self, query, params=()):
        try:
            conn = self._get_connection()
            with conn.cursor(cursor_factory=extras.RealDictCursor) as cursor:
                cursor.execute(query, params)
                res = cursor.fetchone()
            self._return_connection(conn)
            return res
        except Exception as e:
            self.logger.error(f"Global fetch_one error: {e}")
            return None

    def fetch_all(self, query, params=()):
        try:
            conn = self._get_connection()
            with conn.cursor(cursor_factory=extras.RealDictCursor) as cursor:
                cursor.execute(query, params)
                res = cursor.fetchall()
            self._return_connection(conn)
            return res
        except Exception as e:
            self.logger.error(f"Global fetch_all error: {e}")
            return []
