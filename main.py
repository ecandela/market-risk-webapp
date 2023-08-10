import streamlit as st
import pandas as pd
import numpy as np
import os
from io import BytesIO
from googleapiclient.discovery import build
from oauth2client.service_account import ServiceAccountCredentials
from googleapiclient.http import MediaIoBaseDownload
from io import StringIO
import requests

class GoogleDriveService:
    def __init__(self):
        self._SCOPES=['https://www.googleapis.com/auth/drive']

        _base_path = os.path.dirname(__file__)
        _credential_path=os.path.join(_base_path, 'credential.json')
        os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = _credential_path

    def build(self):
        creds = ServiceAccountCredentials.from_json_keyfile_name(os.getenv("GOOGLE_APPLICATION_CREDENTIALS"), self._SCOPES)
        service = build('drive', 'v3', credentials=creds)

        return service , creds

def getFileListFromGDrive():
    selected_fields="files(id,name,webViewLink)"
    service , creds =GoogleDriveService().build()
    list_file=service.files().list(fields=selected_fields).execute()
    print({"files":list_file.get("files")})


    file_id = "1g-BC4wL9mSq68XZ31RkVl9ItabP6O1sd"  # Please set the file ID of the CSV file.

    # Descarga el archivo en un objeto de BytesIO
    request = service.files().get_media(fileId=file_id)
    fh = BytesIO()
    downloader = MediaIoBaseDownload(fh, request)
    done = False
    while not done:
        status, done = downloader.next_chunk()

    # Convierte los datos en un DataFrame
    fh.seek(0)  # Reinicia el puntero del archivo
    data = fh.read().decode('utf-8')  # Decodifica los datos en texto (si es necesario)
    df = pd.read_csv(StringIO(data))  # Crea un DataFrame desde los datos


    return df

df_data = getFileListFromGDrive()

#print(df_data.head())


st.dataframe(df_data)


#st.title('Uber pickups in NYC2')
