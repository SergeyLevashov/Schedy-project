"""
Configuration settings for the Schedy ML Pipeline
"""

import os
from pathlib import Path
from typing import Dict, Any

BASE_DIR = Path(__file__).parent
MODELS_DIR = BASE_DIR / "models"

NER_MODEL_PATH = MODELS_DIR / "NER" / "best_model"
INTENT_MODEL_PATH = MODELS_DIR / "intent" / "intent_classifier.joblib"

MODEL_CONFIG = {
    'intent_classifier': {
        'model_path': INTENT_MODEL_PATH,
        'classes': ["ADD_EVENT", "DELETE_EVENT", "MOVE_EVENT", "CHECK_EVENTS", "UNKNOWN"]
    },
    'ner_model': {
        'model_path': NER_MODEL_PATH,
        'language': 'ru'
    }
}

# Text Processing Configuration
TEXT_PROCESSING_CONFIG = {
    'language': 'ru',
    'timezone': 'Asia/Yekaterinburg',
    'max_text_length': 1000
}

# Google Calendar Configuration
GOOGLE_CALENDAR_CONFIG = {
    'credentials_file': os.getenv('GOOGLE_CREDENTIALS_FILE', 'config/credentials.json'),
    'token_file': os.getenv('GOOGLE_TOKEN_FILE', 'config/token.json'),
    'scopes': ['https://www.googleapis.com/auth/calendar'],
    'calendar_id': os.getenv('GOOGLE_CALENDAR_ID', 'primary')
}

# Default event template
DEFAULT_EVENT_TEMPLATE = {
    "summary": "Новое событие",
    "start": {"timeZone": "Europe/Moscow"},
    "end": {"timeZone": "Europe/Moscow"},
    "description": "",
    "location": "",
    "colorId": "5",
    "attendees": [],
    "reminders": {
        "useDefault": False,
        "overrides": [
            {"method": "popup", "minutes": 10}
        ]
    }
}

# Logging Configuration
LOGGING_CONFIG = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'standard': {
            'format': '%(asctime)s [%(levelname)s] %(name)s: %(message)s'
        },
    },
    'handlers': {
        'default': {
            'level': 'INFO',
            'formatter': 'standard',
            'class': 'logging.StreamHandler',
        },
    },
    'loggers': {
        '': {
            'handlers': ['default'],
            'level': 'INFO',
            'propagate': False
        }
    }
}
