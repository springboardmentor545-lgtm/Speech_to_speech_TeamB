# backend/utils/translation.py
import os
import aiohttp
import structlog
from typing import List, Dict
import uuid
logger = structlog.get_logger()

AZURE_TRANSLATOR_KEY = os.getenv("AZURE_TRANSLATOR_KEY")
AZURE_TRANSLATOR_REGION = os.getenv("AZURE_TRANSLATOR_REGION")


if not AZURE_TRANSLATOR_KEY or not AZURE_TRANSLATOR_REGION:
    logger.warning("Azure Translator key/region not set. translate_text will return an error placeholder.")


async def translate_text(text: str, source_language: str, target_language: str, glossary_rules: List[Dict[str, str]] = None) -> str:
    """Translate text using Microsoft Translator API (real)."""
    if not AZURE_TRANSLATOR_KEY or not AZURE_TRANSLATOR_REGION:
        logger.error("Azure Translator environment variables missing.")
        return f"[TRANSLATION ERROR: Translator not configured] {text}"

    # Apply glossary rules
    if glossary_rules:
        for rule in glossary_rules:
            # Ensure the rule is for the correct language pair
            if rule.get("language_pair") == f"{source_language}-{target_language}":
                source_term = rule.get("source_term")
                target_term = rule.get("target_term")
                if source_term and target_term:
                    # Using the dynamic dictionary feature
                    text = text.replace(source_term, f'<mstrans:dictionary translation="{target_term}">{source_term}</mstrans:dictionary>')

    endpoint = "https://api.cognitive.microsofttranslator.com/translate"
    params = {"api-version": "3.0", "from": source_language, "to": [target_language]}
    headers = {
        "Ocp-Apim-Subscription-Key": AZURE_TRANSLATOR_KEY,
        "Ocp-Apim-Subscription-Region": AZURE_TRANSLATOR_REGION,
        "Content-type": "application/json",
        "X-ClientTraceId": str(uuid.uuid4()),
    }

    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(endpoint, params=params, headers=headers, json=[{"text": text}]) as response:
                if response.status != 200:
                    error_text = await response.text()
                    logger.error("Translation API error", status=response.status, body=error_text)
                    return f"[TRANSLATION ERROR: {response.status}] {text}"

                result = await response.json()
                translated = result[0]["translations"][0]["text"]
                logger.info("✅ Azure Translator success", src=text[:30], tgt=translated[:30])
                return translated

    except Exception as e:
        logger.error("❌ Azure Translator failed", error=str(e))
        return f"[TRANSLATION ERROR: {str(e)}] {text}"
