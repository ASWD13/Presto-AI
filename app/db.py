import os
import json
from datetime import datetime
from supabase import create_client
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

def save_log(text, analysis, entities):
    """Save a new log entry into Supabase"""
    supabase.table("logs").insert({
        "text": text,
        "analysis": analysis,
        "entities": json.dumps(entities),
        "timestamp": datetime.utcnow().isoformat()
    }).execute()

def load_logs(limit=5):
    """Fetch the most recent logs"""
    response = supabase.table("logs").select("*").order("id", desc=True).limit(limit).execute()
    return response.data

def load_logs_by_role(role, limit=5):
    """
    Fetch logs with role-based filtering.
    Only Operative role can see full logs, others see limited information.
    """
    if role == "Operative":
        return load_logs(limit)
    else:
        # For non-Operative roles, return limited log information
        response = supabase.table("logs").select("id, analysis, timestamp").order("id", desc=True).limit(limit).execute()
        return response.data

def delete_log(log_id):
    """Delete a specific log entry by ID"""
    supabase.table("logs").delete().eq("id", log_id).execute()

def delete_all_logs():
    """Delete all log entries from the database"""
    supabase.table("logs").delete().neq("id", 0).execute()
