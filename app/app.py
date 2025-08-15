# Add this snippet to the top of app/app.py
import sys
import os

# This adds the parent directory (your project root) to Python's search path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# --- Now your regular imports will work ---
import streamlit as st
from transformers import pipeline
from models.classifier import get_risk_assessment
from models.NER import get_entities

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
    
    # --- THIS IS THE CHANGE ---
    # Load the zero-shot pipeline and a corresponding model
    classifier_pipeline = pipeline(
        "zero-shot-classification", 
        model="joeddav/xlm-roberta-large-xnli"
    )
    # --- END OF CHANGE ---

    return ner_pipeline, classifier_pipeline

# --- CORE APP LOGIC ---
def analyze_text(text: str) -> dict:
    """
    Analyzes text by calling the separate model functions.
    """
    ner_model, classifier_model = load_models()

    # Call the imported functions to get results
    risk_level, risk_details = get_risk_assessment(text, classifier_model)
    entities = get_entities(text, ner_model)
    
    return {
        "risk_level": risk_level,
        "risk_details": risk_details,
        "entities": entities
    }

# --- UI RENDERING ---
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

# --- MAIN APP LAYOUT ---
st.set_page_config(page_title="Threat Classifier", page_icon="🚨", layout="wide")

st.title("🚨 Threat Intelligence Classifier")
st.markdown("Powered by XLM-RoBERTa. Upload a text file to analyze content, identify entities, and assess the risk level.")
st.divider()

with st.container(border=True):
    uploaded_file = st.file_uploader(
        "**Upload a document for analysis**", type=["txt"], help="Only .txt files are supported."
    )

if uploaded_file is not None:
    text = uploaded_file.read().decode("utf-8")

    with st.spinner('Analyzing text with XLM-RoBERTa...'):
        analysis_results = analyze_text(text)

    st.divider()

    col_text, col_analysis = st.columns(2, gap="large")

    with col_text:
        st.subheader("📄 Document Content")
        with st.container(height=350, border=True):
            st.write(text)

    with col_analysis:
        st.subheader("📊 Analysis Results")
        st.metric(
            label="**Risk Level**",
            value=analysis_results["risk_level"],
            delta=analysis_results["risk_details"],
            delta_color="inverse"
        )
        st.divider()
        st.subheader("🔍 Detected Entities")
        render_entities(analysis_results["entities"])
else:
    st.info("👋 Welcome! Please upload a file to begin the analysis.")