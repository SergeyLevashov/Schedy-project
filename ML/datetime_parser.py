"""
Date and Time Parsing Module
Handles parsing of Russian date/time expressions for calendar events
"""

import re
import pymorphy3
import dateparser
from datetime import datetime, date, timedelta, time
from typing import Optional, Tuple, Dict, Any
import logging

logger = logging.getLogger(__name__)

class DateTimeParser:
    """
    Parse Russian date and time expressions
    """

    def __init__(self, timezone: str = 'Europe/Moscow'):
        self.timezone = timezone
        self.morph = pymorphy3.MorphAnalyzer()

        # Define Russian weekdays
        self.weekdays = {
            'понедельник': 0, 'пн': 0,
            'вторник': 1, 'вт': 1,
            'среда': 2, 'ср': 2, 'среду': 2,
            'четверг': 3, 'чт': 3,
            'пятница': 4, 'пт': 4, 'пятницу': 4,
            'суббота': 5, 'сб': 5, 'субботу': 5,
            'воскресение': 6, 'воскресенье': 6, 'вс': 6
        }

        # Define Russian months
        self.months = {
            'январь': 1, 'января': 1, 'янв': 1,
            'февраль': 2, 'февраля': 2, 'фев': 2,
            'март': 3, 'марта': 3, 'мар': 3,
            'апрель': 4, 'апреля': 4, 'апр': 4,
            'май': 5, 'мая': 5,
            'июнь': 6, 'июня': 6, 'июн': 6,
            'июль': 7, 'июля': 7, 'июл': 7,
            'август': 8, 'августа': 8, 'авг': 8,
            'сентябрь': 9, 'сентября': 9, 'сен': 9,
            'октябрь': 10, 'октября': 10, 'окт': 10,
            'ноябрь': 11, 'ноября': 11, 'ноя': 11,
            'декабрь': 12, 'декабря': 12, 'дек': 12
        }

        # Time patterns
        self.time_patterns = [
            r'(\d{1,2}):(\d{2})',  # HH:MM
            r'(\d{1,2})\s*ч(?:ас(?:а|ов)?)?\s*(\d{2})?',  # X час(а/ов) MM
            r'(\d{1,2})\s*утра',  # X утра
            r'(\d{1,2})\s*дня',   # X дня
            r'(\d{1,2})\s*вечера', # X вечера
        ]

    def parse_date(self, text: str) -> Optional[date]:
        """
        Parse date from Russian text

        Args:
            text (str): Input text containing date

        Returns:
            Optional[date]: Parsed date or None
        """
        if not text:
            return None

        text_lower = text.lower()
        today = date.today()

        try:
            # Handle relative dates
            if re.search(r'\bзавтра\b', text_lower):
                return today + timedelta(days=1)

            if re.search(r'\bсегодня\b', text_lower):
                return today

            if re.search(r'\bпослезавтра\b', text_lower):
                return today + timedelta(days=2)

            if re.search(r'\bвчера\b', text_lower):
                return today - timedelta(days=1)

            # Handle weekdays
            for weekday_name, weekday_num in self.weekdays.items():
                if weekday_name in text_lower:
                    days_ahead = weekday_num - today.weekday()
                    if days_ahead <= 0:  # Target day already happened this week
                        days_ahead += 7
                    return today + timedelta(days=days_ahead)

            # Handle specific dates with months
            # Pattern: DD месяц or месяц DD
            month_pattern = r'(\d{1,2})\s+(' + '|'.join(self.months.keys()) + r')'
            match = re.search(month_pattern, text_lower)
            if match:
                day = int(match.group(1))
                month_name = match.group(2)
                month = self.months[month_name]
                year = today.year

                # If the date has passed this year, assume next year
                try:
                    parsed_date = date(year, month, day)
                    if parsed_date < today:
                        parsed_date = date(year + 1, month, day)
                    return parsed_date
                except ValueError:
                    pass

            # Try dateparser as fallback
            parsed = dateparser.parse(text, languages=['ru'])
            if parsed:
                return parsed.date()

        except Exception as e:
            logger.error(f"Error parsing date from '{text}': {e}")

        return None

    def parse_time(self, text: str) -> Optional[time]:
        """
        Parse time from Russian text

        Args:
            text (str): Input text containing time

        Returns:
            Optional[time]: Parsed time or None
        """
        if not text:
            return None

        text_lower = text.lower()

        try:
            # Try different time patterns
            for pattern in self.time_patterns:
                match = re.search(pattern, text_lower)
                if match:
                    if pattern == r'(\d{1,2}):(\d{2})':  # HH:MM format
                        hour = int(match.group(1))
                        minute = int(match.group(2))
                        return time(hour, minute)

                    elif pattern == r'(\d{1,2})\s*ч(?:ас(?:а|ов)?)?\s*(\d{2})?':  # X час MM
                        hour = int(match.group(1))
                        minute = int(match.group(2)) if match.group(2) else 0
                        return time(hour, minute)

                    elif 'утра' in pattern:  # X утра
                        hour = int(match.group(1))
                        if hour == 12:
                            hour = 0
                        return time(hour, 0)

                    elif 'дня' in pattern:  # X дня
                        hour = int(match.group(1))
                        if hour < 12:
                            hour += 12
                        return time(hour, 0)

                    elif 'вечера' in pattern:  # X вечера
                        hour = int(match.group(1))
                        if hour < 12:
                            hour += 12
                        return time(hour, 0)

            # Handle special time expressions
            if 'утром' in text_lower or 'утра' in text_lower:
                return time(9, 0)  # Default morning time
            elif 'днем' in text_lower or 'дня' in text_lower:
                return time(14, 0)  # Default afternoon time
            elif 'вечером' in text_lower or 'вечера' in text_lower:
                return time(18, 0)  # Default evening time
            elif 'ночью' in text_lower or 'ночи' in text_lower:
                return time(22, 0)  # Default night time

        except Exception as e:
            logger.error(f"Error parsing time from '{text}': {e}")

        return None

    def parse_time_range(self, text: str, date_context: date) -> Tuple[Optional[datetime], Optional[datetime]]:
        """
        Parse time range from text

        Args:
            text (str): Input text
            date_context (date): Date context for the time

        Returns:
            Tuple[Optional[datetime], Optional[datetime]]: Start and end datetime
        """
        if not text or not date_context:
            return None, None

        text_lower = text.lower()

        try:
            # Look for time range patterns like "с 10 до 12" or "10-12"
            range_patterns = [
                r'с\s+(\d{1,2}(?::\d{2})?)\s+до\s+(\d{1,2}(?::\d{2})?)',
                r'(\d{1,2}(?::\d{2})?)\s*-\s*(\d{1,2}(?::\d{2})?)',
                r'с\s+(\d{1,2})\s+до\s+(\d{1,2})'
            ]

            for pattern in range_patterns:
                match = re.search(pattern, text_lower)
                if match:
                    start_time_str = match.group(1)
                    end_time_str = match.group(2)

                    # Parse start time
                    start_time = self.parse_time(start_time_str)
                    if start_time:
                        start_dt = datetime.combine(date_context, start_time)
                    else:
                        continue

                    # Parse end time
                    end_time = self.parse_time(end_time_str)
                    if end_time:
                        end_dt = datetime.combine(date_context, end_time)

                        # If end time is before start time, assume next day
                        if end_dt <= start_dt:
                            end_dt = datetime.combine(date_context + timedelta(days=1), end_time)
                    else:
                        # Default 1 hour duration
                        end_dt = start_dt + timedelta(hours=1)

                    return start_dt, end_dt

            # If no range found, parse single time and add default duration
            single_time = self.parse_time(text)
            if single_time:
                start_dt = datetime.combine(date_context, single_time)
                end_dt = start_dt + timedelta(hours=1)  # Default 1 hour duration
                return start_dt, end_dt

        except Exception as e:
            logger.error(f"Error parsing time range from '{text}': {e}")

        return None, None

    def parse_recurrence(self, text: str) -> Optional[str]:
        """
        Parse recurrence pattern from text

        Args:
            text (str): Input text

        Returns:
            Optional[str]: Recurrence rule or None
        """
        if not text:
            return None

        text_lower = text.lower()

        # Simple recurrence patterns
        if any(word in text_lower for word in ['каждый день', 'ежедневно']):
            return 'RRULE:FREQ=DAILY'
        elif any(word in text_lower for word in ['каждую неделю', 'еженедельно']):
            return 'RRULE:FREQ=WEEKLY'
        elif any(word in text_lower for word in ['каждый месяц', 'ежемесячно']):
            return 'RRULE:FREQ=MONTHLY'
        elif any(word in text_lower for word in ['каждый год', 'ежегодно']):
            return 'RRULE:FREQ=YEARLY'

        return None

    def parse_event(self, text: str) -> Dict[str, Any]:
        """
        Parse all event-related information from text

        Args:
            text (str): Input text

        Returns:
            Dict[str, Any]: Dictionary with parsed info including 'start', 'end', 'summary', 'matched_text'
        """
        result = {
            'date': None,
            'start': None,
            'end': None,
            'recurrence': None,
            'matched_text': []
        }
        text_lower = text.lower()

        try:
            # We will find all matches and then remove them from the text
            # to avoid re-parsing
            all_matches = []

            # 1. Parse date
            parsed_date = self.parse_date(text_lower)
            if parsed_date:
                result['date'] = parsed_date
                # This is tricky because parse_date doesn't return matched text
                # We will re-run some regexes to find the matched text
                date_keywords = [
                    r'\bзавтра\b', r'\bсегодня\b', r'\bпослезавтра\b', r'\bвчера\b'
                ] + list(self.weekdays.keys())
                
                for keyword in date_keywords:
                    match = re.search(r'\b' + keyword + r'\b', text_lower)
                    if match:
                        all_matches.append(match.group(0))

                month_pattern = r'(\d{1,2}\s+(' + '|'.join(self.months.keys()) + r'))'
                month_match = re.search(month_pattern, text_lower)
                if month_match:
                    all_matches.append(month_match.group(1))

            # 2. Parse time range
            if result['date']:
                start_dt, end_dt = self.parse_time_range(text_lower, result['date'])
                if start_dt and end_dt:
                    result['start'] = start_dt
                    result['end'] = end_dt
                    
                    # Again, find the matched text for time
                    range_patterns = [
                        r'с\s+\d{1,2}(?::\d{2})?\s+до\s+\d{1,2}(?::\d{2})?',
                        r'\d{1,2}(?::\d{2})?\s*-\s*\d{1,2}(?::\d{2})?',
                        r'\d{1,2}:\d{2}',
                        r'\d{1,2}\s*ч(?:ас(?:а|ов)?)?\s*(\d{2})?',
                        r'\d{1,2}\s*утра', r'\d{1,2}\s*дня', r'\d{1,2}\s*вечера'
                    ]
                    for pattern in range_patterns:
                        match = re.search(pattern, text_lower)
                        if match:
                            all_matches.append(match.group(0))

            # 3. Parse recurrence
            recurrence_rule = self.parse_recurrence(text_lower)
            if recurrence_rule:
                result['recurrence'] = recurrence_rule
                # Add matched recurrence text
                rec_keywords = [
                    r'каждый\s+день', r'каждую\s+неделю', r'каждый\s+месяц', r'каждый\s+год'
                ]
                for keyword in rec_keywords:
                    match = re.search(keyword, text_lower)
                    if match:
                        all_matches.append(match.group(0))
            
            # Store unique matched text snippets
            result['matched_text'] = list(set(all_matches))

            return result

        except Exception as e:
            logger.error(f"Error in parse_event for text '{text}': {e}")
            return result
