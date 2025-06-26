"""
Text processing utilities for Russian language text
Handles cleaning, preprocessing, and sentence splitting
"""

import re
import spacy
import pymorphy3
from typing import List, Optional
import logging

logger = logging.getLogger(__name__)

class TextProcessor:
    """
    Russian text processor with cleaning and preprocessing capabilities
    """

    def __init__(self, language: str = 'ru'):
        self.language = language
        self.morph = pymorphy3.MorphAnalyzer()

        # Initialize spaCy models
        try:
            self.nlp_sent = spacy.load("ru_core_news_sm")
        except OSError:
            logger.warning("Russian spaCy model not found. Using blank model for sentence splitting.")
            self.nlp_sent = spacy.blank(language)
            # Add basic sentence segmentation
            self.nlp_sent.add_pipe("sentencizer")

    def clean_and_preprocess_text(self, text: str) -> str:
        """
        Clean and preprocess Russian text

        Args:
            text (str): Input text to clean

        Returns:
            str: Cleaned and preprocessed text
        """
        if not text or not isinstance(text, str):
            return ""

        # Basic cleaning
        text = re.sub(r'\n+', ' ', text)  # Replace newlines with spaces
        text = re.sub(r'\s+', ' ', text)  # Replace multiple spaces with single space
        text = text.strip()

        # Remove extra punctuation
        text = re.sub(r'[.]{2,}', '.', text)  # Multiple dots to single dot
        text = re.sub(r'[!]{2,}', '!', text)  # Multiple exclamations to single
        text = re.sub(r'[?]{2,}', '?', text)  # Multiple questions to single

        return text

    def split_into_sentences(self, text: str) -> List[str]:
        """
        Split text into sentences using spaCy

        Args:
            text (str): Input text to split

        Returns:
            List[str]: List of sentences
        """
        if not text:
            return []

        try:
            doc = self.nlp_sent(text)
            sentences = [sent.text.strip() for sent in doc.sents if sent.text.strip()]
            return sentences
        except Exception as e:
            logger.error(f"Error splitting sentences: {e}")
            # Fallback to simple splitting
            return [s.strip() for s in re.split(r'[.!?]', text) if s.strip()]

    def lemmatize(self, word: str) -> str:
        """
        Lemmatize a Russian word using pymorphy3

        Args:
            word (str): Word to lemmatize

        Returns:
            str: Lemmatized form of the word
        """
        if not word:
            return word

        try:
            parsed = self.morph.parse(word)
            if parsed:
                return parsed[0].normal_form
        except Exception as e:
            logger.error(f"Error lemmatizing word '{word}': {e}")

        return word

    def clean_entity_text(self, text: str, label: str) -> str:
        """
        Clean extracted entity text based on its label

        Args:
            text (str): Entity text to clean
            label (str): Entity label (e.g., 'PERSON', 'TIME', 'DATE')

        Returns:
            str: Cleaned entity text
        """
        if not text:
            return text

        text = text.strip()

        # Specific cleaning based on entity type
        if label == 'PERSON':
            # Remove common prefixes/suffixes for person names
            text = re.sub(r'^(с|со)\s+', '', text, flags=re.IGNORECASE)
            text = text.title()  # Capitalize names

        elif label in ['TIME', 'DATE']:
            # Clean time/date entities
            text = re.sub(r'\s+', ' ', text)

        elif label == 'EVENT':
            # Clean event names
            text = re.sub(r'^(на|в|о|про)\s+', '', text, flags=re.IGNORECASE)

        return text.strip()

    def remove_prepositions(self, text: str) -> str:
        """
        Remove prepositions from text using spaCy.

        Args:
            text (str): Input text.

        Returns:
            str: Text without prepositions.
        """
        if not text:
            return ""
        
        try:
            doc = self.nlp_sent(text)
            # Reconstruct the text, keeping tokens that are not prepositions (ADP - Adposition)
            # token.text_with_ws preserves the trailing whitespace.
            tokens_without_prepositions = [token.text_with_ws for token in doc if token.pos_ != 'ADP']
            
            return "".join(tokens_without_prepositions)
        except Exception as e:
            logger.error(f"Error removing prepositions: {e}")
            return text

    def preprocess_for_classification(self, text: str) -> str:
        """
        Preprocess text specifically for intent classification

        Args:
            text (str): Input text

        Returns:
            str: Preprocessed text ready for classification
        """
        text = self.clean_and_preprocess_text(text)

        # Convert to lowercase for classification
        text = text.lower()

        # Remove punctuation for classification
        text = re.sub(r'[^\w\s]', ' ', text)
        text = re.sub(r'\s+', ' ', text).strip()

        return text
