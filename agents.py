import os
import json
import datetime
from dotenv import load_dotenv

from autogen_agentchat.agents import AssistantAgent
from autogen_ext.models.openai import OpenAIChatCompletionClient
from autogen_ext.models.openai._model_info import ModelInfo

load_dotenv()


from instructions import (
    GUARDRAIL_PROMPT,
    SALES_PROMPT,
    FOLLOW_UP_PROMPT,
    DEMO_BOOKING_PROMPT,
    ATTACK_PROMPT,
    CLASSIFIER_PROMPT
)


# DATE_LINE = f"\nCURRENT DATE AND TIME: {datetime.datetime.now().strftime('%Y-%m-%d %I:%M %p')}\n"

# demo_booking_prompt = DEMO_BOOKING_PROMPT + DATE_LINE

client = OpenAIChatCompletionClient(
    model="llama-3.1-8b-instant",
    api_key=os.getenv("GROQ_API_KEY"),
    base_url="https://api.groq.com/openai/v1",
    model_info=ModelInfo(
        model_name="llama-3.1-8b-instant",
        provider="groq",
        family="llama",
        max_context_length=8192,
        function_calling=True,
        json_output=True,
        vision=False,
    ),
)

# client = OpenAIChatCompletionClient(
#     model="gpt-4o-mini",   
#     api_key=os.getenv("OPENAI_API_KEY"),
#     model_info=ModelInfo(
#         model_name="gpt-4o-mini",
#         provider="openai",
#         family="gpt",
#         max_context_length=16384,
#         function_calling=True,
#         json_output=True,
#         vision=False,
#     ),
# )

import datetime
import re
from typing import Optional, Dict, List
from loguru import logger

from autogen_core.tools import FunctionTool
import datetime

def _format_time_12h(time_value):
    """
    Convert a time or datetime object to a 12-hour formatted string.
    Example:
      14:00 -> "2:00 PM"
      10:00 -> "10:00 AM"
    """

    if isinstance(time_value, datetime.datetime):
        time_value = time_value.time()

    if isinstance(time_value, datetime.time):
        return time_value.strftime("%-I:%M %p") if hasattr(time_value, "strftime") else ""

    # Fallback for string inputs like "14:00"
    if isinstance(time_value, str):
        try:
            parsed_time = datetime.datetime.strptime(time_value.strip(), "%H:%M").time()
            return parsed_time.strftime("%-I:%M %p")
        except ValueError:
            pass

    return ""

def normalize_time(time_str: str) -> str:
    time_str = time_str.strip().lower()
    
    if ("am" in time_str or "pm" in time_str) and ":" in time_str:
        return datetime.datetime.strptime(
            time_str.replace(" ", ""),
            "%I:%M%p"
        ).strftime("%H:%M")
    
    if "am" in time_str or "pm" in time_str:
        return datetime.datetime.strptime(
            time_str.replace(" ", ""),
            "%I%p"
        ).strftime("%H:00")

    if ":" in time_str:
        h, m = map(int, time_str.split(":"))
        return f"{h:02d}:{m:02d}"

    # fallback: "2" → "02:00"
    return f"{int(time_str):02d}:00"

import datetime

import re

def parse_human_date(date_str: str) -> datetime.date:
    now = datetime.datetime.now()
    date_str = date_str.lower().strip()

    # 1. Handle "Today" and "Tomorrow"
    if date_str == "today":
        return now.date()
    if date_str == "tomorrow":
        return now.date() + datetime.timedelta(days=1)

    # 2. Check if the user already provided a 4-digit year (e.g., 2025, 2026)
    # This regex looks for 4 digits in a row
    has_year = bool(re.search(r'\b\d{4}\b', date_str))

    # 3. Only append the current year if the user didn't provide one
    if not has_year:
        full_date_str = f"{date_str} {now.year}".title()
    else:
        full_date_str = date_str.title()

    # 4. Try parsing with various formats
    formats = ["%d %b %Y", "%b %d %Y", "%d %B %Y", "%B %d %Y"]
    parsed_date = None

    for fmt in formats:
        try:
            parsed_date = datetime.datetime.strptime(full_date_str, fmt).date()
            break
        except ValueError:
            continue

    if not parsed_date:
        raise ValueError(f"Could not parse date: {date_str}")

    # 5. SMART YEAR LOGIC
    # Only shift to next year if the user DID NOT provide a specific year
    if not has_year and parsed_date < now.date():
        parsed_date = parsed_date.replace(year=now.year + 1)

    return parsed_date



