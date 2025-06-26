#!/usr/bin/env python3
"""
Schedy - Russian Text to Calendar Event ML Pipeline
Main application entry point
"""

import os
import sys
import json
import logging
import argparse
from datetime import datetime
from typing import List, Dict, Any

# Add current directory to path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from config import LOGGING_CONFIG
from pipeline import SchedyPipeline
from intent_classifier import IntentClassifier, create_sample_training_data
from ner_extractor import create_sample_ner_data
from calendar_client import setup_google_calendar_credentials

# Configure logging
logger = logging.getLogger(__name__)


class SchedyApp:
    """
    Main Schedy application class
    """

    def __init__(self):
        self.pipeline = None
        self._initialize_pipeline()

    def _initialize_pipeline(self):
        """Initialize the ML pipeline"""
        try:
            self.pipeline = SchedyPipeline()
            logger.info("Schedy pipeline initialized successfully")
        except Exception as e:
            logger.error(f"Error initializing pipeline: {e}")
            raise

    def process_text(self, text: str, create_event: bool = False) -> Dict[str, Any]:
        """
        Process input text

        Args:
            text (str): Input text to process
            create_event (bool): Whether to create calendar event

        Returns:
            Dict[str, Any]: Processing results
        """
        if not self.pipeline:
            raise RuntimeError("Pipeline not initialized")

        if create_event:
            return self.pipeline.process_and_create_event(text)
        else:
            return self.pipeline.process_text(text)

    def process_file(self, file_path: str, create_events: bool = False) -> List[Dict[str, Any]]:
        """
        Process text from file

        Args:
            file_path (str): Path to text file
            create_events (bool): Whether to create calendar events

        Returns:
            List[Dict[str, Any]]: Processing results for each line
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")

        results = []
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                for line_num, line in enumerate(f, 1):
                    line = line.strip()
                    if not line:
                        continue

                    logger.info(f"Processing line {line_num}: {line}")
                    result = self.process_text(line, create_events)
                    result['line_number'] = line_num
                    results.append(result)

        except Exception as e:
            logger.error(f"Error processing file {file_path}: {e}")
            raise

        return results

    def train_intent_classifier(self, data_path: str = None):
        """
        Train the intent classifier

        Args:
            data_path (str): Path to training data CSV file
        """
        try:
            if data_path and os.path.exists(data_path):
                import pandas as pd
                df = pd.read_csv(data_path)
                logger.info(f"Training intent classifier with data from {data_path}")
            else:
                logger.info("Using sample training data for intent classifier")
                df = create_sample_training_data()

            # Train the classifier
            classifier = IntentClassifier()
            classifier.train(df)

            # Save the model
            os.makedirs('models', exist_ok=True)
            classifier.save('models/intent_classifier.joblib')

            logger.info("Intent classifier training completed and model saved")

        except Exception as e:
            logger.error(f"Error training intent classifier: {e}")
            raise

    def get_upcoming_events(self, days: int = 7) -> List[Dict[str, Any]]:
        """
        Get upcoming calendar events

        Args:
            days (int): Number of days to look ahead

        Returns:
            List[Dict[str, Any]]: Upcoming events
        """
        if not self.pipeline:
            raise RuntimeError("Pipeline not initialized")

        return self.pipeline.get_upcoming_events(days)

    def setup_calendar(self):
        """Setup Google Calendar credentials"""
        setup_google_calendar_credentials()


def main():
    """Main application entry point"""
    parser = argparse.ArgumentParser(
        description='Schedy - Russian Text to Calendar Event ML Pipeline'
    )

    subparsers = parser.add_subparsers(dest='command', help='Available commands')

    # Process text command
    process_parser = subparsers.add_parser('process', help='Process text input')
    process_parser.add_argument('text', help='Text to process')
    process_parser.add_argument('--create-event', action='store_true',
                                help='Create calendar event')
    process_parser.add_argument('--output', help='Output file for results (JSON)')

    # Process file command
    file_parser = subparsers.add_parser('process-file', help='Process file input')
    file_parser.add_argument('file', help='File to process')
    file_parser.add_argument('--create-events', action='store_true',
                             help='Create calendar events')
    file_parser.add_argument('--output', help='Output file for results (JSON)')

    # Train command
    train_parser = subparsers.add_parser('train', help='Train models')
    train_parser.add_argument('--data', help='Training data file (CSV)')

    # Events command
    events_parser = subparsers.add_parser('events', help='Get upcoming events')
    events_parser.add_argument('--days', type=int, default=7,
                               help='Number of days to look ahead (default: 7)')

    # Setup command
    setup_parser = subparsers.add_parser('setup', help='Setup Google Calendar')

    # Interactive command
    interactive_parser = subparsers.add_parser('interactive', help='Interactive mode')

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return

    try:
        app = SchedyApp()

        if args.command == 'process':
            result = app.process_text(args.text, args.create_event)

            if args.output:
                with open(args.output, 'w', encoding='utf-8') as f:
                    json.dump(result, f, ensure_ascii=False, indent=2, default=str)
                print(f"Results saved to {args.output}")
            else:
                print(json.dumps(result, ensure_ascii=False, indent=2, default=str))

        elif args.command == 'process-file':
            results = app.process_file(args.file, args.create_events)

            if args.output:
                with open(args.output, 'w', encoding='utf-8') as f:
                    json.dump(results, f, ensure_ascii=False, indent=2, default=str)
                print(f"Results saved to {args.output}")
            else:
                for result in results:
                    print(f"Line {result['line_number']}: {result}")

        elif args.command == 'train':
            app.train_intent_classifier(args.data)
            print("Training completed successfully")

        elif args.command == 'events':
            events = app.get_upcoming_events(args.days)
            if events:
                print(f"Upcoming events ({args.days} days):")
                for event in events:
                    start = event.get('start', {})
                    start_time = start.get('dateTime', start.get('date', 'Unknown'))
                    summary = event.get('summary', 'No title')
                    print(f"  - {start_time}: {summary}")
            else:
                print("No upcoming events found")

        elif args.command == 'setup':
            app.setup_calendar()

        elif args.command == 'interactive':
            interactive_mode(app)

    except Exception as e:
        logger.error(f"Application error: {e}")
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


def interactive_mode(app: SchedyApp):
    """
    Interactive mode for the application

    Args:
        app (SchedyApp): Application instance
    """
    print("\n=== Schedy Interactive Mode ===")
    print("Enter Russian text to create calendar events.")
    print("Commands: 'quit' to exit, 'events' to show upcoming events")
    print("Type 'help' for more commands\n")

    while True:
        try:
            user_input = input("schedy> ").strip()

            if not user_input:
                continue

            if user_input.lower() in ['quit', 'exit', 'q']:
                print("До свидания!")
                break

            elif user_input.lower() == 'help':
                print("""
