import streamlit as st
import plotly.graph_objects as go
from workflow import run_analysis_pipeline
from data.history_manager import save_history, load_history

st.set_page_config(page_title="Autonomous Stock Market Simulator", layout="wide")

st.title("🤖 Autonomous Multi-Agent Stock Market Simulator")
st.markdown("""
This application uses three LangChain/Gemini AI Agents to analyze stocks:
1. **Technical Agent:** Analyzes chart patterns and indicators.
2. **Fundamental Agent:** Analyzes the latest news and catalysts.
3. **Portfolio Manager Agent:** Synthesizes everything and makes a final decision.
""")

st.sidebar.header("Configuration")
ticker = st.sidebar.text_input("Enter Stock Ticker (e.g., AAPL, TSLA, MSFT)", "AAPL").upper()
run_analysis = st.sidebar.button("Run Analysis")

tab_dash, tab_hist = st.tabs(["📊 Dashboard", "🕒 History"])

with tab_dash:
    if run_analysis:
        with st.spinner(f"Agents are analyzing {ticker}... This may take a minute."):
            results = run_analysis_pipeline(ticker)
            
        if "error" in results:
            st.error(results["error"])
        else:
            st.success(f"Analysis complete for {results.get('company_name', ticker)} ({ticker})!")
            
            # 1. Price Chart
            st.subheader("📊 Recent Price Chart")
            hist_data = results["hist_data"]
            
            fig = go.Figure(data=[go.Candlestick(x=hist_data.index,
                            open=hist_data['Open'],
                            high=hist_data['High'],
                            low=hist_data['Low'],
                            close=hist_data['Close'])])
            fig.update_layout(title=f"{ticker} 1-Year Price", xaxis_rangeslider_visible=False)
            st.plotly_chart(fig, use_container_width=True)
            
            # Create columns for Tech and Fund reports
            col1, col2 = st.columns(2)
            
            with col1:
                st.subheader("📈 Technical Agent Report")
                st.info(results["technical"])
                
            with col2:
                st.subheader("📰 Fundamental Agent Report")
                st.warning(results["fundamental"])
                
            # Manager Report
            st.divider()
            st.subheader("💼 Portfolio Manager Final Decision")
            st.success(results["manager"])
            
            # Save to History
            save_history(ticker, results["technical"], results["fundamental"], results["manager"])

with tab_hist:
    st.header("🕒 Historical Analyses")
    history = load_history()
    
    if not history:
        st.info("No historical analyses found yet. Run an analysis in the Dashboard to save it here.")
    else:
        # Create a dictionary for the selectbox to map display text to the history object
        history_options = {f"{item['timestamp']} - {item['ticker']}": item for item in history}
        selected_key = st.selectbox("Select a past analysis to view:", list(history_options.keys()))
        
        if selected_key:
            selected_item = history_options[selected_key]
            
            st.subheader(f"Results for {selected_item['ticker']} ({selected_item['timestamp']})")
            
            col1, col2 = st.columns(2)
            with col1:
                st.subheader("📈 Technical Agent Report")
                st.info(selected_item["technical"])
                
            with col2:
                st.subheader("📰 Fundamental Agent Report")
                st.warning(selected_item["fundamental"])
                
            st.divider()
            st.subheader("💼 Portfolio Manager Final Decision")
            st.success(selected_item["manager"])
