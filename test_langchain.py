import os
from langchain_google_genai import ChatGoogleGenerativeAI
from dotenv import load_dotenv

load_dotenv()

try:
    llm = ChatGoogleGenerativeAI(model="gemini-1.5-pro", temperature=0.2, google_api_key=os.getenv("GOOGLE_API_KEY"))
    response = llm.invoke("Hello")
    print("Success:", response.content)
except Exception as e:
    print("Error:", e)
