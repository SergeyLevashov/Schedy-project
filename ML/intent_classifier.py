import os
import pickle
import pandas as pd
import logging
import joblib
from typing import List, Optional
from sklearn.pipeline import Pipeline
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.svm import LinearSVC
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, accuracy_score

from text_processor import TextProcessor

logger = logging.getLogger(__name__)


class IntentClassifier:
    """
    Intent classifier for calendar operations using TF-IDF and SVM
    """

    def __init__(self):
        self.pipeline = Pipeline([
            ('tfidf', TfidfVectorizer(
                max_features=5000,
                ngram_range=(1, 2),
                min_df=2,
                max_df=0.95
            )),
            ('clf', LinearSVC(random_state=42, max_iter=10000))
        ])
        self.classes = ["ADD_EVENT", "DELETE_EVENT", "MOVE_EVENT", "CHECK_EVENTS", "UNKNOWN"]
        self.text_processor = TextProcessor()
        self.is_trained = False

    def _map_template_to_intent(self, template: str) -> str:
        """
        Map template strings to intent labels

        Args:
            template (str): Template string

        Returns:
            str: Intent label
        """
        template_lower = template.lower()

        # Keywords for different intents
        add_keywords = ['добавь', 'создай', 'поставь', 'запланируй', 'занеси', 'назначь']
        delete_keywords = ['удали', 'отмени', 'убери', 'сотри']
        move_keywords = ['перенеси', 'измени', 'сдвинь', 'перепланируй']
        check_keywords = ['покажи', 'что у меня', 'расписание', 'планы', 'события']

        # Check for keywords
        for keyword in add_keywords:
            if keyword in template_lower:
                return "ADD_EVENT"

        for keyword in delete_keywords:
            if keyword in template_lower:
                return "DELETE_EVENT"

        for keyword in move_keywords:
            if keyword in template_lower:
                return "MOVE_EVENT"

        for keyword in check_keywords:
            if keyword in template_lower:
                return "CHECK_EVENTS"

        return "UNKNOWN"

    def train(self, df: pd.DataFrame, text_column: str = 'text', template_column: str = 'template'):
        """
        Train the intent classifier

        Args:
            df (pd.DataFrame): Training dataframe
            text_column (str): Name of the text column
            template_column (str): Name of the template column (optional)
        """
        try:
            # If template column exists, map templates to intents
            if template_column in df.columns:
                df['intent'] = df[template_column].apply(self._map_template_to_intent)
            elif 'intent' not in df.columns:
                # If no intent column, try to infer from text
                logger.warning("No intent or template column found. Inferring intents from text.")
                df['intent'] = df[text_column].apply(self._map_template_to_intent)

            # Preprocess text
            X = df[text_column].apply(self.text_processor.preprocess_for_classification)
            y = df['intent']

            # Filter out unknown intents for training
            mask = y != "UNKNOWN"
            X_filtered = X[mask]
            y_filtered = y[mask]

            if len(X_filtered) == 0:
                raise ValueError("No valid training examples found")

            # Train the model
            self.pipeline.fit(X_filtered, y_filtered)
            self.is_trained = True

            # Log training statistics
            logger.info(f"Trained intent classifier on {len(X_filtered)} examples")
            logger.info(f"Intent distribution: {y_filtered.value_counts().to_dict()}")

        except Exception as e:
            logger.error(f"Error training intent classifier: {e}")
            raise

    def predict(self, text: str) -> str:
        """
        Predict intent for given text

        Args:
            text (str): Input text

        Returns:
            str: Predicted intent
        """
        if not self.is_trained:
            logger.warning("Model not trained. Using rule-based classification.")
            return self._map_template_to_intent(text)

        try:
            # Preprocess text
            processed_text = self.text_processor.preprocess_for_classification(text)

            # Predict
            prediction = self.pipeline.predict([processed_text])[0]

            # Get prediction probability/confidence
            try:
                decision_scores = self.pipeline.decision_function([processed_text])[0]
                max_score = max(decision_scores)

                # If confidence is too low, return UNKNOWN
                if max_score < 0.5:
                    return "UNKNOWN"

            except Exception:
                pass  # Some classifiers don't support decision_function

            return prediction

        except Exception as e:
            logger.error(f"Error predicting intent: {e}")
            return "UNKNOWN"

    def evaluate(self, test_df: pd.DataFrame, text_column: str = 'text',
                 template_column: str = 'template') -> dict:
        """
        Evaluate the classifier on test data

        Args:
            test_df (pd.DataFrame): Test dataframe
            text_column (str): Name of the text column
            template_column (str): Name of the template column

        Returns:
            dict: Evaluation metrics
        """
        if not self.is_trained:
            raise ValueError("Model not trained")

        # Prepare test data
        if template_column in test_df.columns:
            test_df['intent'] = test_df[template_column].apply(self._map_template_to_intent)

        X_test = test_df[text_column].apply(self.text_processor.preprocess_for_classification)
        y_test = test_df['intent']

        # Predict
        y_pred = [self.predict(text) for text in test_df[text_column]]

        # Calculate metrics
        accuracy = accuracy_score(y_test, y_pred)
        report = classification_report(y_test, y_pred, output_dict=True)

        return {
            'accuracy': accuracy,
            'classification_report': report
        }

    def save(self, path: str):
        """
        Save the trained model

        Args:
            path (str): Path to save the model
        """
        if not self.is_trained:
            raise ValueError("Cannot save untrained model")

        try:
            os.makedirs(os.path.dirname(path), exist_ok=True)
            with open(path, 'wb') as f:
                pickle.dump({
                    'pipeline': self.pipeline,
                    'classes': self.classes,
                    'is_trained': self.is_trained
                }, f)
            logger.info(f"Model saved to {path}")
        except Exception as e:
            logger.error(f"Error saving model: {e}")
            raise

    @classmethod
    def load(cls, path: str) -> 'IntentClassifier':
        """
        Load a trained model

        Args:
            path (str): Path to the saved model

        Returns:
            IntentClassifier: Loaded classifier instance
        """
        try:
            classifier = cls()
            classifier.pipeline = joblib.load(path)

            print(f"Model loaded from {path}")
            return classifier

        except Exception as e:
            logger.error(f"Error loading model: {e}")
            raise


