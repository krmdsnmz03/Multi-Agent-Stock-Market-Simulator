import os
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import PromptTemplate
from dotenv import load_dotenv

load_dotenv()

def analyze_fundamental_data(ticker: str, news_data: list) -> str:
    """
    Uses Gemini to analyze recent news and perform sentiment analysis.
    """
    llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash", temperature=0.3, google_api_key=os.getenv("GOOGLE_API_KEY"))
    
    # Format news items for the prompt
    formatted_news = "\n".join([f"- {n['title']}: {n['description']} (Source: {n['source']})" for n in news_data])
    if not formatted_news:
        formatted_news = "No recent news available."
        
    template = """
    You are an expert Fundamental Analysis and Sentiment Analysis Agent.
    Your task is to evaluate the following recent news articles for {ticker}.
    
    Recent News:
    {formatted_news}
    
    Please provide:
    1. An overall sentiment score (Bullish, Bearish, or Neutral).
    2. A summary of the key positive and negative catalysts mentioned in the news.
    3. Any potential macroeconomic or sector-specific impacts discussed.
    4. A concise conclusion on the fundamental outlook based on this news.
    
    Base your analysis strictly on the provided news. Do not hallucinate external events.
    """
    
    prompt = PromptTemplate(template=template, input_variables=["ticker", "formatted_news"])
    chain = prompt | llm
    
    try:
        response = chain.invoke({"ticker": ticker, "formatted_news": formatted_news})
        return response.content
    except Exception as e:
        return f"Error in Fundamental Analysis: {e}"
