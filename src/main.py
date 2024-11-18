from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from email.mime.text import MIMEText
from fastapi import HTTPException
from dotenv import load_dotenv
import requests
import save_data
import get_token
import logging
import smtplib
import os
import asyncio

load_dotenv()

EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD")

logging.basicConfig(
    filename="api_logs.log",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

#iniciar api: uvicorn main:app --host 0.0.0.0 --port 8000 --workers 1
# mkdocs serve -a 127.0.0.1:9000 

app = FastAPI(
    title="API para la obtencion de datos generados por el aparato ArduinoUNOR4",
    version="1.0.0"
)

# log
@app.middleware("http")
async def log_requests(request: Request, call_next):
    logging.info(f"Solicitud entrante: {request.method} {request.url}")
    save_data.log_to_db('INFO', f"Solicitud entrante: {request.method} {request.url}", str(request.url))

    response = await call_next(request)

    logging.info(f"Llamada completada {response.status_code}")
    save_data.log_to_db('INFO', f"Llamada completada: {response.status_code}", str(request.url), response.status_code)

    return response

# Montar archivos estáticos
# app.mount("/static", StaticFiles(directory="static"), name="static")

# # Configurar plantillas
# templates = Jinja2Templates(directory="templates")


# @app.get("/", response_class=HTMLResponse)
# async def read_root(request: Request):
#     return templates.TemplateResponse("index.html", {"request": request})

# Funcion obtener data
@app.get("/data")
async def get_data():
    global sent_email
    try:
        url = f"https://api2.arduino.cc/iot/v2/things/{get_token.THING_ID}/properties"
        headers = {
            "Authorization": f"Bearer {get_token.get_access_token()}",
            "Content-Type": "application/json"
        }
        
        # Hacer la solicitud a la API de Arduino
        response = requests.get(url, headers=headers)

        # Verificar si la solicitud fue exitosa
        if response.status_code != 200:
            error_message = f"Error en la API de Arduino: {response.status_code} - {response.text}"
            logging.error(error_message)
            
            if not sent_email:
                #send_error_email(error_message)
                sent_email = True
                save_data.log_to_db(error_message, endpoint="error", status_code=502)
            raise HTTPException(status_code=502, detail="Error al conectar con la API Arduino. Posible estado Offline")
        
        # Parsear la respuesta de la API
        data = response.json()
        
        if not data or data == "":
            print("no hay data")
            
        return data

    except requests.exceptions.RequestException as e:
        logging.error(f"La API tuvo un error en su solicitud: {str(e)}.")
        raise HTTPException(status_code=502, detail="Error al obtener datos de la API de Arduino. Posible estado Offline")
    except Exception as e:
        logging.error(f"La API tuvo un error en su solicitud: {str(e)}.")
        #send_error_email(f"Error al obtener datos de la API de Arduino: {str(e)}")  # Enviar correo si falla la API
        raise HTTPException(status_code=500, detail="Error al obtener datos de la API de Arduino. Posible estado Offline")

    # Función para enviar correos en caso de error
def send_error_email(error_message):
    try:
        server = smtplib.SMTP_SSL('mail.starflowers.com.ec', 465)
        server.login("pasante.sistemas@starflowers.com.ec", EMAIL_PASSWORD)
        
        # Crear el mensaje con el asunto y el cuerpo
        subject = "Error en la API de Arduino de Cuarto Frio"
        body = f"Ocurrió un error con la API: {error_message}"
        
        # Crear el objeto MIMEText para el correo
        msg = MIMEText(body)
        msg['Subject'] = subject
        msg['From'] = "pasante.sistemas@starflowers.com.ec"
        msg['To'] = "sistemas@starflowers.com.ec"
        
        # Enviar el correo
        server.sendmail("pasante.sistemas@starflowers.com.ec", "sistemas@starflowers.com.ec", msg.as_string())
        
        logging.error("Se envió el correo de manera satisfactoria")
        server.quit()
    except Exception as e:
        logging.error(f"Error al enviar el correo: {str(e)}")


# Manejo global de excepciones
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logging.error(f"Excepción no controlada: {str(exc)}")
    send_error_email("Ocurrio un error con el manejo de excepciones " + str(exc))
    raise HTTPException(status_code=500, detail="Ocurrio un error interno en el servidor")

# Hilo para guardar datos en la base de datos cada 1 minuto
async def save_data_periodically():
    while True:
        try:
            # Obtener datos desde la API
            data = await get_data()
            # Guardar los datos en la base de datos
            save_data.save_data_to_db(data)
            print('Datos guardados en la base de datos.')
            logging.info("Datos guardados en la base de datos.")
            save_data.log_to_db('INFO', "Datos guardados en la base de datos.", endpoint='guardado', status_code=200)

        except ValueError as e:
            error_message = f"Error en el proceso periódico de guardado de datos: {str(e)}"
            logging.error(error_message)
            save_data.log_to_db('ERROR', error_message, endpoint='fallido', status_code=500)
            send_error_email(error_message)

        # Pausar 1 minuto antes de la siguiente ejecución de forma asincrónica
        await asyncio.sleep(60)

# Iniciar la tarea asíncrona en el evento de inicio de FastAPI
@app.on_event("startup")
async def startup_event():
    try:
        # Crear la tarea asíncrona para el guardado periódico
        asyncio.create_task(save_data_periodically())
        logging.info("Tarea asíncrona iniciada para guardar datos cada 1 minuto.")
        save_data.log_to_db('INFO', "Tarea asíncrona iniciada para guardar datos cada 1 minuto.", endpoint='iniciado', status_code=200)
    except Exception as e:
        error_message = f"Error al iniciar la tarea asíncrona: {str(e)}"
        logging.error(error_message)
        save_data.log_to_db('ERROR', error_message, endpoint='inicio_fallido', status_code=500)
        send_error_email(error_message)