import os
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import PromptTemplate
from dotenv import load_dotenv

load_dotenv()

def analyze_technical_data(ticker: str, data_summary: str) -> str:
    """
    Uses Gemini to analyze technical stock data and generate a report.
    """
    llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash", temperature=0.2, google_api_key=os.getenv("GOOGLE_API_KEY"))
    
    template = """
    You are an expert Technical Analysis Agent for the stock market.
    Your task is to analyze the following technical data and indicators for {ticker}.
    
    Data Summary:
    {data_summary}
    
    Please provide:
    1. A summary of the current price trend (bullish, bearish, neutral).
    2. An interpretation of the moving averages (e.g., SMA_20 vs SMA_50 crossovers).
    3. An evaluation of momentum using RSI and MACD.
    4. A clear conclusion on the technical strength of the stock.
    
    Keep your analysis concise, professional, and directly related to the provided data.
    """
    
    prompt = PromptTemplate(template=template, input_variables=["ticker", "data_summary"])
    chain = prompt | llm
    
    try:
        response = chain.invoke({"ticker": ticker, "data_summary": data_summary})
        return response.content
    except Exception as e:
        return f"Error in Technical Analysis: {e}"
