# pyrefly: ignore [missing-import]
import google.genai as genai
import os

client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))
try:
    response = client.models.generate_content(model="gemini-3.1-flash-lite", contents="Hello")
    print("SUCCESS:", response.text)
except Exception as e:
    print("ERROR:", type(e).__name__)
    print(str(e))
