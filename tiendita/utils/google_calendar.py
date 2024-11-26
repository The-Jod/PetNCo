from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
import os
import pickle
from datetime import datetime, timedelta

SCOPES = ['https://www.googleapis.com/auth/calendar']

def get_google_calendar_service(credentials=None):
    """
    Obtiene el servicio de Google Calendar
    """
    creds = None
    
    if credentials:
        creds = Credentials.from_authorized_user_info(credentials, SCOPES)
    
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
    
    service = build('calendar', 'v3', credentials=creds)
    return service

def crear_evento_calendario(service, titulo, descripcion, fecha_inicio, fecha_fin, timezone='America/Santiago'):
    """
    Crea un evento en Google Calendar
    """
    evento = {
        'summary': titulo,
        'description': descripcion,
        'start': {
            'dateTime': fecha_inicio.isoformat(),
            'timeZone': timezone,
        },
        'end': {
            'dateTime': fecha_fin.isoformat(),
            'timeZone': timezone,
        },
        'reminders': {
            'useDefault': True
        }
    }
    
    event = service.events().insert(calendarId='primary', body=evento).execute()
    return event['id'] 