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
from db import save_log, load_logs, load_logs_by_role, delete_log, delete_all_logs
from datetime import datetime

# --- CONFIGURATION ---
ENTITY_COLORS = {
    "LOC": "#0068C9",       # Location
    "PER": "#FFA500",       # Person
    "ORG": "#2E8B57",       # Organization
    "WEAPON": "#FF4B4B",    # Custom/Example
    "DEFAULT": "#696969"
}

# --- RBAC CONFIGURATION ---
ROLES = {
    "Observer": {
        "level": 1,
        "description": "Lowest clearance - Risk level only",
        "color": "#FF6B6B"
    },
    "Analyst": {
        "level": 2,
        "description": "Mid clearance - Content + Risk level",
        "color": "#4ECDC4"
    },
    "Commander": {
        "level": 3,
        "description": "High clearance - Content + Risk + Entities",
        "color": "#45B7D1"
    },
    "Operative": {
        "level": 4,
        "description": "Top clearance - Full access",
        "color": "#96CEB4"
    }
}

# --- RBAC HELPER FUNCTIONS ---
def filter_output_by_role(role: str, content: str, entities: list, risk_details: str) -> dict:
    """
    Filters analysis output based on user role and clearance level.
    """
    role_config = ROLES.get(role, ROLES["Observer"])
    level = role_config["level"]
    
    filtered_output = {
        "content": content,
        "entities": entities,
        "risk_details": risk_details
    }
    
    # Observer (Level 1) - Only risk level
    if level == 1:
        filtered_output["content"] = "[REDACTED]"
        filtered_output["entities"] = []
        filtered_output["risk_details"] = "[REDACTED]"
    
    # Analyst (Level 2) - Content + Risk level, no entities
    elif level == 2:
        filtered_output["entities"] = []
        filtered_output["risk_details"] = "[REDACTED]"
    
    # Commander (Level 3) - Content + Risk + Entities, no explanations
    elif level == 3:
        filtered_output["risk_details"] = "[REDACTED]"
    
    # Operative (Level 4) - Full access (no filtering)
    
    return filtered_output

def render_role_badge(role: str):
    """Renders a styled role badge."""
    role_config = ROLES.get(role, ROLES["Observer"])
    st.markdown(f"""
    <div style="display: inline-block; padding: 8px 16px; background-color: {role_config['color']}20; 
                border: 2px solid {role_config['color']}; border-radius: 20px; margin-bottom: 20px;">
        <span style="color: {role_config['color']}; font-weight: bold; font-size: 14px;">
            🔐 {role} - {role_config['description']}
        </span>
    </div>
    """, unsafe_allow_html=True)

def render_entities_by_role(entities: list, role: str):
    """Renders entities based on user role clearance."""
    role_config = ROLES.get(role, ROLES["Observer"])
    level = role_config["level"]
    
    if not entities:
        st.info("No entities were detected in the text.")
        return
    
    if level <= 1:  # Observer - no entities
        st.info("Entity information is not available at your clearance level.")
        return
    
    if level == 2:  # Analyst - show entity count but not names
        st.info(f"Detected {len(entities)} entities. Entity details require higher clearance.")
        return
    
    # Commander and Operative - show full entities
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
    risk_level, risk_details, evidence = get_risk_assessment(text, classifier_model)
    entities = get_entities(text, ner_model)
    
    return {
        "risk_level": risk_level,
        "risk_details": risk_details,
        "evidence": evidence,
        "entities": entities
    }

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

# --- ROLE SELECTION ---
if "role" not in st.session_state:
    st.session_state.role = None

role_col1, role_col2 = st.columns([2, 1])
with role_col1:
    if st.session_state.role is None:
        selected_role = st.selectbox(
            "**Select Your Security Clearance Level**",
            options=list(ROLES.keys()),
            help="Choose your role to determine what information you can access"
        )
        if st.button("🔐 Confirm Role Selection", type="primary"):
            st.session_state.role = selected_role
            st.rerun()
    else:
        # Role is locked after selection
        st.selectbox(
            "**Security Clearance Level**",
            options=[st.session_state.role],
            disabled=True,
            help="Role locked for this session"
        )

with role_col2:
    if st.session_state.role:
        role_config = ROLES.get(st.session_state.role, ROLES["Observer"])
        st.markdown(f"""
        <div style="padding: 10px; background-color: {role_config['color']}15; 
                    border: 1px solid {role_config['color']}; border-radius: 8px;">
            <p style="margin: 0; font-size: 12px; color: {role_config['color']};">
                <strong>Clearance Level {role_config['level']}</strong><br>
                {role_config['description']}
            </p>
        </div>
        """, unsafe_allow_html=True)

# --- SIDEBAR ---
with st.sidebar:
    st.header("📜 Past Analyses")
    
    # Only show logs if user has Operative clearance
    if st.session_state.role == "Operative":
        logs = load_logs_by_role(st.session_state.role, limit=5)  # fetch last 5 logs
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
    else:
        # Show limited log information for non-Operative roles
        logs = load_logs_by_role(st.session_state.role, limit=3)
        if logs:
            st.info(f"📊 Recent Analysis Count: {len(logs)}")
            st.info("🔒 Full analysis history requires Operative clearance level.")
        else:
            st.info("🔒 Access to analysis history requires Operative clearance level.")

# --- FILE UPLOAD ---
if st.session_state.role is None:
    st.warning("⚠️ Please select your security clearance level before proceeding.")
    st.stop()

with st.container(border=True):
    uploaded_file = st.file_uploader(
        "**Upload a document for analysis**", type=["txt"], help="Only .txt files are supported."
    )

if uploaded_file is not None:
    text = uploaded_file.read().decode("utf-8")

    with st.spinner('Analyzing text...'):
        analysis_results = analyze_text(text)

    # Save results to DB (only if Operative clearance)
    if st.session_state.role == "Operative":
        save_log(
            text=text,
            analysis=analysis_results["risk_level"],
            entities=analysis_results["entities"]
        )

    st.divider()
    
    # Display role badge
    render_role_badge(st.session_state.role)
    
    # Filter output based on role
    filtered_output = filter_output_by_role(
        st.session_state.role,
        text,
        analysis_results["entities"],
        analysis_results["risk_details"]
    )
    
    col_text, col_analysis = st.columns(2, gap="large")

    with col_text:
        st.subheader("📄 Document Content")
        with st.container(height=350, border=True):
            if filtered_output["content"] == "[REDACTED]":
                st.warning("🔒 Document content is not available at your clearance level.")
            else:
                st.write(filtered_output["content"])

    with col_analysis:
        st.subheader("📊 Analysis Results")
        risk_styling = get_risk_styling(analysis_results["risk_level"])
        
        # Custom risk level display with dynamic styling
        st.markdown(f"""
        <div style="text-align: center; padding: 20px; border: 2px solid {risk_styling['color']}; border-radius: 10px; background-color: {risk_styling['color']}15;">
            <h2 style="color: {risk_styling['color']}; margin: 0;">{analysis_results["risk_level"]}</h2>
            <p style="color: {risk_styling['color']}; font-weight: bold; margin: 5px 0;">{risk_styling['text']}</p>
            <p style="color: #666; font-size: 14px; margin: 0;">{filtered_output["risk_details"]}</p>
        </div>
        """, unsafe_allow_html=True)
        
        st.divider()
        st.subheader("🔍 Detected Entities")
        render_entities_by_role(analysis_results["entities"], st.session_state.role)
else:
    if st.session_state.role:
        st.info("👋 Ready for analysis! Please upload a file to begin.")
    else:
        st.info("👋 Welcome! Please select your security clearance level to begin.")
