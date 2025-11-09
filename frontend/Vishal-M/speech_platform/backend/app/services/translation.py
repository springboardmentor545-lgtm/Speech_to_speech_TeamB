# app/services/translation.py
import os
import requests
import uuid
from typing import Optional, List, Dict
from dotenv import load_dotenv
import structlog

# Load environment variables
load_dotenv()

logger = structlog.get_logger()

# --- NEW: Read Translator Service keys ---
TRANSLATOR_KEY = os.getenv("AZURE_TRANSLATOR_KEY")
TRANSLATOR_REGION = os.getenv("AZURE_TRANSLATOR_REGION")

# The global endpoint for the Translator service
TRANSLATOR_ENDPOINT = os.getenv("AZURE_TRANSLATOR_ENDPOINT")

# Validate keys
if not all([TRANSLATOR_KEY, TRANSLATOR_REGION]):
    logger.error(
        "Missing required environment variables for Translator service. "
        "Check TRANSLATOR_KEY and TRANSLATOR_REGION"
    )
    client_ready = False
else:
    client_ready = True
    logger.info(f"Azure AI Translator client initialized. Region: {TRANSLATOR_REGION}")


# Language mapping (optional, but good for logging)
SUPPORTED_LANGUAGES = {
    'es': 'Spanish', 'fr': 'French', 'de': 'German', 'it': 'Italian', 'pt': 'Portuguese',
    'ja': 'Japanese', 'ko': 'Korean', 'zh': 'Chinese', 'ar': 'Arabic', 'hi': 'Hindi',
    'ru': 'Russian', 'nl': 'Dutch', 'tr': 'Turkish', 'sv': 'Swedish', 'pl': 'Polish',
    'vi': 'Vietnamese', 'th': 'Thai', 'en': 'English', 'ta': 'Tamil', 'te': 'Telugu'
}

def translate_text(
    text: str, 
    target_language: str, 
    source_language: str = "en",
    domain: str = "general",
    glossary_rules: Optional[List[Dict]] = None # Note: Glossary works differently here
) -> dict:
    
    if not client_ready:
        logger.error("Translation failed: Azure Translator client not initialized")
        return {
            'success': False,
            'error': 'Azure Translator client is not initialized. Check environment variables.',
            'source_text': text,
            'translated_text': None
        }

    # The API path
    path = '/translate?api-version=3.0'
    
    # Set the 'from' and 'to' parameters
    params = {
        'to': target_language
    }
    
    # Add source language if it's not 'auto'
    if source_language and source_language.lower() != 'auto':
        params['from'] = source_language

    # Set headers
    headers = {
        'Ocp-Apim-Subscription-Key': TRANSLATOR_KEY,
        'Ocp-Apim-Subscription-Region': TRANSLATOR_REGION,
        'Content-type': 'application/json',
        'X-ClientTraceId': str(uuid.uuid4())
    }

    # Create the request body
    body = [{
        'text': text
    }]

    try:
        # Call the API
        response = requests.post(TRANSLATOR_ENDPOINT + path, params=params, headers=headers, json=body)
        response.raise_for_status() # Raise an exception for bad status codes
        
        # Parse the JSON response
        json_response = response.json()
        
        if not json_response or len(json_response) == 0 or 'translations' not in json_response[0]:
             raise ValueError("Invalid response structure from Translator")

        translation = json_response[0]['translations'][0]['text']

        if not translation:
            raise ValueError("Empty translation received from model")

        logger.info(f"Translation successful (Azure AI Translator)")
        
        return {
            'success': True,
            'translated_text': translation,
            'source_text': text,
            'source_language': source_language,
            'target_language': target_language,
            'target_language_code': target_language,
            'tokens_used': 0, # Not applicable in the same way
            'model': 'Azure-AI-Translator'
        }
        
    except Exception as e:
        logger.error("Translation error", error=str(e), exc_info=True)
        return {
            'success': False,
            'error': str(e),
            'source_text': text,
            'translated_text': None
        }