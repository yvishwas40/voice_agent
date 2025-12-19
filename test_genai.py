import os
from google import genai
from google.genai import types
from dotenv import load_dotenv

load_dotenv()

api_key = os.getenv("GOOGLE_API_KEY")
client = genai.Client(api_key=api_key)

print("Attempting to generate content...")
try:
    # Try the correct method structure for new SDK
    response = client.models.generate_content(
        model="gemini-1.5-flash",
        contents="Say hello in JSON",
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
            temperature=0.0
        )
    )
    print("Success:")
    print(response.text)
except Exception as e:
    print(f"Error: {e}")
    # Inspect client
    print(dir(client))
