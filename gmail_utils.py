import configparser
import os
import pickle

from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build, Resource

config = configparser.ConfigParser()
config.read('config.ini')

google_api_config = config["GoogleAPI"]

CLIENT_SECRET_FILE_PATH = google_api_config['CLIENT_SECRET_FILE']
API_NAME = google_api_config['API_NAME']
API_VERSION = google_api_config['API_VERSION']
SCOPES = ['https://www.googleapis.com/auth/gmail.readonly', 'https://www.googleapis.com/auth/gmail.modify']


def authenticate_gmail() -> Resource:
    credentials = None

    if os.path.exists('token.pickle'):
        with open('token.pickle', 'rb') as token:
            credentials = pickle.load(token)

    if not credentials or not credentials.valid:
        if credentials and credentials.refresh_token and credentials.expired:
            credentials.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(CLIENT_SECRET_FILE_PATH, SCOPES)
            credentials = flow.run_local_server(port=0)

        with open('token.pickle', 'wb') as token:
            pickle.dump(credentials, token)

    service = build(API_NAME, API_VERSION, credentials=credentials)
    return service