def get_date_info(
    date_str: Optional[str] = None,
    time_str: Optional[str] = None,
    working_hours: Optional[List[Dict]] = None
) -> dict:
    try:
        if not date_str and not time_str:
            return {"is_valid": False, "error_message": "Please provide a date or time."}
   
        # Default working hours
        if working_hours is None:
            working_hours = [
                {"day": "Monday", "type": "Working", "start_time": "10:00", "end_time": "19:00"},
                {"day": "Tuesday", "type": "Working", "start_time": "10:00", "end_time": "19:00"},
                {"day": "Wednesday", "type": "Working", "start_time": "10:00", "end_time": "19:00"},
                {"day": "Thursday", "type": "Working", "start_time": "10:00", "end_time": "19:00"},
                {"day": "Friday", "type": "Working", "start_time": "10:00", "end_time": "19:00"},
                {"day": "Saturday", "type": "Holiday", "start_time": "", "end_time": ""},
                {"day": "Sunday", "type": "Holiday", "start_time": "", "end_time": ""}
            ]

        now = datetime.datetime.now()
        current_date = now.date()
        time_provided = time_str is not None

        # ✅ DATE HANDLING
        if date_str:
            date_obj = parse_human_date(date_str)
        else:
            date_obj = current_date  # assume today if date not provided

        is_past = date_obj < current_date
        if is_past:
            error_message = f"It is not relevent to book a demo on a past date"
        day_of_week = date_obj.strftime("%A")

        # Get working day config
        day_config = next(
            (d for d in working_hours if d.get("day") == day_of_week),
            None
        )


        is_weekend = False
        is_outside_working_hours = False
        error_message = None
        suggested_hours_message = None

        # ✅ TIME HANDLING
        if time_str:
            time_str = normalize_time(time_str)
            parts = time_str.split(":")
            hour = int(parts[0])
            minute = int(parts[1]) if len(parts) > 1 else 0
            full_datetime = datetime.datetime.combine(date_obj, datetime.time(hour, minute))
            is_datetime_past = full_datetime < now
        else:
            hour = minute = None
            full_datetime = None
            is_datetime_past = False

        # ✅ WORKING HOURS CHECK
        if day_config:
            if day_config.get("type") == "Holiday":
                is_weekend = True
                error_message = f"We don't schedule meetings on {day_of_week}s.our working days are monday to firday."
            elif time_str and day_config.get("type") == "Working":
                start_time = day_config["start_time"]
                end_time = day_config["end_time"]

                start_h, start_m = map(int, start_time.split(":"))
                end_h, end_m = map(int, end_time.split(":"))

                time_minutes = hour * 60 + minute
                start_minutes = start_h * 60 + start_m
                end_minutes = end_h * 60 + end_m

                is_outside_working_hours = not (start_minutes <= time_minutes < end_minutes)

                if is_outside_working_hours:
                    start_12h = _format_time_12h(start_time)
                    end_12h = _format_time_12h(end_time)
                    error_message = f"Our working hours on {day_of_week}s are between {start_12h} and {end_12h}."
                    suggested_hours_message = f"{start_12h} to {end_12h}"
        else:
            is_weekend = True
            error_message = "That day is not available for meetings.our working days are monday to firday."

        six_months_later = current_date + datetime.timedelta(days=180)
        is_too_far = date_obj > six_months_later
        if is_too_far:
            error_message = "We only schedule meeting under 180 days"
        
        debug_data = {
            "is_valid": not (is_past or is_weekend or is_too_far or is_datetime_past or is_outside_working_hours),
            "time_provided": time_provided,
            "is_past":is_past,
            "is_datetime_past": is_datetime_past,
            "is_weekend": is_weekend,
            "is_too_far": is_too_far,
            "is_outside_working_hours": is_outside_working_hours,
            "day_of_week": day_of_week,
            "date": date_str,
            "time": time_str,
            "current_date": current_date.strftime("%Y-%m-%d"),
            "current_time": now.strftime("%H:%M"),
            "working_hours_config": day_config,
            "error_message": error_message,
            "suggested_hours": suggested_hours_message
        }
        print(debug_data)
        return debug_data

    except Exception as e:
        logger.error(f"Error validating datetime: {e}")
        return {"is_valid": False, "error": str(e)}

    





date_time_info = FunctionTool(
    func=get_date_info,
    name="date_time_info",
    description="Returns factual validation flags for date and time. No user messages."
)





guardrail_agent = AssistantAgent(
    name="guardrail_agent",
    model_client=client,
    system_message=GUARDRAIL_PROMPT,
)

classifier_agent = AssistantAgent(
    name="intent_classifier",
    system_message=CLASSIFIER_PROMPT,
    model_client=client,
)
 
sales_agent = AssistantAgent(
    name="sales_agent",
    system_message=SALES_PROMPT,
    model_client=client,
)

followup_agent = AssistantAgent(
    name="followup_agent",
    system_message=FOLLOW_UP_PROMPT,
    model_client=client,
    reflect_on_tool_use=True,
    tools=[date_time_info],
)


demo_agent = AssistantAgent(
    name="demo_booking_agent",
    system_message=DEMO_BOOKING_PROMPT,
    model_client=client,
    reflect_on_tool_use=True,
    tools=[date_time_info],
)


attack_agent = AssistantAgent(
    name="attack_agent",
    system_message=ATTACK_PROMPT,
    model_client=client,
)