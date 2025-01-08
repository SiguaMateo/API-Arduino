from fastapi import FastAPI
import requests
import asyncio
import uvicorn
import os

try:
    import data_base
    import get_token
    import mail
except ImportError as e:
    raise ImportError(f"Error al importar módulos personalizados: {e}")

app = FastAPI(
    title="API para la obtención de datos generados por el aparato ArduinoUNO R4",
    description="Se utilizó FastAPI para obtener los datos de la nube utilizando Tokens",
    version="1.0.1"
)

sent_emails = set()

def send_email_once(function_name, error_message):
    if function_name not in sent_emails:
        mail.send_mail(error_message)
        sent_emails.add(function_name)

def get_url_base(thing_id):
    url_base = data_base.get_url_api()
    if not url_base:
        error_message = "La URL base no es válida"
        data_base.log_to_db("ERROR", error_message, endpoint="/get_url_base", status_code=400)
        raise ValueError(error_message)
    return url_base.format(THING_ID=thing_id)

def fetch_data():
    url = get_url_base(data_base.get_cl_th())
    headers = {
        "Authorization": f"Bearer {get_token.get_access_token()}",
        "Content-Type": "application/json"
    }
    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.Timeout:
        error_message = "Timeout al conectar con la API."
    except requests.exceptions.ConnectionError:
        error_message = "Error de conexión con la API."
    except requests.exceptions.HTTPError as e:
        error_message = f"HTTPError: {e.response.status_code} {e.response.text}"
    except Exception as e:
        error_message = f"Error desconocido al conectar con la API: {str(e)}"

    data_base.log_to_db("ERROR", error_message, endpoint="/fetch_data", status_code=500)
    send_email_once("fetch_data", error_message)
    raise RuntimeError(error_message)

@app.get("/data")
async def get_data():
    try:
        data = fetch_data()
        if not data:
            return {"message": "No se encontraron datos."}
        return data
    except Exception as e:
        return {"error": f"Falló la obtención de datos: {str(e)}"}

async def save_data_periodically():
    while True:
        try:
            data = fetch_data()
            if data:
                await asyncio.to_thread(data_base.save_data_to_db, data)
                print("informacion guardada " , data)
        except Exception as e:
            error_message = f"Error al guardar datos periódicos: {str(e)}"
            print(error_message)
            data_base.log_to_db("ERROR", error_message, endpoint="/save_periodic", status_code=500)
            send_email_once("save_data_periodically", error_message)
        await asyncio.sleep(60)

@app.on_event("startup")
async def startup_event():
    try:
        asyncio.create_task(save_data_periodically())
        print("Proceso periódico de guardado iniciado correctamente.")
    except Exception as e:
        error_message = f"Error al iniciar el proceso periódico: {str(e)}"
        data_base.log_to_db("ERROR", error_message, endpoint="/startup", status_code=500)
        raise

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=9992, reload=True)
