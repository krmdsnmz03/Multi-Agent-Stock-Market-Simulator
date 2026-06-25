import streamlit as st
import plotly.graph_objects as go
import pandas as pd
import time
from workflow import run_analysis_pipeline
from data.history_manager import save_history, load_history
from data.market_data import get_market_overview, backtest_strategy

st.set_page_config(page_title="Autonomous Stock Market Simulator", layout="wide")

# Custom CSS for styling cards and metrics
st.markdown("""
<style>
    .metric-trend-up {
        color: #10B981 !important;
        font-weight: bold;
    }
    .metric-trend-down {
        color: #EF4444 !important;
        font-weight: bold;
    }
</style>
""", unsafe_allow_html=True)

st.title("🤖 Autonomous Multi-Agent Stock Market Simulator")
st.markdown("""
This application uses three LangChain/Gemini AI Agents to analyze stocks:
1. **Technical Agent:** Analyzes chart patterns and indicators.
2. **Fundamental Agent:** Analyzes the latest news and catalysts.
3. **Portfolio Manager Agent:** Synthesizes everything and makes a final decision.
""")

# Initialize session state
if "ticker" not in st.session_state:
    st.session_state.ticker = "AAPL"
if "run_analysis_triggered" not in st.session_state:
    st.session_state.run_analysis_triggered = False

st.sidebar.header("Configuration")
ticker_input = st.sidebar.text_input("Enter Stock Ticker (e.g., AAPL, TSLA, MSFT)", value=st.session_state.ticker).upper()

# Update session state if input changes
if ticker_input != st.session_state.ticker:
    st.session_state.ticker = ticker_input

# Load search history to show in dropdown
history = load_history()
seen = set()
past_tickers = []
for entry in history:
    t = entry.get("ticker", "").upper()
    if t and t not in seen:
        seen.add(t)
        past_tickers.append(t)

# Display select box for past tickers if any exist
if past_tickers:
    selected_recent = st.sidebar.selectbox(
        "Or Select from Search History:",
        options=["-- Select Ticker --"] + past_tickers,
        key="recent_tickers_select"
    )
    if selected_recent != "-- Select Ticker --":
        st.session_state.ticker = selected_recent
        st.rerun()

# Advanced configuration expander
with st.sidebar.expander("🛠️ Advanced Settings (Agent Personas)", expanded=False):
    short_sma = st.slider("Short-term SMA period", min_value=5, max_value=30, value=20)
    long_sma = st.slider("Long-term SMA period", min_value=31, max_value=100, value=50)
    manager_persona = st.selectbox("Portfolio Manager Persona", ["Balanced", "Aggressive", "Conservative"])

run_analysis = st.sidebar.button("Run Analysis")

if run_analysis:
    st.session_state.run_analysis_triggered = True

tab_dash, tab_hist = st.tabs(["📊 Dashboard", "🕒 History"])

def draw_sparkline(history_list, is_positive):
    color = "#10B981" if is_positive else "#EF4444"
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        y=history_list,
        mode="lines",
        line=dict(color=color, width=2.5),
        hoverinfo="none"
    ))
    fig.update_layout(
        xaxis=dict(visible=False, showgrid=False, zeroline=False),
        yaxis=dict(visible=False, showgrid=False, zeroline=False),
        margin=dict(l=0, r=0, t=4, b=4),
        height=50,
        showlegend=False,
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)'
    )
    return fig

