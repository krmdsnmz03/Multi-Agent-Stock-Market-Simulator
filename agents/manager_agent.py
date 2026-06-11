import os
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import PromptTemplate
from dotenv import load_dotenv

load_dotenv()

def generate_portfolio_decision(ticker: str, tech_analysis: str, fund_analysis: str) -> str:
    """
    Acts as the Portfolio Manager, synthesizing reports to make a final buy/sell/hold decision.
    """
    llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash", temperature=0.1, google_api_key=os.getenv("GOOGLE_API_KEY"))
    
    template = """
    You are an elite Portfolio Manager Agent. Your task is to review the reports from your 
    Technical Analysis Agent and Fundamental Analysis Agent for the stock {ticker}, and 
    make a final investment decision.
    
    === Technical Analysis Report ===
    {tech_analysis}
    
    === Fundamental Analysis Report ===
    {fund_analysis}
    
    Please provide a comprehensive final report with the following structure:
    
    ## 1. Executive Summary
    Briefly summarize the findings from both reports.
    
    ## 2. Risk Assessment
    Evaluate the risks based on technical weaknesses or negative news.
    
    ## 3. Final Decision (BUY, SELL, or HOLD)
    Clearly state your final recommendation. Justify this decision by weighing the technical 
    trends against the fundamental catalysts. Ensure you explicitly say "Recommendation: BUY", 
    "Recommendation: SELL", or "Recommendation: HOLD".
    """
    
    prompt = PromptTemplate(
        template=template, 
        input_variables=["ticker", "tech_analysis", "fund_analysis"]
    )
    chain = prompt | llm
    
    try:
        response = chain.invoke({
            "ticker": ticker, 
            "tech_analysis": tech_analysis, 
            "fund_analysis": fund_analysis
        })
        return response.content
    except Exception as e:
        return f"Error in Portfolio Manager Analysis: {e}"
