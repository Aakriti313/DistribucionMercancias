# import mysql.connector # type: ignore
# from sqlalchemy import create_engine


# # Conexión a la base de datos MySQL
# def obtener_conexion():
#     try:
#         conn = mysql.connector.connect(
#             host="10.0.40.21",
#             user="PortatilDeMarc",
#             password="laragon123",
#             database="plataforma_logistica"
#         )
#         return conn
#     except mysql.connector.Error as err:
#         print(f"Error de conexión: {err}")
#         return None
import mysql.connector

def obtener_conexion():
    try:
        # Establecemos la conexión
        db_connection = mysql.connector.connect(
            host="localhost",  # o la IP de tu servidor de base de datos
            user="root",
            password="",  # Si tienes una contraseña, cámbiala aquí
            database="plataforma_logistica"
        )
        return db_connection
    except mysql.connector.Error as err:
        print(f"Error de conexión: {err}")
        return None

def obtener_cursor():
    # Obtén la conexión
    db_connection = obtener_conexion()
    if db_connection:
        # Crea y retorna el cursor
        cursor = db_connection.cursor()
        return cursor, db_connection
    else:
        return None, None