with tab_dash:
    if st.session_state.run_analysis_triggered:
        # Back button to return to overview
        if st.button("⬅️ Back to Market Overview", use_container_width=True):
            st.session_state.run_analysis_triggered = False
            st.rerun()
            
        ticker = st.session_state.ticker
        with st.spinner(f"Agents are analyzing {ticker}... This may take a minute."):
            results = run_analysis_pipeline(ticker, short_sma=short_sma, long_sma=long_sma, persona=manager_persona)
            
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
            fig.update_layout(title=f"{ticker} 1-Year Price (with SMAs)", xaxis_rangeslider_visible=False)
            st.plotly_chart(fig, use_container_width=True)
            
            # Consensus Gauge & Supervisor Audit
            st.divider()
            col_gauge, col_supervisor = st.columns([1, 1.5])
            
            manager_decision = results.get("manager", "")
            score = 50
            if "BUY" in manager_decision.upper():
                score = 85
            elif "SELL" in manager_decision.upper():
                score = 15
                
            with col_gauge:
                st.subheader("🎯 Consensus Decision Meter")
                fig_gauge = go.Figure(go.Indicator(
                    mode = "gauge+number",
                    value = score,
                    domain = {'x': [0, 1], 'y': [0, 1]},
                    gauge = {
                        'axis': {'range': [0, 100], 'tickwidth': 1, 'tickcolor': "gray"},
                        'bar': {'color': "rgba(0,0,0,0.15)"},
                        'bgcolor': "rgba(0,0,0,0.05)",
                        'borderwidth': 1,
                        'bordercolor': "gray",
                        'steps': [
                            {'range': [0, 35], 'color': '#EF4444'},
                            {'range': [35, 65], 'color': '#FBBF24'},
                            {'range': [65, 100], 'color': '#10B981'}
                        ],
                        'threshold': {
                            'line': {'color': "black", 'width': 4},
                            'thickness': 0.75,
                            'value': score
                        }
                    }
                ))
                fig_gauge.update_layout(height=220, margin=dict(l=20, r=20, t=30, b=10))
                st.plotly_chart(fig_gauge, use_container_width=True, config={'displayModeBar': False})
                
            with col_supervisor:
                st.subheader("🔍 Supervisor Cognitive Bias Audit")
                st.info(results.get("supervisor", "Supervisor audit not available."))
            
            # Create columns for Tech and Fund reports
            st.divider()
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
            
            # 5. Backtesting Module
            st.divider()
            with st.expander("📊 Strategy Backtest (1-Year Crossover Performance)", expanded=True):
                with st.spinner("Running historical backtest..."):
                    backtest_results = backtest_strategy(ticker, short_sma=short_sma, long_sma=long_sma)
                    
                if backtest_results:
                    b_col1, b_col2, b_col3 = st.columns(3)
                    with b_col1:
                        st.metric("Strategy Return (SMA Crossover)", f"{backtest_results['strategy_return']:+.2f}%")
                    with b_col2:
                        st.metric("Benchmark Return (Buy & Hold)", f"{backtest_results['bh_return']:+.2f}%")
                    with b_col3:
                        perf_diff = backtest_results['strategy_return'] - backtest_results['bh_return']
                        st.metric("Outperformance vs Benchmark", f"{perf_diff:+.2f}%", delta=f"{perf_diff:+.2f}%")
                    
                    # Plot equity curves
                    fig_bt = go.Figure()
                    fig_bt.add_trace(go.Scatter(x=backtest_results['df'].index, y=backtest_results['df']['Strategy'], name="SMA Strategy", line=dict(color='#10B981', width=2)))
                    fig_bt.add_trace(go.Scatter(x=backtest_results['df'].index, y=backtest_results['df']['Buy_Hold'], name="Buy & Hold Benchmark", line=dict(color='#64748B', width=1.5, dash='dash')))
                    fig_bt.update_layout(title="Equity Growth ($10,000 Initial Capital)", xaxis_title="Date", yaxis_title="Portfolio Value ($)", height=350, margin=dict(l=20, r=20, t=40, b=20))
                    st.plotly_chart(fig_bt, use_container_width=True)
                    
                    # Display trade logs if any exist
                    trades = backtest_results.get("trades", [])
                    if trades:
                        with st.expander("📜 Transaction History (Trades Executed)"):
                            trade_df = pd.DataFrame(trades)
                            st.dataframe(trade_df, use_container_width=True)
                    else:
                        st.info("No trades executed during this 1-year period (no SMA crossovers detected).")
            
            # Export Report Button
            st.divider()
            report_md = f"""# Multi-Agent Stock Analysis Report: {ticker}
**Company Name:** {results.get('company_name', ticker)}
**Analysis Date:** {time.strftime('%Y-%m-%d %H:%M:%S')}
**Style/Persona:** {manager_persona}
**SMAs Configured:** Short-term={short_sma}, Long-term={long_sma}

---

## 📈 Technical Agent Report
{results['technical']}

---

## 📰 Fundamental Agent Report
{results['fundamental']}

---

## 💼 Portfolio Manager Final Recommendation
{results['manager']}

---

## 🔍 Supervisor Cognitive Bias Audit
{results.get('supervisor', 'N/A')}
"""
            st.download_button(
                label="📥 Download Full Analysis Report (Markdown)",
                data=report_md,
                file_name=f"{ticker}_analysis_report.md",
                mime="text/markdown",
                use_container_width=True
            )
            
            # Save to History
            save_history(ticker, results["technical"], results["fundamental"], results["manager"], results.get("supervisor", "No supervisor report available."))
    else:
        st.header("📈 US Market Overview")
        st.write("Current daily trends for indices and major companies. Click 'Analyze' to run multi-agent simulations.")
        
        with st.spinner("Fetching market overview data..."):
            overview = get_market_overview()
            
        if not overview:
            st.warning("Unable to load market data. Please enter a stock ticker in the sidebar to start a simulation.")
        else:
            # 1. Render Indices (S&P 500, Nasdaq 100)
            st.subheader("Indices")
            col_sp, col_nas = st.columns(2)
            
            # S&P 500
            if "^GSPC" in overview:
                sp_data = overview["^GSPC"]
                with col_sp:
                    with st.container(border=True):
                        c_text, c_chart = st.columns([1.2, 1.5])
                        with c_text:
                            st.markdown(f"### {sp_data['name']}")
                            st.caption(sp_data['symbol'])
                            st.markdown(f"## {sp_data['price']:,.2f}")
                            trend_class = "metric-trend-up" if sp_data['change'] >= 0 else "metric-trend-down"
                            st.markdown(f"<span class='{trend_class}'>{sp_data['change']:+.2f}%</span>", unsafe_allow_html=True)
                        with c_chart:
                            fig = draw_sparkline(sp_data['history'], sp_data['change'] >= 0)
                            st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})
            
            # Nasdaq 100
            if "^IXIC" in overview:
                nas_data = overview["^IXIC"]
                with col_nas:
                    with st.container(border=True):
                        c_text, c_chart = st.columns([1.2, 1.5])
                        with c_text:
                            st.markdown(f"### {nas_data['name']}")
                            st.caption(nas_data['symbol'])
                            st.markdown(f"## {nas_data['price']:,.2f}")
                            trend_class = "metric-trend-up" if nas_data['change'] >= 0 else "metric-trend-down"
                            st.markdown(f"<span class='{trend_class}'>{nas_data['change']:+.2f}%</span>", unsafe_allow_html=True)
                        with c_chart:
                            fig = draw_sparkline(nas_data['history'], nas_data['change'] >= 0)
                            st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})
            
            st.divider()
            
            # 2. Render Major Tech Stocks in 3 columns
            st.subheader("Major US Companies")
            tech_tickers = ["AAPL", "MSFT", "GOOGL", "NVDA", "TSLA", "AMZN"]
            
            # Create a 3-column layout
            cols = st.columns(3)
            
            for i, sym in enumerate(tech_tickers):
                if sym in overview:
                    stock_data = overview[sym]
                    col_index = i % 3
                    with cols[col_index]:
                        with st.container(border=True):
                            s_text, s_chart = st.columns([1.2, 1.2])
                            with s_text:
                                st.markdown(f"**{stock_data['name']}**")
                                st.caption(stock_data['symbol'])
                                st.markdown(f"### ${stock_data['price']:,.2f}")
                                trend_class = "metric-trend-up" if stock_data['change'] >= 0 else "metric-trend-down"
                                st.markdown(f"<span class='{trend_class}'>{stock_data['change']:+.2f}%</span>", unsafe_allow_html=True)
                            with s_chart:
                                fig = draw_sparkline(stock_data['history'], stock_data['change'] >= 0)
                                st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})
                            
                            # Run Analysis trigger button
                            if st.button(f"Analyze {sym}", key=f"analyze_{sym}", use_container_width=True):
                                st.session_state.ticker = sym
                                st.session_state.run_analysis_triggered = True
                                st.rerun()

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
            
            # Consensus and Bias Audit in History too
            h_score = 50
            if "BUY" in selected_item["manager"].upper():
                h_score = 85
            elif "SELL" in selected_item["manager"].upper():
                h_score = 15
                
            col_h_gauge, col_h_supervisor = st.columns([1, 1.5])
            with col_h_gauge:
                st.subheader("🎯 Consensus Decision Meter")
                fig_h_gauge = go.Figure(go.Indicator(
                    mode = "gauge+number",
                    value = h_score,
                    domain = {'x': [0, 1], 'y': [0, 1]},
                    gauge = {
                        'axis': {'range': [0, 100], 'tickwidth': 1, 'tickcolor': "gray"},
                        'bar': {'color': "rgba(0,0,0,0.15)"},
                        'bgcolor': "rgba(0,0,0,0.05)",
                        'borderwidth': 1,
                        'bordercolor': "gray",
                        'steps': [
                            {'range': [0, 35], 'color': '#EF4444'},
                            {'range': [35, 65], 'color': '#FBBF24'},
                            {'range': [65, 100], 'color': '#10B981'}
                        ],
                        'threshold': {
                            'line': {'color': "black", 'width': 4},
                            'thickness': 0.75,
                            'value': h_score
                        }
                    }
                ))
                fig_h_gauge.update_layout(height=200, margin=dict(l=20, r=20, t=30, b=10))
                st.plotly_chart(fig_h_gauge, use_container_width=True, config={'displayModeBar': False})
                
            with col_h_supervisor:
                st.subheader("🔍 Supervisor Cognitive Bias Audit")
                st.info(selected_item.get("supervisor", "No supervisor report available for this older entry."))
            
            st.divider()
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
