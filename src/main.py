try:
    from fastapi import FastAPI
    import requests
    import data_base
    import gettoken
    import send_email
    import asyncio
    import os
    import uvicorn
    from tenacity import retry, stop_after_attempt, wait_fixed
except Exception as e:
    print(f"ERROR, en la importacion de las librerias, {e}")

app = FastAPI(
    title="API para la obtención de datos generados por el aparato ArduinoUNOR4",
    version="1.0.0"
)

# Endpoint base de la API de Arduino
THING_ID = os.getenv("THING_ID")
BASE_URL = f"https://api2.arduino.cc/iot/v2/things/{THING_ID}/properties"

def send_email_once(function_name, error_message):
    """Envía un correo solo si no se ha enviado previamente para un error dado."""
    if not [function_name]:
        send_email.send_mail(error_message)
        [function_name] = True

# Función para obtener datos de la API
@retry(stop=stop_after_attempt(5), wait=wait_fixed(120), reraise=True)
def fetch_data():
    try:
        url = BASE_URL
        headers = {
            "Authorization": f"Bearer {gettoken.get_access_token()}",
            "Content-Type": "application/json"
        }
        response = requests.get(url, headers=headers, timeout=10) 
        response.raise_for_status()  # Lanza excepción para códigos de error HTTP
        return response.json()
    except requests.exceptions.RequestException as e:
        # Registro detallado del error
        error_message = f"Error al conectar con la API: {str(e)}"
        data_base.log_to_db("ERROR", error_message, endpoint="/data", status_code=500)
        send_email_once("fetch_data", error_message)
        raise

# Ruta para obtener datos manualmente
@app.get("/data")
async def get_data():
    try:
        data = fetch_data()
        if not data:
            return {"message": "No se encontraron datos."}
        return data
    except Exception as e:
        return {"error": f"Falló la obtención de datos: {str(e)}"}

# Hilo asíncrono para guardar datos periódicamente
async def save_data_periodically():
    while True:
        try:
            data = fetch_data()  # Llama a la función síncrona dentro de asyncio
            data_base.save_data_to_db(data)
            print(data)
            print("Datos guardados correctamente.")
        except Exception as e:
            error_message = f"Error al guardar datos periódicos: {str(e)}"
            print(error_message)
            data_base.log_to_db("ERROR", error_message, endpoint="/save_periodic", status_code=500)
            send_email_once("save_data_periodically", error_message)
        await asyncio.sleep(60)

# Evento de inicio
@app.on_event("startup")
async def startup_event():
    try:
        asyncio.create_task(save_data_periodically())
        print("Iniciado el guardado periódico de datos.")
    except Exception as e:
        error_message = f"Error al iniciar el proceso periódico: {str(e)}"
        data_base.log_to_db("ERROR", error_message, endpoint="/startup", status_code=500)
        send_email.send_mail("startup_event", error_message)

if __name__ == "__main__":
    uvicorn.run("app:main", host="0.0.0.0", port=9992)