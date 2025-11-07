# translate_text.py
import os, requests
from dotenv import load_dotenv
load_dotenv()

TRANSLATOR_KEY = os.getenv("TRANSLATOR_KEY")
TRANSLATOR_REGION = os.getenv("TRANSLATOR_REGION")
ENDPOINT = "https://api.cognitive.microsofttranslator.com/translate"

if not TRANSLATOR_KEY or not TRANSLATOR_REGION:
    raise EnvironmentError("TRANSLATOR_KEY or TRANSLATOR_REGION missing in .env")

def translate_text(text: str, to_lang: str = "hi") -> str:
    try:
        params = {"api-version": "3.0", "to": to_lang}
        headers = {
            "Ocp-Apim-Subscription-Key": TRANSLATOR_KEY,
            "Ocp-Apim-Subscription-Region": TRANSLATOR_REGION,
            "Content-type": "application/json"
        }
        body = [{"text": text}]
        r = requests.post(ENDPOINT, params=params, headers=headers, json=body, timeout=20)
        r.raise_for_status()
        js = r.json()
        return js[0]["translations"][0]["text"]
    except Exception as e:
        print("Translation error:", e)
        return text
