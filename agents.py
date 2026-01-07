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

from datetime import date

import datetime
import re
from typing import Optional


import datetime
import re
from typing import Optional,Dict


from autogen_core.tools import FunctionTool


def get_date_info(date_str: str) -> dict:
    parsed_date = datetime.datetime.strptime("10 Jan 2026 02:00 PM", "%d %b %Y %I:%M %p").date()


    return {
        "date": parsed_date.isoformat(),
        "weekday": parsed_date.strftime("%A"),
        "weekday_abbr": parsed_date.strftime("%a"),
        "weekday_index": parsed_date.weekday(),
        "is_working_day": parsed_date.weekday() < 5
    }


date_time_info = FunctionTool(
    func=get_date_info,
    name="get_date_info",
    description=(
        "Analyzes a provided date and time. "
        "Assumes current year if missing. "
        "Parses month abbreviations and times like '2 am' or '4 pm'."
        "return output to prompt"
        "dont return output to user give output to prompt and ask what to do next"
    )
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
)

validator_agent = AssistantAgent(
    name="validator_agent",
    system_message="""
You are a validation agent.

Rules:
- Use the provided tool to analyze the user's date and time.
- Respond ONLY with structured validation results.
- Do NOT speak in natural language.
- Do NOT explain anything.
""",
    model_client=client,
    reflect_on_tool_use=True,
    tools=[get_date_info],
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