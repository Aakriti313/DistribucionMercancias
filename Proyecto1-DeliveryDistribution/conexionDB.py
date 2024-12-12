import mysql.connector # type: ignore
from sqlalchemy import create_engine

# Conexión a la base de datos MySQL
def obtener_conexion():
    try:
        conn = mysql.connector.connect(
            host="localhost",
            user="root",
            password="",
            database="plataforma_logistica"
        )
        return conn
    except mysql.connector.Error as err:
        print(f"Error de conexión: {err}")
        return None