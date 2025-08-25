import os
import json
import streamlit as st
from supabase import create_client, Client

# Prefer Streamlit secrets, fallback to environment variables for local dev
def _get_secret(name: str, default: str | None = None) -> str | None:
    # Try flat keys in st.secrets first
    if name in st.secrets:
        return st.secrets[name]
    # Try nested structure like st.secrets["supabase"]["url"|"key"]
    if "supabase" in st.secrets:
        nested = st.secrets["supabase"]
        mapped_key = {"SUPABASE_URL": "url", "SUPABASE_KEY": "key"}.get(name)
        if mapped_key and mapped_key in nested:
            return nested[mapped_key]
    # Fallback to environment variable
    return os.getenv(name, default)

SUPABASE_URL = _get_secret("SUPABASE_URL")
SUPABASE_KEY = _get_secret("SUPABASE_KEY")

try:
    supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
except Exception as e:
    st.error("Could not connect to Supabase. Please check your .env file and Supabase credentials.")
    st.stop()

def save_log(text, analysis, entities):
    """Save a new log entry. Relies on Supabase's default created_at column."""
    try:
        supabase.table("logs").insert({
            "text": text,
            "analysis": analysis,
            "entities": json.dumps(entities)
        }).execute()
    except Exception as e:
        st.error(f"DB Error: Could not save log. {e}")

def load_logs_by_role(role: str, limit: int = 5):
    """Fetches logs from the database, respecting RBAC."""
    try:
        # Full data for Operative, limited for others (app logic decides what to show)
        query = supabase.table('logs').select('*').order('created_at', desc=True).limit(limit)
        response = query.execute()
        return response.data
    except Exception as e:
        st.error(f"DB Error: Could not load role-based logs. {e}")
        return []

def load_all_logs():
    """Fetches all log records for the dashboard."""
    try:
        response = supabase.table('logs').select('*').order('created_at', desc=True).execute()
        return response.data
    except Exception as e:
        st.error(f"DB Error: Could not load all logs for dashboard. {e}")
        return []

def delete_log(log_id):
    """Delete a specific log entry by ID."""
    try:
        supabase.table("logs").delete().eq("id", log_id).execute()
    except Exception as e:
        st.error(f"DB Error: Could not delete log. {e}")

def delete_all_logs():
    """Delete all log entries."""
    try:
        supabase.table("logs").delete().neq("id", 0).execute() # Deletes all rows
    except Exception as e:
        st.error(f"DB Error: Could not delete all logs. {e}")