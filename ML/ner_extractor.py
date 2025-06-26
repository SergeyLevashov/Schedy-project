import os
import spacy
from spacy.training import Example
from spacy.tokens import DocBin
import logging
from typing import Dict, List, Any, Optional
import json

from text_processor import TextProcessor

logger = logging.getLogger(__name__)

class NERExtractor:
    """
    Named Entity Recognition extractor for Russian text
    """

    def __init__(self, model_path: Optional[str] = None, language: str = "ru"):
        self.language = language
        self.model_path = model_path
        self.text_processor = TextProcessor(language)

        # Entity labels
        self.entity_labels = ["PERSON", "TIME", "DATE", "EVENT", "LOCATION", "DURATION"]

        # Load or create model
        if model_path and os.path.exists(model_path):
            self.nlp = self.load_model(model_path)
        else:
            self.nlp = self.create_model()

    def create_model(self):
        """
        Create a new NER model

        Returns:
            spacy.Language: New spaCy model
        """
        try:
            nlp = spacy.blank(self.language)

            # Add tok2vec component
            if "tok2vec" not in nlp.pipe_names:
                tok2vec = nlp.add_pipe("tok2vec", first=True)
                tok2vec.model.initialize()

            # Add NER component
            if "ner" not in nlp.pipe_names:
                ner = nlp.add_pipe("ner", after="tok2vec")
            else:
                ner = nlp.get_pipe("ner")

            # Add labels
            for label in self.entity_labels:
                ner.add_label(label)

            logger.info("Created new NER model")
            return nlp

        except Exception as e:
            logger.error(f"Error creating NER model: {e}")
            raise

    def load_model(self, model_path: str):
        """
        Load existing NER model

        Args:
            model_path (str): Path to the model

        Returns:
            spacy.Language: Loaded spaCy model
        """
        try:
            nlp = spacy.load(model_path)
            logger.info(f"Loaded NER model from {model_path}")
            return nlp
        except Exception as e:
            logger.error(f"Error loading NER model from {model_path}: {e}")
            logger.info("Creating new model instead")
            return self.create_model()

    def extract_entities(self, text: str) -> Dict[str, str]:
        """
        Extract entities from text

        Args:
            text (str): Input text

        Returns:
            Dict[str, str]: Dictionary of extracted entities
        """
        if not text:
            return {}

        try:
            # Clean text
            cleaned_text = self.text_processor.clean_and_preprocess_text(text)

            # Process with NER model
            doc = self.nlp(cleaned_text)

            # Extract entities
            entities = {}
            for ent in doc.ents:
                label = ent.label_
                entity_text = self.text_processor.clean_entity_text(ent.text, label)

                # Store the first occurrence of each entity type
                if label not in entities and entity_text:
                    entities[label] = entity_text

            # Fallback entity extraction using patterns
            entities.update(self._extract_entities_with_patterns(cleaned_text))

            return entities

        except Exception as e:
            logger.error(f"Error extracting entities from '{text}': {e}")
            return self._extract_entities_with_patterns(text)

    def _extract_entities_with_patterns(self, text: str) -> Dict[str, str]:
        """
        Fallback entity extraction using regex patterns

        Args:
            text (str): Input text

        Returns:
            Dict[str, str]: Dictionary of extracted entities
        """
        import re

        entities = {}
        text_lower = text.lower()

        try:
            # Extract PERSON entities (names after prepositions)
            person_patterns = [
                r'(?:с|со|вместе с)\s+([А-ЯЁ][а-яё]+(?:\s+[А-ЯЁ][а-яё]+)?)',
                r'(?:встреча с|встреча с)\s+([А-ЯЁ][а-яё]+(?:\s+[А-ЯЁ][а-яё]+)?)',
                r'(?:к|ко)\s+([А-ЯЁ][а-яё]+(?:\s+[А-ЯЁ][а-яё]+)?)'
            ]

            for pattern in person_patterns:
                match = re.search(pattern, text)
                if match and 'PERSON' not in entities:
                    entities['PERSON'] = match.group(1).strip()
                    break

            # Extract EVENT entities
            event_patterns = [
                r'(?:встречу|событие|мероприятие|презентацию|собрание)\s+([^\s]+(?:\s+[^\s]+)*?)(?:\s+на|\s+в|$)',
                r'(?:запланируй|добавь|создай)\s+([^\s]+(?:\s+[^\s]+)*?)(?:\s+на|\s+в|$)'
            ]

            for pattern in event_patterns:
                match = re.search(pattern, text_lower)
                if match and 'EVENT' not in entities:
                    event_text = match.group(1).strip()
                    # Filter out common non-event words
                    if event_text not in ['встречу', 'событие', 'мероприятие', 'презентацию']:
                        entities['EVENT'] = event_text.title()
                        break

            # Extract LOCATION entities
            location_patterns = [
                r'(?:в|на)\s+(офисе|доме|работе|[А-ЯЁ][а-яё]+(?:\s+[А-ЯЁ][а-яё]+)*?)(?:\s|$)',
                r'(?:адрес|место|по адресу)\s+([^\n]+)'
            ]

            for pattern in location_patterns:
                match = re.search(pattern, text)
                if match and 'LOCATION' not in entities:
                    location = match.group(1).strip()
                    if len(location) > 1:  # Avoid single characters
                        entities['LOCATION'] = location
                        break

        except Exception as e:
            logger.error(f"Error in pattern-based entity extraction: {e}")

        return entities

    def train(self, training_data: List[Dict[str, Any]], epochs: int = 10):
        """
        Train the NER model

        Args:
            training_data (List[Dict]): Training data in spaCy format
            epochs (int): Number of training epochs
        """
        if not training_data:
            logger.warning("No training data provided")
            return

        try:
            # Prepare training examples
            examples = []
            for item in training_data:
                text = item['text']
                entities = item.get('entities', [])

                doc = self.nlp.make_doc(text)
                example = Example.from_dict(doc, {"entities": entities})
                examples.append(example)

            # Initialize the model
            self.nlp.initialize(lambda: examples)

            # Train the model
            for epoch in range(epochs):
                losses = {}
                self.nlp.update(examples, losses=losses)
                logger.info(f"Epoch {epoch + 1}/{epochs}, Losses: {losses}")

            logger.info("NER model training completed")

        except Exception as e:
            logger.error(f"Error training NER model: {e}")
            raise

    def save_model(self, path: str):
        """
        Save the trained model

        Args:
            path (str): Path to save the model
        """
        try:
            os.makedirs(path, exist_ok=True)
            self.nlp.to_disk(path)
            logger.info(f"NER model saved to {path}")
        except Exception as e:
            logger.error(f"Error saving NER model: {e}")
            raise

    def evaluate(self, test_data: List[Dict[str, Any]]) -> Dict[str, float]:
        """
        Evaluate the NER model

        Args:
            test_data (List[Dict]): Test data

        Returns:
            Dict[str, float]: Evaluation metrics
        """
        if not test_data:
            return {}

        try:
            examples = []
            for item in test_data:
                text = item['text']
                entities = item.get('entities', [])

                doc = self.nlp.make_doc(text)
                example = Example.from_dict(doc, {"entities": entities})
                examples.append(example)

            # Evaluate
            scores = self.nlp.evaluate(examples)

            return {
                'precision': scores.get('ents_p', 0.0),
                'recall': scores.get('ents_r', 0.0),
                'f1': scores.get('ents_f', 0.0)
            }

        except Exception as e:
            logger.error(f"Error evaluating NER model: {e}")
            return {}

def create_sample_ner_data() -> List[Dict[str, Any]]:
    """
    Create sample NER training data

    Returns:
        List[Dict]: Sample training data
    """
    sample_data = [
        {
            "text": "Поставь встречу с Кириллом на завтра в 10 утра",
            "entities": [
                (18, 26, "PERSON"),  # "Кириллом"
                (30, 36, "DATE"),    # "завтра"
                (39, 47, "TIME")     # "10 утра"
            ]
        },
        {
            "text": "Добавь презентацию на понедельник в 14:30",
            "entities": [
                (7, 18, "EVENT"),     # "презентацию"
                (22, 33, "DATE"),     # "понедельник"
                (36, 41, "TIME")      # "14:30"
            ]
        },
        {
            "text": "Создай напоминание о враче на среду в 9 утра в поликлинике",
            "entities": [
                (21, 26, "EVENT"),    # "враче"
                (30, 35, "DATE"),     # "среду"
                (38, 45, "TIME"),     # "9 утра"
                (48, 59, "LOCATION")  # "поликлинике"
            ]
        }
    ]

    return sample_data
