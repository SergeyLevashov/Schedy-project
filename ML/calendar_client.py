"""
Google Calendar Integration Module
Handles authentication and CRUD operations with Google Calendar API
"""

import os
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

logger = logging.getLogger(__name__)

class GoogleCalendarClient:
    """
    Google Calendar API client with authentication and event management
    """

    def __init__(self, credentials_file: str = 'credentials.json', 
                 token_file: str = 'token.json',
                 scopes: List[str] = None):
        self.credentials_file = credentials_file
        self.token_file = token_file
        self.scopes = scopes or ['https://www.googleapis.com/auth/calendar']
        self.service = None
        self.creds = None

        # Initialize the service
        self._authenticate()

    def _authenticate(self):
        """
        Authenticate with Google Calendar API
        """
        try:
            # Load existing token
            if os.path.exists(self.token_file):
                self.creds = Credentials.from_authorized_user_file(self.token_file, self.scopes)

            # If there are no (valid) credentials available, let the user log in
            if not self.creds or not self.creds.valid:
                if self.creds and self.creds.expired and self.creds.refresh_token:
                    self.creds.refresh(Request())
                else:
                    if not os.path.exists(self.credentials_file):
                        raise FileNotFoundError(
                            f"Credentials file not found: {self.credentials_file}. "
                            "Please download it from Google Cloud Console."
                        )

                    flow = InstalledAppFlow.from_client_secrets_file(
                        self.credentials_file, self.scopes)
                    self.creds = flow.run_local_server(port=0)

                # Save the credentials for the next run
                with open(self.token_file, 'w') as token:
                    token.write(self.creds.to_json())

            # Build the service
            self.service = build('calendar', 'v3', credentials=self.creds)
            logger.info("Successfully authenticated with Google Calendar API")

        except Exception as e:
            logger.error(f"Error authenticating with Google Calendar: {e}")
            raise

    def create_event(self, event_data: Dict[str, Any], calendar_id: str = 'primary') -> Optional[str]:
        """
        Create a new calendar event

        Args:
            event_data (Dict): Event data in Google Calendar format
            calendar_id (str): Calendar ID to create event in

        Returns:
            Optional[str]: Event ID if successful, None otherwise
        """
        try:
            event = self.service.events().insert(
                calendarId=calendar_id,
                body=event_data
            ).execute()

            event_id = event.get('id')
            logger.info(f"Created event with ID: {event_id}")
            return event_id

        except HttpError as e:
            logger.error(f"HTTP error creating event: {e}")
            return None
        except Exception as e:
            logger.error(f"Error creating event: {e}")
            return None

    def get_events(self, calendar_id: str = 'primary', 
                   time_min: Optional[datetime] = None,
                   time_max: Optional[datetime] = None,
                   max_results: int = 10) -> List[Dict[str, Any]]:
        """
        Get events from calendar

        Args:
            calendar_id (str): Calendar ID
            time_min (Optional[datetime]): Start time filter
            time_max (Optional[datetime]): End time filter
            max_results (int): Maximum number of events to return

        Returns:
            List[Dict]: List of events
        """
        try:
            # Set default time range if not provided
            if time_min is None:
                time_min = datetime.utcnow()
            if time_max is None:
                time_max = time_min + timedelta(days=30)

            events_result = self.service.events().list(
                calendarId=calendar_id,
                timeMin=time_min.isoformat() + 'Z',
                timeMax=time_max.isoformat() + 'Z',
                maxResults=max_results,
                singleEvents=True,
                orderBy='startTime'
            ).execute()

            events = events_result.get('items', [])
            logger.info(f"Retrieved {len(events)} events")
            return events

        except HttpError as e:
            logger.error(f"HTTP error getting events: {e}")
            return []
        except Exception as e:
            logger.error(f"Error getting events: {e}")
            return []

    def update_event(self, event_id: str, event_data: Dict[str, Any], 
                     calendar_id: str = 'primary') -> bool:
        """
        Update an existing event

        Args:
            event_id (str): Event ID to update
            event_data (Dict): Updated event data
            calendar_id (str): Calendar ID

        Returns:
            bool: True if successful, False otherwise
        """
        try:
            updated_event = self.service.events().update(
                calendarId=calendar_id,
                eventId=event_id,
                body=event_data
            ).execute()

            logger.info(f"Updated event with ID: {event_id}")
            return True

        except HttpError as e:
            logger.error(f"HTTP error updating event: {e}")
            return False
        except Exception as e:
            logger.error(f"Error updating event: {e}")
            return False

    def delete_event(self, event_id: str, calendar_id: str = 'primary') -> bool:
        """
        Delete an event

        Args:
            event_id (str): Event ID to delete
            calendar_id (str): Calendar ID

        Returns:
            bool: True if successful, False otherwise
        """
        try:
            self.service.events().delete(
                calendarId=calendar_id,
                eventId=event_id
            ).execute()

            logger.info(f"Deleted event with ID: {event_id}")
            return True

        except HttpError as e:
            logger.error(f"HTTP error deleting event: {e}")
            return False
        except Exception as e:
            logger.error(f"Error deleting event: {e}")
            return False

    def find_events_by_summary(self, summary: str, calendar_id: str = 'primary',
                               time_min: Optional[datetime] = None,
                               time_max: Optional[datetime] = None) -> List[Dict[str, Any]]:
        """
        Find events by summary/title

        Args:
            summary (str): Event summary to search for
            calendar_id (str): Calendar ID
            time_min (Optional[datetime]): Start time filter
            time_max (Optional[datetime]): End time filter

        Returns:
            List[Dict]: Matching events
        """
        try:
            events = self.get_events(calendar_id, time_min, time_max, max_results=100)

            matching_events = []
            for event in events:
                event_summary = event.get('summary', '').lower()
                if summary.lower() in event_summary:
                    matching_events.append(event)

            logger.info(f"Found {len(matching_events)} events matching '{summary}'")
            return matching_events

        except Exception as e:
            logger.error(f"Error finding events by summary: {e}")
            return []

    def get_free_busy(self, time_min: datetime, time_max: datetime,
                      calendar_ids: List[str] = None) -> Dict[str, List[Dict]]:
        """
        Get free/busy information for calendars

        Args:
            time_min (datetime): Start time
            time_max (datetime): End time
            calendar_ids (List[str]): List of calendar IDs to check

        Returns:
            Dict: Free/busy information
        """
        if calendar_ids is None:
            calendar_ids = ['primary']

        try:
            body = {
                'timeMin': time_min.isoformat() + 'Z',
                'timeMax': time_max.isoformat() + 'Z',
                'items': [{'id': cal_id} for cal_id in calendar_ids]
            }

            freebusy_result = self.service.freebusy().query(body=body).execute()

            logger.info("Retrieved free/busy information")
            return freebusy_result.get('calendars', {})

        except HttpError as e:
            logger.error(f"HTTP error getting free/busy: {e}")
            return {}
        except Exception as e:
            logger.error(f"Error getting free/busy: {e}")
            return {}