Available commands:
  - Type any Russian text to process it
  - 'events' - Show upcoming calendar events
  - 'train' - Train models with sample data
  - 'quit' or 'exit' - Exit interactive mode
                """)
                continue

            elif user_input.lower() == 'events':
                events = app.get_upcoming_events()
                if events:
                    print("Upcoming events:")
                    for event in events[:10]:  # Show first 10
                        start = event.get('start', {})
                        start_time = start.get('dateTime', start.get('date', 'Unknown'))
                        summary = event.get('summary', 'No title')
                        print(f"  - {start_time}: {summary}")
                else:
                    print("No upcoming events found")
                continue

            elif user_input.lower() == 'train':
                print("Training intent classifier with sample data...")
                app.train_intent_classifier()
                print("Training completed!")
                continue

            # Process regular text input
            print(f"Processing: {user_input}")
            result = app.process_text(user_input, create_event=False)

            if result.get('success'):
                print(f"Intent: {result.get('intent')}")
                print(f"Entities: {result.get('entities', {})}")

                if result.get('event_data'):
                    print("Event data created:")
                    event_data = result['event_data']
                    print(f"  Title: {event_data.get('summary')}")
                    print(f"  Start: {event_data.get('start', {}).get('dateTime', 'TBD')}")
                    print(f"  End: {event_data.get('end', {}).get('dateTime', 'TBD')}")

                    create = input("Create this event in calendar? (y/n): ").lower()
                    if create in ['y', 'yes', 'да']:
                        event_result = app.process_text(user_input, create_event=True)
                        if event_result.get('calendar_created'):
                            print(f"✓ Event created with ID: {event_result.get('event_id')}")
                        else:
                            print("✗ Failed to create calendar event")
                else:
                    print("No event data generated (intent not ADD_EVENT)")
            else:
                print(f"Error processing text: {result.get('error')}")

            print()  # Empty line for readability

        except KeyboardInterrupt:
            print("\n\nExiting...")
            break
        except Exception as e:
            print(f"Error: {e}")


if __name__ == '__main__':
    main()
