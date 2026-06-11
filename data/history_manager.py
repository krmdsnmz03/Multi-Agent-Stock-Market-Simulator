import json
import os
from datetime import datetime

HISTORY_FILE = "data/history.json"

def load_history():
    """Loads the analysis history from the JSON file."""
    if not os.path.exists(HISTORY_FILE):
        return []
    try:
        with open(HISTORY_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading history: {e}")
        return []

def save_history(ticker, technical, fundamental, manager):
    """Saves a new analysis result to the history JSON file."""
    history = load_history()
    
    new_entry = {
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "ticker": ticker.upper(),
        "technical": technical,
        "fundamental": fundamental,
        "manager": manager
    }
    
    # Insert at the beginning so the newest is first
    history.insert(0, new_entry)
    
    try:
        # Ensure the directory exists
        os.makedirs(os.path.dirname(HISTORY_FILE), exist_ok=True)
        with open(HISTORY_FILE, "w", encoding="utf-8") as f:
            json.dump(history, f, indent=4, ensure_ascii=False)
    except Exception as e:
        print(f"Error saving history: {e}")