def create_sample_training_data() -> pd.DataFrame:
    """
    Create sample training data for intent classification

    Returns:
        pd.DataFrame: Sample training data
    """
    sample_data = [
        # ADD_EVENT examples
        ("Поставь мне встречу с Кириллом на завтра в 10", "ADD_EVENT"),
        ("Добавь в календарь встречу c Андреем на 12 июня", "ADD_EVENT"),
        ("Запланируй презентацию на понедельник в 14:30", "ADD_EVENT"),
        ("Создай напоминание о докторе на среду в 9 утра", "ADD_EVENT"),
        ("Давай занесем событие на пятницу вечером", "ADD_EVENT"),

        # DELETE_EVENT examples
        ("Отмени встречу на завтра", "DELETE_EVENT"),
        ("Удали событие в пятницу", "DELETE_EVENT"),
        ("Убери напоминание о докторе", "DELETE_EVENT"),

        # MOVE_EVENT examples
        ("Перенеси встречу на час позже", "MOVE_EVENT"),
        ("Измени время презентации на 15:00", "MOVE_EVENT"),
        ("Сдвинь событие на завтра", "MOVE_EVENT"),

        # CHECK_EVENTS examples
        ("Что у меня на завтра", "CHECK_EVENTS"),
        ("Покажи мое расписание на неделю", "CHECK_EVENTS"),
        ("Какие у меня планы на пятницу", "CHECK_EVENTS"),

        # UNKNOWN examples
        ("Привет как дела", "UNKNOWN"),
        ("Расскажи шутку", "UNKNOWN"),
        ("Какая погода", "UNKNOWN")
    ]

    return pd.DataFrame(sample_data, columns=['text', 'intent'])
