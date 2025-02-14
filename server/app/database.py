import mysql.connector
from mysql.connector import Error

DB_CONFIG = {
    "host": "localhost",
    "user": "root",
    "password": "root",
    "database": "freightos",
    "port": "8889",
}


def get_db_connection():
    try:
        conn = mysql.connector.connect(**DB_CONFIG, connection_timeout=5)
        return conn
    except Error as e:
        print(f"❌ Database connection error: {e}")
        return None
