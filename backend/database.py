"""
Module de gestion de la connexion à la base de données MySQL
"""

import mysql.connector
from mysql.connector import pooling
import os
from contextlib import contextmanager

# Configuration de la base de données
DB_CONFIG = {
    'host': os.getenv('DB_HOST', 'localhost'),
    'user': os.getenv('DB_USER', 'root'),
    'password': os.getenv('DB_PASSWORD', 'your_password'),
    'database': os.getenv('DB_NAME', 'exam_scheduling'),
    'charset': 'utf8mb4',
    'collation': 'utf8mb4_unicode_ci'
}

# Pool de connexions pour améliorer les performances
connection_pool = pooling.MySQLConnectionPool(
    pool_name="exam_pool",
    pool_size=10,
    pool_reset_session=True,
    **DB_CONFIG
)

@contextmanager
def get_db_connection():
    """
    Context manager pour obtenir une connexion depuis le pool
    Usage:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT ...")
    """
    conn = connection_pool.get_connection()
    try:
        yield conn
    finally:
        conn.close()

@contextmanager
def get_db_cursor(dictionary=False):
    """
    Context manager pour obtenir un curseur
    Usage:
        with get_db_cursor(dictionary=True) as cursor:
            cursor.execute("SELECT ...")
            results = cursor.fetchall()
    """
    conn = connection_pool.get_connection()
    cursor = conn.cursor(dictionary=dictionary)
    try:
        yield cursor
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        cursor.close()
        conn.close()

def execute_query(query, params=None, fetch=True, dictionary=False):
    """
    Exécute une requête SQL et retourne les résultats
    
    Args:
        query: Requête SQL
        params: Paramètres de la requête (tuple ou dict)
        fetch: Si True, retourne les résultats (fetchall)
        dictionary: Si True, retourne des dictionnaires au lieu de tuples
    
    Returns:
        Liste des résultats si fetch=True, sinon None
    """
    with get_db_cursor(dictionary=dictionary) as cursor:
        cursor.execute(query, params or ())
        if fetch:
            return cursor.fetchall()
        return None

def execute_many(query, data_list):
    """
    Exécute une requête avec plusieurs ensembles de paramètres
    Utile pour les insertions en masse
    """
    with get_db_cursor() as cursor:
        cursor.executemany(query, data_list)
        return cursor.rowcount
