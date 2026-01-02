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

def get_current_time() -> str:
    return datetime.datetime.now().strftime("%I:%M %p")





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
    tools=[get_current_time],
)


demo_agent = AssistantAgent(
    name="demo_booking_agent",
    system_message=DEMO_BOOKING_PROMPT,
    model_client=client,
    tools=[get_current_time],
)


attack_agent = AssistantAgent(
    name="attack_agent",
    system_message=ATTACK_PROMPT,
    model_client=client,
)