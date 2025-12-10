# client.py
from dotenv import load_dotenv
import os
from openai import OpenAI, AzureOpenAI

load_dotenv()

# --- Direct OpenAI client (optional) ---
openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# --- Azure OpenAI client ---
azure_client = AzureOpenAI(
    api_version="2025-03-01-preview",
    azure_endpoint="https://ai-ethan0241ai492715927424.openai.azure.com/",
    api_key=os.getenv("AZURE_OPENAI_API_KEY"),
)


# --- Default client (choose one) ---
# You can toggle this dynamically:
USE_AZURE = True
client = azure_client if USE_AZURE else openai_client
