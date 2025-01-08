try:
    from dotenv import load_dotenv
    import os
    import requests
    import data_base
    import mail
    import data_base
except Exception as e:
    print(f"ERROR, importacion de librerias en get_token, {e}")

load_dotenv()

URL_TOKEN = data_base.get_url_token()
CLIENT_ID = data_base.get_cl_id()
CLIENT_SECRET = data_base.get_cl_se()
URL_AUDIENCE = data_base.get_url_aud()

try:
    def get_access_token():
        payload = {
            "grant_type": "client_credentials",
            "client_id": CLIENT_ID,
            "client_secret": CLIENT_SECRET,
            "audience": URL_AUDIENCE
        }
        response = requests.post(URL_TOKEN, data=payload)
        return response.json()["access_token"]
except Exception as e:
    error_message = f"Ocurrio un error con el token. Error: {e}"
    print(error_message)
    data_base.log_to_db(error_message, status_code=500, endpoint="token error")
    mail(error_message)