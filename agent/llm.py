from langchain_google_genai import ChatGoogleGenerativeAI
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

gemini = ChatGoogleGenerativeAI(
    model="gemini-2.5-flash",
    temperature=0,
    timeout=60,  
    max_retries=2,
    transport="rest",
    google_api_key=os.getenv("GOOGLE_API_KEY")
)
