import os
import pyodbc
from datetime import datetime
from dotenv import load_dotenv
import mail

# Cargar variables de entorno
load_dotenv()

# Función de manejo centralizado de excepciones
def log_and_notify_error(message, exception=None, endpoint=None, status_code=None):
    error_detail = f"{message}: {exception}" if exception else message
    print(error_detail)
    log_to_db("ERROR", error_detail, endpoint, status_code)
    mail.send_mail(error_detail)

# Configuración de la conexión a SQL Server
try:
    conn = pyodbc.connect(
        r'DRIVER={ODBC Driver 17 for SQL Server};'
        f'SERVER={os.getenv("DATABASE_SERVER")};'
        f'DATABASE={os.getenv("DATABASE_NAME")};'
        f'UID={os.getenv("DATABASE_USER")};'
        f'PWD={os.getenv("DATABASE_PASSWORD")}'
    )
    print("Conexión con la base de datos establecida")
except Exception as e:
    log_and_notify_error("Error al conectar con la base de datos", e)

def get_value_from_db(query):
    cursor_u = conn.cursor()
    if cursor_u:
        try:
            result = cursor_u.execute(query).fetchone()
            if result:
                return str(result[0])
            else:
                print(f"Error: No se encontró ningún resultado para la consulta: {query}")
                return None
        except Exception as e:
            print(f"Ocurrió un error al ejecutar la consulta: {e}")
            return None
        
url_token_query = """SELECT prm_valor
                FROM dbo.Parametros_Sistema
                WHERE id_grupo = 1 AND prm_descripcion = 'url_token'"""

url_aud_query = """SELECT prm_valor
                FROM dbo.Parametros_Sistema
                WHERE id_grupo = 1 AND prm_descripcion = 'url_aud'"""

cl_id_query = """SELECT prm_valor
                FROM dbo.Parametros_Sistema
                WHERE id_grupo = 1 AND prm_descripcion = 'cl_id'"""

cl_se_query  = """SELECT prm_valor
                FROM dbo.Parametros_Sistema
                WHERE id_grupo = 1 AND prm_descripcion = 'cl_se'"""

url_api_query = """SELECT prm_valor
                FROM dbo.Parametros_Sistema
                WHERE id_grupo = 1 AND prm_descripcion = 'url_api'"""

cl_th_query = """SELECT prm_valor
    FROM dbo.Parametros_Sistema
                WHERE id_grupo = 1 AND prm_descripcion = 'cl_th'"""

user_mail_query = """SELECT prm_valor
                FROM dbo.Parametros_Sistema
                WHERE id_grupo = 8 AND prm_descripcion = 'user_mail'"""

password_mail_query = """SELECT prm_valor
                FROM dbo.Parametros_Sistema
                WHERE id_grupo = 8 AND prm_descripcion = 'password_mail'"""

server_mail_query = """SELECT prm_valor
                FROM dbo.Parametros_Sistema
                WHERE id_grupo = 8 AND prm_descripcion = 'domain_mail'"""

port_mail_query = """SELECT prm_valor
                FROM dbo.Parametros_Sistema
                WHERE id_grupo = 8 AND prm_descripcion = 'port'"""

target_mail_query = """SELECT prm_valor
                FROM dbo.Parametros_Sistema
                WHERE id_grupo = 8 AND prm_descripcion = 'mail_sis'"""

def get_url_token():
    return get_value_from_db(url_token_query)

def get_url_aud():
    return get_value_from_db(url_aud_query)

def get_cl_id():
    return get_value_from_db(cl_id_query)

def get_cl_se():
    return get_value_from_db(cl_se_query)

def get_url_api():
    return get_value_from_db(url_api_query)

def get_cl_th():
    return get_value_from_db(cl_th_query)

def get_user_mail():
    return get_value_from_db(user_mail_query)

def get_pass_mail():
    return get_value_from_db(password_mail_query)

def get_port_mail():
    return get_value_from_db(port_mail_query)

def get_server_mail():
    return get_value_from_db(server_mail_query)

def get_user_target():
    return get_value_from_db(target_mail_query)

def save_data_to_db(data):
    if data is None:
        print("Data es None, no se procesará")
        return
    if not conn:
        print("Conexión a la base de datos no disponible")
        return

    with conn.cursor() as cursor:
        try:
            if isinstance(data, list):
                for item in data:
                    if not isinstance(item, dict):
                        log_to_db('ERROR', f"Item no válido: {item}")
                        continue
                    process_and_insert(cursor, item)
            elif isinstance(data, dict):
                process_and_insert(cursor, data)
            else:
                log_to_db('ERROR', 'El tipo de dato proporcionado no es válido.', endpoint='/save_data')
            conn.commit()
        except Exception as e:
            log_and_notify_error("Error al guardar datos en la base de datos", e)

def process_and_insert(cursor, item):
    try:
        item['created_at'] = parse_datetime(item.get('created_at'))
        item['updated_at'] = parse_datetime(item.get('updated_at'))
        item['value_updated_at'] = parse_datetime(item.get('value_updated_at'))
        item['last_value'] = float(item.get('last_value', 0))
        cursor.execute(insert_query, item['created_at'], item['href'], item['id'], item['last_value'],
                       item['linked_to_trigger'], item['name'], item['permission'], item['persist'], item['tag'],
                       item['thing_id'], item['thing_name'], item['type'], item['update_parameter'],
                       item['update_strategy'], item['updated_at'], item['value_updated_at'], item['variable_name'])
    except Exception as e:
        log_and_notify_error("Error al procesar o insertar datos", e)

def parse_datetime(date_str):
    if not date_str:
        return None
    for fmt in ("%Y-%m-%dT%H:%M:%S.%fZ", "%Y-%m-%dT%H:%M:%S.%f", "%Y-%m-%dT%H:%M:%S"):
        try:
            return datetime.strptime(date_str, fmt)
        except ValueError:
            continue
    return None

def log_to_db(log_level, message, endpoint=None, status_code=None):
    if not conn:
        print("No hay conexión a la base de datos para registrar logs")
        return
    with conn.cursor() as cursor:
        cursor.execute("""
            INSERT INTO APILogs (log_level, message, endpoint, status_code)
            VALUES (?, ?, ?, ?)
        """, log_level, message, endpoint, status_code)
        conn.commit()

insert_query = """
    INSERT INTO Cuarto_Frio_ArduinoUNOR4 (
        created_at, href, property_id, last_value, linked_to_trigger,
        name, permission, persist, tag, thing_id, thing_name,
        type, update_parameter, update_strategy, updated_at, value_updated_at, variable_name
    )
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
"""
