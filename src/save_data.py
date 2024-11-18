from dotenv import load_dotenv
import os
import pyodbc
from datetime import datetime

# Cargar las variables de entorno
load_dotenv()

# Configuración de la conexión a SQL Server
try:
    conn = pyodbc.connect(
        r'DRIVER={ODBC Driver 17 for SQL Server};'
        f'SERVER={os.getenv("DATABASE_SERVER")};'
        f'DATABASE={os.getenv("DATABASE_NAME")};'
        f'UID={os.getenv("DATABASE_USER")};'
        f'PWD={os.getenv("DATABASE_PASSWORD")}'
    )
except Exception as e:
    print("errooooor ----------")

# def create_table_Data():
#     with conn.cursor() as cursor:
#         # Verificar si la tabla existe y eliminarla si es así
#         cursor.execute("""
#             IF EXISTS (SELECT * FROM sysobjects WHERE name='Cuarto_Frio_ArduinoUNO' AND xtype='U')
#             BEGIN
#                 DROP TABLE Cuarto_Frio_ArduinoUNO
#             END
#         """)
#         conn.commit()

#         # Crear una nueva tabla
#         cursor.execute("""
#             CREATE TABLE Cuarto_Frio_ArduinoUNOR4 (
#                 created_at DATETIME,
#                 href VARCHAR(255),
#                 property_id VARCHAR(50),
#                 last_value FLOAT,
#                 linked_to_trigger BIT,
#                 name VARCHAR(50),
#                 permission VARCHAR(20),
#                 persist BIT,
#                 tag INT,
#                 thing_id VARCHAR(50),
#                 thing_name VARCHAR(50),
#                 type VARCHAR(10),
#                 update_parameter INT,
#                 update_strategy VARCHAR(20),
#                 updated_at DATETIME,
#                 value_updated_at DATETIME,
#                 variable_name VARCHAR(50)
#             )
#         """)
#         conn.commit()

def save_data_to_db(data):
    if data is None:
        #log_to_db('ERROR', 'El dato proporcionado es None.')
        print("Data None")
        return
    
    with conn.cursor() as cursor:
        if isinstance(data, list):
            for item in data:
                if not isinstance(item, dict):
                    log_to_db('ERROR', f"Item no es un diccionario: {item}")
                    continue

                #print(f"Datos del item: {item}")  # Para depuración

                item['created_at'] = parse_datetime(str(item.get('created_at', '')))
                item['updated_at'] = parse_datetime(str(item.get('updated_at', '')))
                item['value_updated_at'] = parse_datetime(str(item.get('value_updated_at', '')))

                # Validaciones adicionales de fecha
                if item['created_at'] is None:
                    print()
                if item['updated_at'] is None:
                    print()
                if item['value_updated_at'] is None:
                    print()

                try:
                    item['last_value'] = float(item.get('last_value', 0))
                except Exception as e:
                    continue  # Saltar este ítem si hay un error de conversión

                #print(f"Datos listos para insertar: {item}")  # Imprime los datos que serán insertados

                # Inserción de datos en la base de datos
                cursor.execute("""
                    INSERT INTO Cuarto_Frio_ArduinoUNOR4 (
                        created_at, href, property_id, last_value, linked_to_trigger,
                        name, permission, persist, tag, thing_id, thing_name,
                        type, update_parameter, update_strategy, updated_at, value_updated_at, variable_name
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, 
                item['created_at'], item['href'], item['id'], item['last_value'], item['linked_to_trigger'],
                item['name'], item['permission'], item['persist'], item['tag'], item['thing_id'], item['thing_name'],
                item['type'], item['update_parameter'], item['update_strategy'], item['updated_at'], item['value_updated_at'], item['variable_name'])

        elif isinstance(data, dict):
            # Asegúrate de que 'data' es un diccionario
            data['created_at'] = parse_datetime(str(data.get('created_at', '')))
            data['updated_at'] = parse_datetime(str(data.get('updated_at', '')))
            data['value_updated_at'] = parse_datetime(str(data.get('value_updated_at', '')))

            if data['created_at'] is None or data['updated_at'] is None or data['value_updated_at'] is None:
                log_to_db('ERROR', 'Alguna fecha no es válida.', endpoint='/save_data')
                return

            try:
                data['last_value'] = float(data.get('last_value', 0))
            except ValueError as e:
                return  # No insertar si hay un error de conversión

            cursor.execute("""
                INSERT INTO Cuarto_Frio_ArduinoUNOR4 (
                    created_at, href, property_id, last_value, linked_to_trigger,
                    name, permission, persist, tag, thing_id, thing_name,
                    type, update_parameter, update_strategy, updated_at, value_updated_at, variable_name
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, 
            data['created_at'], data['href'], data['id'], data['last_value'], data['linked_to_trigger'],
            data['name'], data['permission'], data['persist'], data['tag'], data['thing_id'], data['thing_name'],
            data['type'], data['update_parameter'], data['update_strategy'], data['updated_at'], data['value_updated_at'], data['variable_name'])
        
        else:
            log_to_db('ERROR', 'El tipo de dato proporcionado no es válido.', endpoint='/save_data')
    conn.commit()


# def create_table_Logs():
#     with conn.cursor() as cursor:
#         # Verificar si la tabla existe y eliminarla si es así
#         cursor.execute("""
#             IF EXISTS (SELECT * FROM sysobjects WHERE name='APILogs' AND xtype='U')
#             BEGIN
#                 DROP TABLE APILogs
#             END
#         """)
#         conn.commit()

#         # Crear una nueva tabla
#         cursor.execute("""
#             CREATE TABLE APILogs (
#             log_time DATETIME DEFAULT GETDATE(),
#             log_level VARCHAR(20),
#             message TEXT,
#             endpoint VARCHAR(255),
#             status_code INT
#             )
#         """)
#         conn.commit()


# create_table_Data()
# create_table_Logs()


def log_to_db(log_level, message, endpoint=None, status_code=None):
    with conn.cursor() as cursor:
        cursor.execute("""
            INSERT INTO APILogs (log_level, message, endpoint, status_code)
            VALUES (?, ?, ?, ?)
        """, log_level, message, endpoint, status_code)
        conn.commit()

def parse_datetime(date_str):
    for fmt in ("%Y-%m-%dT%H:%M:%S.%fZ", "%Y-%m-%dT%H:%M:%S.%f", "%Y-%m-%dT%H:%M:%S"):
        try:
            return datetime.strptime(date_str, fmt)
        except ValueError:
            continue
    return None  # Retornar None si no se pudo convertir