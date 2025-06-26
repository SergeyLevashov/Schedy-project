"""
Main ML Pipeline for Schedy
Processes Russian text and creates calendar events
"""

import os
import json
import logging
import re
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any

from config import (
    MODEL_CONFIG, TEXT_PROCESSING_CONFIG, GOOGLE_CALENDAR_CONFIG, 
    DEFAULT_EVENT_TEMPLATE
)
from text_processor import TextProcessor
from intent_classifier import IntentClassifier
from datetime_parser import DateTimeParser
from ner_extractor import NERExtractor
from calendar_client import GoogleCalendarClient, EventBuilder

logger = logging.getLogger(__name__)

class SchedyPipeline:
    """
    Main pipeline for processing text and creating calendar events
    """

    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}

        # Initialize components
        self.text_processor = TextProcessor(
            language=TEXT_PROCESSING_CONFIG['language']
        )

        self.intent_classifier = IntentClassifier()
        self.datetime_parser = DateTimeParser(
            timezone=TEXT_PROCESSING_CONFIG['timezone']
        )
        self.ner_extractor = NERExtractor(
            model_path=MODEL_CONFIG['ner_model']['model_path'],
            language=MODEL_CONFIG['ner_model']['language']
        )

        # Initialize Google Calendar client (optional)
        self.calendar_client = None
        self._init_calendar_client()

        # Load trained models if available
        self._load_models()

    def _init_calendar_client(self):
        """Initialize Google Calendar client if credentials are available"""
        try:
            if os.path.exists(GOOGLE_CALENDAR_CONFIG['credentials_file']):
                self.calendar_client = GoogleCalendarClient(
                    credentials_file=GOOGLE_CALENDAR_CONFIG['credentials_file'],
                    token_file=GOOGLE_CALENDAR_CONFIG['token_file'],
                    scopes=GOOGLE_CALENDAR_CONFIG['scopes']
                )
                logger.info("Google Calendar client initialized")
            else:
                logger.warning(
                    f"Google Calendar credentials not found at "
                    f"{GOOGLE_CALENDAR_CONFIG['credentials_file']}. "
                    f"Calendar integration will be disabled."
                )
        except Exception as e:
            logger.error(f"Error initializing Google Calendar client: {e}")

    def _load_models(self):
        """Load trained models if available"""
        # Load intent classifier
        intent_model_path = MODEL_CONFIG['intent_classifier']['model_path']
        if os.path.exists(intent_model_path):
            try:
                self.intent_classifier = IntentClassifier.load(intent_model_path)
                logger.info("Loaded intent classifier model")
            except Exception as e:
                logger.error(f"Error loading intent classifier: {e}")
        else:
            logger.warning("Intent classifier model not found. Using rule-based classification.")

    def process_text(self, text: str) -> Dict[str, Any]:
        """
        Process input text and extract event information

        Args:
            text (str): Input text in Russian

        Returns:
            Dict[str, Any]: Processed event information
        """
        if not text or len(text.strip()) == 0:
            return {'error': 'Empty input text'}

        # Limit text length
        max_length = TEXT_PROCESSING_CONFIG.get('max_text_length', 1000)
        if len(text) > max_length:
            text = text[:max_length]
            logger.warning(f"Input text truncated to {max_length} characters")

        try:
            # Step 1: Clean and preprocess text
            cleaned_text = self.text_processor.clean_and_preprocess_text(text)
            logger.info(f"Processing text: {cleaned_text}")

            # Step 2: Parse date/time information FIRST
            # This can help clean the text for the NER model
            datetime_info = self.datetime_parser.parse_event(cleaned_text)
            logger.info(f"Parsed datetime: {datetime_info}")

            # Step 3: Classify intent
            # Intent classification needs lowercased and cleaned text
            text_for_classification = self.text_processor.preprocess_for_classification(cleaned_text)
            intent = self.intent_classifier.predict(text_for_classification)
            logger.info(f"Detected intent: {intent}")

            # Step 4: Extract entities from the original cleaned text.
            # Do not remove parts of the text, as it confuses the model.
            entities = self.ner_extractor.extract_entities(cleaned_text)
            logger.info(f"Raw extracted entities: {entities}")

            # Step 4.5: Post-process entities for normalization (lemmatize and capitalize)
            processed_entities = self._postprocess_entities(entities)
            logger.info(f"Processed entities: {processed_entities}")

            # Step 5: Build event data
            event_data = self._build_event_data(
                intent, processed_entities, datetime_info, cleaned_text
            )

            return {
                'original_text': text,
                'cleaned_text': cleaned_text,
                'intent': intent,
                'entities': entities,
                'processed_entities': processed_entities,
                'datetime_info': datetime_info,
                'event_data': event_data,
                'success': True
            }

        except Exception as e:
            logger.error(f"Error processing text: {e}")
            return {
                'original_text': text,
                'error': str(e),
                'success': False
            }

    def _build_event_data(self, intent: str, entities: Dict[str, str], 
                         datetime_info: Dict[str, Any], text: str) -> Optional[Dict[str, Any]]:
        """
        Build Google Calendar event data from extracted information

        Args:
            intent (str): Detected intent
            entities (Dict[str, str]): Extracted entities
            datetime_info (Dict[str, Any]): Parsed datetime information
            text (str): Original text

        Returns:
            Optional[Dict[str, Any]]: Google Calendar event data
        """
        if intent != 'ADD_EVENT':
            return None

        try:
            # Start with default template
            event_data = DEFAULT_EVENT_TEMPLATE.copy()

            # Set event summary
            if 'EVENT_NAME' in entities:
                event_data['summary'] = entities['EVENT_NAME']
            elif 'EVENT' in entities:
                event_data['summary'] = entities['EVENT']
            elif 'PERSON' in entities:
                event_data['summary'] = f"Встреча с {entities['PERSON']}"
            else:
                event_data['summary'] = "Новое событие"

            # Set description
            event_data['description'] = f"Создано из текста: {text}"

            # Set location
            if 'LOCATION' in entities:
                event_data['location'] = entities['LOCATION']

            # Set attendees
            if 'PERSON' in entities:
                # Note: This would need email mapping in a real system
                event_data['attendees'] = []

            # Set date/time
            if datetime_info.get('start') and datetime_info.get('end'):
                event_data['start'] = {
                    'dateTime': datetime_info['start'].isoformat(),
                    'timeZone': TEXT_PROCESSING_CONFIG['timezone']
                }
                event_data['end'] = {
                    'dateTime': datetime_info['end'].isoformat(),
                    'timeZone': TEXT_PROCESSING_CONFIG['timezone']
                }
            elif datetime_info.get('date'):
                # All day event
                date_str = datetime_info['date'].isoformat()
                event_data['start'] = {'date': date_str}
                event_data['end'] = {'date': date_str}
            else:
                # Default to tomorrow at 10:00
                tomorrow = datetime.now() + timedelta(days=1)
                start_time = tomorrow.replace(hour=10, minute=0, second=0, microsecond=0)
                end_time = start_time + timedelta(hours=1)

                event_data['start'] = {
                    'dateTime': start_time.isoformat(),
                    'timeZone': TEXT_PROCESSING_CONFIG['timezone']
                }
                event_data['end'] = {
                    'dateTime': end_time.isoformat(),
                    'timeZone': TEXT_PROCESSING_CONFIG['timezone']
                }

            return event_data

        except Exception as e:
            logger.error(f"Error building event data: {e}")
            return None

    def _postprocess_entities(self, entities: Dict[str, str]) -> Dict[str, str]:
        """
        Lemmatize and capitalize extracted entities for correct representation.
        """
        processed_entities = {}
        for label, text in entities.items():
            # Lemmatize each word in the entity text to get its base form
            words = text.split()
            lemmatized_words = [self.text_processor.lemmatize(word) for word in words]
            
            # Capitalize appropriately
            if label in ['PERSON', 'LOCATION']:
                # For people and places, capitalize each word.
                processed_text = ' '.join(word.capitalize() for word in lemmatized_words)
            elif label in ['EVENT_NAME', 'EVENT']:
                # For event titles, capitalize the first word of the phrase.
                processed_text = ' '.join(lemmatized_words).capitalize()
            else:
                processed_text = ' '.join(lemmatized_words)
            
            processed_entities[label] = processed_text
        return processed_entities

    def create_calendar_event(self, event_data: Dict[str, Any]) -> Optional[str]:
        """
        Create event in Google Calendar

        Args:
            event_data (Dict[str, Any]): Event data

        Returns:
            Optional[str]: Event ID if successful
        """
        if not self.calendar_client:
            logger.error("Google Calendar client not initialized")
            return None

        try:
            event_id = self.calendar_client.create_event(
                event_data, 
                calendar_id=GOOGLE_CALENDAR_CONFIG['calendar_id']
            )
            return event_id
        except Exception as e:
            logger.error(f"Error creating calendar event: {e}")
            return None

    def process_and_create_event(self, text: str) -> Dict[str, Any]:
        """
        Process text and create calendar event in one step

        Args:
            text (str): Input text

        Returns:
            Dict[str, Any]: Processing result with event creation status
        """
        # Process text
        result = self.process_text(text)

        if not result.get('success'):
            return result

        # Create calendar event if intent is ADD_EVENT
        if result.get('intent') == 'ADD_EVENT' and result.get('event_data'):
            event_id = self.create_calendar_event(result['event_data'])
            result['event_id'] = event_id
            result['calendar_created'] = event_id is not None
        else:
            result['calendar_created'] = False

        return result

    def check_time_requirement(self, parsed_data: Dict[str, Any]) -> str:
        """
        Check if required time information is present

        Args:
            parsed_data (Dict[str, Any]): Parsed event data

        Returns:
            str: Error message if time is missing, empty string otherwise
        """
        datetime_info = parsed_data.get('datetime_info', {})

        if not datetime_info.get('start') and not datetime_info.get('date'):
            return "Пожалуйста, укажите время или дату события."

        return ""

    def get_upcoming_events(self, days: int = 7) -> List[Dict[str, Any]]:
        """
        Get upcoming events from Google Calendar

        Args:
            days (int): Number of days to look ahead

        Returns:
            List[Dict[str, Any]]: List of upcoming events
        """
        if not self.calendar_client:
            logger.error("Google Calendar client not initialized")
            return []

        try:
            time_min = datetime.now()
            time_max = time_min + timedelta(days=days)

            events = self.calendar_client.get_events(
                calendar_id=GOOGLE_CALENDAR_CONFIG['calendar_id'],
                time_min=time_min,
                time_max=time_max,
                max_results=50
            )

            return events
        except Exception as e:
            logger.error(f"Error getting upcoming events: {e}")
            return []

    def train_models(self, training_data_path: str):
        """
        Train the ML models with new data

        Args:
            training_data_path (str): Path to training data
        """
        try:
            # This would implement model training
            logger.info(f"Training models with data from {training_data_path}")
            # Implementation would depend on data format and requirements
            pass
        except Exception as e:
            logger.error(f"Error training models: {e}")
            raise

def check_time_requirement(parsed: Dict[str, Any]) -> str:
    """
    Standalone function to check time requirements
    """
    if not parsed.get('datetime_info', {}).get('start'):
        return "Пожалуйста, укажите время начала события."
    return ""

def update_event_time_fields(event_data: Dict[str, Any], parsed: Dict[str, Any]) -> Dict[str, Any]:
    """
    Update event time fields from parsed data
    """
    datetime_info = parsed.get('datetime_info', {})

    if datetime_info.get('start') and datetime_info.get('end'):
        event_data.update({
            'start': {
                'dateTime': datetime_info['start'].isoformat(),
                'timeZone': event_data.get('start', {}).get('timeZone', 'Europe/Moscow')
            },
            'end': {
                'dateTime': datetime_info['end'].isoformat(),
                'timeZone': event_data.get('end', {}).get('timeZone', 'Europe/Moscow')
            }
        })

    return event_data