class EventBuilder:
    """
    Helper class to build Google Calendar event objects
    """

    @staticmethod
    def build_event(summary: str, start_datetime: datetime, end_datetime: datetime,
                    description: str = "", location: str = "", timezone: str = "Europe/Moscow",
                    attendees: List[str] = None, reminders: Dict = None) -> Dict[str, Any]:
        """
        Build a Google Calendar event object

        Args:
            summary (str): Event title
            start_datetime (datetime): Start datetime
            end_datetime (datetime): End datetime
            description (str): Event description
            location (str): Event location
            timezone (str): Timezone
            attendees (List[str]): List of attendee emails
            reminders (Dict): Reminder configuration

        Returns:
            Dict[str, Any]: Google Calendar event object
        """
        event = {
            'summary': summary,
            'start': {
                'dateTime': start_datetime.isoformat(),
                'timeZone': timezone,
            },
            'end': {
                'dateTime': end_datetime.isoformat(),
                'timeZone': timezone,
            },
            'description': description,
            'location': location,
        }

        # Add attendees if provided
        if attendees:
            event['attendees'] = [{'email': email} for email in attendees]

        # Add reminders
        if reminders:
            event['reminders'] = reminders
        else:
            event['reminders'] = {
                'useDefault': False,
                'overrides': [
                    {'method': 'popup', 'minutes': 10},
                ]
            }

        return event

    @staticmethod
    def build_all_day_event(summary: str, date_start: str, date_end: str = None,
                           description: str = "", location: str = "") -> Dict[str, Any]:
        """
        Build an all-day event

        Args:
            summary (str): Event title
            date_start (str): Start date in YYYY-MM-DD format
            date_end (str): End date in YYYY-MM-DD format (optional)
            description (str): Event description
            location (str): Event location

        Returns:
            Dict[str, Any]: Google Calendar all-day event object
        """
        if date_end is None:
            date_end = date_start

        event = {
            'summary': summary,
            'start': {
                'date': date_start,
            },
            'end': {
                'date': date_end,
            },
            'description': description,
            'location': location,
        }

        return event

def setup_google_calendar_credentials():
    """
    Helper function to set up Google Calendar credentials
    This function provides instructions for setting up the credentials
    """
    instructions = """
    To set up Google Calendar integration:

    1. Go to the Google Cloud Console (https://console.cloud.google.com/)
    2. Create a new project or select an existing one
    3. Enable the Google Calendar API
    4. Create credentials (OAuth 2.0 client ID)
    5. Download the credentials file and save it as 'credentials.json'
    6. Make sure the redirect URI includes 'http://localhost' for local development

    The first time you run the application, it will open a browser window
    for you to authenticate and grant permissions.
    """

    print(instructions)
    return instructions
