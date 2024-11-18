from dotenv import load_dotenv
import os
import requests
import save_data

load_dotenv()

CLIENT_ID = os.getenv("CLIENT_ID")
CLIENT_SECRET = os.getenv("CLIENT_SECRET")
THING_ID = os.getenv("THING_ID")

try:
    def get_access_token():
        url = "https://api2.arduino.cc/iot/v1/clients/token"
        payload = {
            "grant_type": "client_credentials",
            "client_id": CLIENT_ID,
            "client_secret": CLIENT_SECRET,
            "audience": "https://api2.arduino.cc/iot"
        }
        response = requests.post(url, data=payload)
        return response.json()["access_token"]
except Exception as e:
    error_message = f"Ocurrio un error con el token. Error: {e}"
    print(error_message)
    save_data.log_to_db(error_message, status_code=500, endpoint="token error")