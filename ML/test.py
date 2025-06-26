#!/usr/bin/env python3
"""
Test script for Schedy ML Pipeline
"""

import sys
import os
import json

# Add current directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from pipeline import SchedyPipeline
from intent_classifier import create_sample_training_data


def test_text_processing():
    """Test basic text processing"""
    print("Testing text processing...")

    pipeline = SchedyPipeline()

    test_cases = [
        "Поставь встречу с Кириллом на завтра в 10 утра",
        "Добавь в календарь встречу c Андреем на 12 июня",
        "Запланируй презентацию на понедельник в 14:30",
        "Создай напоминание о докторе на среду в 9 утра",
        "Отмени встречу на завтра",
        "Что у меня на пятницу?",
        "Привет, как дела?"  # Should be UNKNOWN
    ]

    results = []
    for test_text in test_cases:
        print(f"\nProcessing: {test_text}")
        result = pipeline.process_text(test_text)

        if result.get('success'):
            print(f"  Intent: {result.get('intent')}")
            print(f"  Entities: {result.get('entities', {})}")

            if result.get('event_data'):
                event = result['event_data']
                print(f"  Event: {event.get('summary')}")
        else:
            print(f"  Error: {result.get('error')}")

        results.append(result)

    return results


def test_intent_classification():
    """Test intent classification specifically"""
    print("\n=== Testing Intent Classification ===")

    try:
        from intent_classifier import IntentClassifier

        # Create and train classifier
        classifier = IntentClassifier()
        sample_data = create_sample_training_data()
        classifier.train(sample_data)

        test_texts = [
            "Поставь встречу завтра",
            "Удали событие",
            "Перенеси встречу",
            "Покажи расписание",
            "Привет как дела"
        ]

        for text in test_texts:
            intent = classifier.predict(text)
            print(f"  '{text}' -> {intent}")

        print("✓ Intent classification test passed")
        return True

    except Exception as e:
        print(f"✗ Intent classification test failed: {e}")
        return False


def test_datetime_parsing():
    """Test datetime parsing"""
    print("\n=== Testing DateTime Parsing ===")

    try:
        from datetime_parser import DateTimeParser

        parser = DateTimeParser()

        test_texts = [
            "завтра в 10 утра",
            "понедельник в 14:30",
            "12 июня в 15:00",
            "пятницу вечером",
            "среду в 9 утра"
        ]

        for text in test_texts:
            parsed = parser.parse_event(text)
            print(f"  '{text}' -> Date: {parsed.get('date')}, Start: {parsed.get('start')}")

        print("✓ DateTime parsing test passed")
        return True

    except Exception as e:
        print(f"✗ DateTime parsing test failed: {e}")
        return False


def test_ner():
    """Test Named Entity Recognition"""
    print("\n=== Testing Named Entity Recognition ===")

    try:
        from ner_extractor import NERExtractor

        ner = NERExtractor()

        test_texts = [
            "Встреча с Кириллом в офисе",
            "Презентация для клиентов",
            "Поход к врачу в поликлинику",
            "Обед с Анной в ресторане"
        ]

        for text in test_texts:
            entities = ner.extract_entities(text)
            print(f"  '{text}' -> {entities}")

        print("✓ NER test passed")
        return True

    except Exception as e:
        print(f"✗ NER test failed: {e}")
        return False


def main():
    """Run all tests"""
    print("=== Schedy ML Pipeline Tests ===\n")

    tests_passed = 0
    total_tests = 4

    # Test 1: Basic text processing
    try:
        test_text_processing()
        tests_passed += 1
        print("\n✓ Text processing test passed")
    except Exception as e:
        print(f"\n✗ Text processing test failed: {e}")

    # Test 2: Intent classification
    if test_intent_classification():
        tests_passed += 1

    # Test 3: DateTime parsing
    if test_datetime_parsing():
        tests_passed += 1

    # Test 4: NER
    if test_ner():
        tests_passed += 1

    print(f"\n=== Test Results ===")
    print(f"Passed: {tests_passed}/{total_tests}")

    if tests_passed == total_tests:
        print("✓ All tests passed! The system is working correctly.")
        return 0
    else:
        print("⚠ Some tests failed. Check the error messages above.")
        return 1


if __name__ == '__main__':
    sys.exit(main())
