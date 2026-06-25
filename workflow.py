import time
from data.market_data import get_historical_data, get_stock_info
from data.news_data import get_company_news
from agents.tech_agent import analyze_technical_data
from agents.fund_agent import analyze_fundamental_data
from agents.manager_agent import generate_portfolio_decision
from agents.supervisor_agent import audit_investment_thesis

def run_analysis_pipeline(ticker: str, short_sma: int = 20, long_sma: int = 50, persona: str = "Balanced") -> dict:
    """
    Executes the full multi-agent analysis pipeline for a given ticker,
    incorporating agent configurations and a supervisor audit check.
    """
    results = {}
    
    # 1. Fetch Data
    print(f"Fetching data for {ticker}...")
    try:
        info = get_stock_info(ticker)
        company_name = info.get("shortName", ticker)
    except:
        company_name = ticker
        
    hist_data = get_historical_data(ticker, period="1y", short_sma=short_sma, long_sma=long_sma)
    news_data = get_company_news(ticker, company_name=company_name, limit=5)
    
    # Check if historical data is empty
    if hist_data.empty:
        return {"error": f"No historical data found for {ticker}."}
        
    # Summarize technical data for the prompt to save tokens
    recent_data = hist_data.tail(5).copy()
    data_summary_str = recent_data[['Close', 'SMA_20', 'SMA_50', 'RSI', 'MACD']].to_string()
    
    # 2. Run Technical Agent
    print(f"Running Technical Analysis for {ticker}...")
    tech_report = analyze_technical_data(ticker, data_summary_str)
    results["technical"] = tech_report
    
    # To avoid Gemini Free Tier API rate limits (15 RPM), we wait slightly
    time.sleep(10)
    
    # 3. Run Fundamental Agent
    print(f"Running Fundamental Analysis for {ticker}...")
    fund_report = analyze_fundamental_data(ticker, news_data)
    results["fundamental"] = fund_report
    
    # To avoid Gemini Free Tier API rate limits (15 RPM), we wait slightly
    time.sleep(10)
    
    # 4. Run Portfolio Manager Agent
    print(f"Generating Portfolio Manager Decision for {ticker}...")
    manager_report = generate_portfolio_decision(ticker, tech_report, fund_report, persona=persona)
    results["manager"] = manager_report
    
    # To avoid Gemini Free Tier API rate limits (15 RPM), we wait slightly
    time.sleep(10)
    
    # 5. Run Supervisor Bias Auditor Agent
    print(f"Running Supervisor Cognitive Bias Audit for {ticker}...")
    supervisor_report = audit_investment_thesis(ticker, manager_report)
    results["supervisor"] = supervisor_report
    
    # Return raw data for UI plotting
    results["hist_data"] = hist_data
    results["news_data"] = news_data
    results["company_name"] = company_name
    
    return results

