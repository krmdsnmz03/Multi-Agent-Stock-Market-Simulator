import os
import requests
from dotenv import load_dotenv

load_dotenv()

NEWS_API_KEY = os.getenv("NEWS_API_KEY")

def get_company_news(ticker: str, company_name: str = "", limit: int = 5) -> list:
    """
    Fetches latest news for a given ticker or company name using NewsAPI.
    If NEWS_API_KEY is not set or invalid, it returns mock data to allow testing.
    """
    if not NEWS_API_KEY or NEWS_API_KEY == "your_news_api_key_here":
        print("Warning: NEWS_API_KEY is not set. Returning mock news data.")
        return [
            {"title": f"{ticker} announces strong Q3 earnings", "description": f"The company beat revenue expectations...", "source": "Mock News"},
            {"title": f"Market rally boosts {ticker} stock", "description": f"Overall market positivity has pushed {ticker} to new highs.", "source": "Mock News"}
        ]
        
    query = company_name if company_name else ticker
    url = f"https://newsapi.org/v2/everything?q={query}&sortBy=publishedAt&pageSize={limit}&apiKey={NEWS_API_KEY}"
    
    try:
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
        
        articles = []
        for item in data.get("articles", []):
            articles.append({
                "title": item.get("title", ""),
                "description": item.get("description", ""),
                "source": item.get("source", {}).get("name", "Unknown"),
                "publishedAt": item.get("publishedAt", "")
            })
        return articles
    except Exception as e:
        print(f"Error fetching news: {e}")
        return []
