import sys
import os
import json # Added for JSON parsing in sidebar

# This adds the parent directory (your project root) to Python's search path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# --- Imports ---
import streamlit as st
from transformers import pipeline
from models.classifier import get_risk_assessment
from models.NER import get_entities
from db import save_log, load_logs, delete_log, delete_all_logs
from datetime import datetime

# --- CONFIGURATION ---
ENTITY_COLORS = {
    "LOC": "#0068C9",       # Location
    "PER": "#FFA500",       # Person
    "ORG": "#2E8B57",       # Organization
    "WEAPON": "#FF4B4B",    # Custom/Example
    "DEFAULT": "#696969"
}

# --- MODEL LOADING ---
@st.cache_resource
def load_models():
    """Loads and caches the NLP models."""
    ner_pipeline = pipeline("ner", model="Davlan/xlm-roberta-base-ner-hrl", aggregation_strategy="simple")
    classifier_pipeline = pipeline(
        "zero-shot-classification", 
        model="joeddav/xlm-roberta-large-xnli"
    )
    return ner_pipeline, classifier_pipeline

# --- CORE APP LOGIC ---
def analyze_text(text: str) -> dict:
    """Analyzes text by calling the separate model functions."""
    ner_model, classifier_model = load_models()
    risk_level, risk_details = get_risk_assessment(text, classifier_model)
    entities = get_entities(text, ner_model)
    
    return {
        "risk_level": risk_level,
        "risk_details": risk_details,
        "entities": entities
    }

# --- ENTITY RENDERING ---
def render_entities(entities: list):
    """Generates and displays styled HTML for detected entities."""
    if not entities:
        st.info("No entities were detected in the text.")
        return
        
    entity_html = ""
    for entity, label in entities:
        color = ENTITY_COLORS.get(label.upper(), ENTITY_COLORS["DEFAULT"])
        entity_html += f"""
        <span style="display: inline-block; margin: 5px; padding: 6px 12px; border: 1px solid {color}; border-radius: 15px;">
            {entity}
            <span style="color: {color}; font-weight: bold; margin-left: 6px;">{label}</span>
        </span>
        """
    st.markdown(entity_html, unsafe_allow_html=True)

# --- RISK LEVEL STYLING ---
def get_risk_styling(risk_level: str) -> dict:
    """Returns the appropriate styling for each risk level."""
    risk_level_lower = risk_level.lower()
    
    if "critical" in risk_level_lower:
        return {
            "color": "red",
            "text": "High Threat Potential",
            "delta_color": "inverse"
        }
    elif "suspicious" in risk_level_lower:
        return {
            "color": "orange",
            "text": "Suspicious Activity",
            "delta_color": "normal"
        }
    else:  # Benign
        return {
            "color": "green",
            "text": "Low Threat Potential",
            "delta_color": "normal"
        }

# --- MAIN APP ---
st.set_page_config(page_title="Threat Classifier", page_icon="🚨", layout="wide")
st.title("🚨 Threat Intelligence Classifier")
st.markdown("Upload a text file to analyze content, identify entities, and assess the risk level.")
st.divider()

# --- SIDEBAR ---
with st.sidebar:
    st.header("📜 Past Analyses")
    logs = load_logs(limit=5)  # fetch last 5 logs
    if logs:
        for log in logs:
            # Get the first entity for the title, or use a default if no entities
            first_entity = "No Entities"
            if log["entities"]:
                # Parse the entities JSON string and get the first entity
                try:
                    entities_list = json.loads(log["entities"]) if isinstance(log["entities"], str) else log["entities"]
                    if entities_list and len(entities_list) > 0:
                        first_entity = entities_list[0][0]  # Get the entity name (first element of first tuple)
                except:
                    first_entity = "Error"
            
            with st.expander(f"🔍 {first_entity} | {log['analysis']}"):
                st.write("**Content:**", log["text"][:200] + "...")
                st.write("**Entities:**", log["entities"])
                
                # Delete button for individual log
                col1, col2 = st.columns([3, 1])
                with col2:
                    if st.button("🗑️", key=f"delete_{log['id']}", help="Delete this log entry"):
                        delete_log(log['id'])
                        st.rerun()
        
        # Delete All button at the bottom
        st.divider()
        if st.button("🗑️ Delete All History", type="secondary", use_container_width=True):
            # Confirmation dialog
            if st.session_state.get('confirm_delete_all', False):
                delete_all_logs()
                st.session_state.confirm_delete_all = False
                st.rerun()
            else:
                st.session_state.confirm_delete_all = True
                st.warning("⚠️ Click again to confirm deletion of ALL history")
    else:
        st.info("No logs yet. Upload a file to see results here.")

# --- FILE UPLOAD ---
with st.container(border=True):
    uploaded_file = st.file_uploader(
        "**Upload a document for analysis**", type=["txt"], help="Only .txt files are supported."
    )

if uploaded_file is not None:
    text = uploaded_file.read().decode("utf-8")

    with st.spinner('Analyzing text...'):
        analysis_results = analyze_text(text)

    # Save results to DB
    save_log(
        text=text,
        analysis=analysis_results["risk_level"],
        entities=analysis_results["entities"]
    )

    st.divider()
    col_text, col_analysis = st.columns(2, gap="large")

    with col_text:
        st.subheader("📄 Document Content")
        with st.container(height=350, border=True):
            st.write(text)

    with col_analysis:
        st.subheader("📊 Analysis Results")
        risk_styling = get_risk_styling(analysis_results["risk_level"])
        
        # Custom risk level display with dynamic styling
        st.markdown(f"""
        <div style="text-align: center; padding: 20px; border: 2px solid {risk_styling['color']}; border-radius: 10px; background-color: {risk_styling['color']}15;">
            <h2 style="color: {risk_styling['color']}; margin: 0;">{analysis_results["risk_level"]}</h2>
            <p style="color: {risk_styling['color']}; font-weight: bold; margin: 5px 0;">{risk_styling['text']}</p>
            <p style="color: #666; font-size: 14px; margin: 0;">{analysis_results["risk_details"]}</p>
        </div>
        """, unsafe_allow_html=True)
        
        st.divider()
        st.subheader("🔍 Detected Entities")
        render_entities(analysis_results["entities"])
else:
    st.info("👋 Welcome! Please upload a file to begin the analysis.")
