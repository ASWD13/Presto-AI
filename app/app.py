import sys
import os
import json
import pandas as pd
import plotly.express as px
from datetime import datetime

# This adds the parent directory (your project root) to Python's search path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# --- Imports ---
import streamlit as st
from transformers import pipeline

# IMPORTANT: These imports will now connect to your REAL db.py file
from models.classifier import get_risk_assessment
from models.NER import get_entities
from db import save_log, load_logs_by_role, delete_log, delete_all_logs, load_all_logs 

# --- CONFIGURATION ---
ENTITY_COLORS = {
    "LOC": "#0068C9",      # Location
    "PER": "#FFA500",      # Person
    "ORG": "#2E8B57",      # Organization
    "WEAPON": "#FF4B4B",  # Custom/Example
    "DEFAULT": "#696969"
}

# --- RBAC CONFIGURATION ---
ROLES = {
    "Observer": { "level": 1, "description": "Lowest clearance - Risk level only", "color": "#FF6B6B" },
    "Analyst": { "level": 2, "description": "Mid clearance - Content + Risk level", "color": "#4ECDC4" },
    "Commander": { "level": 3, "description": "High clearance - Content + Risk + Entities", "color": "#45B7D1" },
    "Operative": { "level": 4, "description": "Top clearance - Full access", "color": "#96CEB4" }
}

# --- SVG ICONS ---
def svg_icon(name: str, size: int = 18, stroke: str = "#fff", fill: str = "none") -> str:
    pre = f'<svg xmlns="http://www.w3.org/2000/svg" width="{size}" height="{size}" viewBox="0 0 24 24" fill="{fill}" stroke="{stroke}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="vertical-align: -3px; margin-right:6px;">'
    post = "</svg>"
    paths = {
        "lock": ['<rect x="4" y="10" width="16" height="10" rx="2" ry="2"></rect>', '<path d="M8 10V7a4 4 0 0 1 8 0v3"></path>', '<circle cx="12" cy="15" r="1"></circle>'],
        "file-text": ['<path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path>', '<path d="M14 2v6h6"></path>', '<path d="M16 13H8"></path>', '<path d="M16 17H8"></path>'],
        "search": ['<circle cx="11" cy="11" r="7"></circle>', '<line x1="21" y1="21" x2="16.65" y2="16.65"></line>'],
        "trash": ['<polyline points="3 6 5 6 21 6"></polyline>', '<path d="M19 6l-1 14a2 2 0 0 1-2 2H8a2 2 0 0 1-2-2L5 6"></path>', '<path d="M10 11v6"></path>', '<path d="M14 11v6"></path>', '<path d="M9 6V4a2 2 0 0 1 2-2h2a2 2 0 0 1 2 2v2"></path>'],
        "alert": ['<path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"></path>', '<line x1="12" y1="9" x2="12" y2="13"></line>', '<line x1="12" y1="17" x2="12" y2="17"></line>'],
        "siren": ['<rect x="5" y="9" width="14" height="10" rx="2" ry="2"></rect>', '<path d="M7 9a5 5 0 0 1 10 0"></path>', '<line x1="2" y1="9" x2="6" y2="9"></line>', '<line x1="18" y1="9" x2="22" y2="9"></line>', '<line x1="12" y1="2" x2="12" y2="5"></line>'],
        "bar-chart": ['<line x1="3" y1="20" x2="21" y2="20"></line>', '<rect x="6" y="12" width="3" height="8"></rect>', '<rect x="11" y="8" width="3" height="12"></rect>', '<rect x="16" y="4" width="3" height="16"></rect>'],
        "tags": ['<path d="M20.59 13.41l-7.17 7.17a2 2 0 0 1-2.83 0L3 13.99V7a2 2 0 0 1 2-2h7l7.59 7.59a2 2 0 0 1 0 2.82z"></path>', '<circle cx="7.5" cy="7.5" r="1.5"></circle>'],
        "dashboard": ['<rect x="3" y="3" width="7" height="9"></rect>', '<rect x="14" y="3" width="7" height="5"></rect>', '<rect x="14" y="12" width="7" height="9"></rect>', '<rect x="3" y="16" width="7" height="5"></rect>']
    }
    content = "".join(paths.get(name, []))
    return pre + content + post

# --- RBAC HELPER FUNCTIONS ---
def filter_output_by_role(role: str, content: str, entities: list, risk_details: str) -> dict:
    role_config = ROLES.get(role, ROLES["Observer"])
    level = role_config["level"]
    filtered_output = {"content": content, "entities": entities, "risk_details": risk_details}
    if level == 1:
        filtered_output["content"] = "[REDACTED]"
        filtered_output["entities"] = []
        filtered_output["risk_details"] = "[REDACTED]"
    elif level == 2:
        filtered_output["entities"] = []
        filtered_output["risk_details"] = "[REDACTED]"
    elif level == 3:
        filtered_output["risk_details"] = "[REDACTED]"
    return filtered_output

def render_role_badge(role: str):
    role_config = ROLES.get(role, ROLES["Observer"])
    st.markdown(f"""
    <div style="display: inline-block; padding: 8px 16px; background-color: {role_config['color']}20; 
                 border: 2px solid {role_config['color']}; border-radius: 20px; margin-bottom: 20px;">
        <span style="color: {role_config['color']}; font-weight: bold; font-size: 14px;">
            {svg_icon('lock', 16, role_config['color'])}{role} - {role_config['description']}
        </span>
    </div>
    """, unsafe_allow_html=True)

def render_entities_by_role(entities: list, role: str):
    role_config = ROLES.get(role, ROLES["Observer"])
    level = role_config["level"]
    if not entities:
        st.info("No entities were detected in the text.")
        return
    if level <= 1:
        st.info("Entity information is not available at your clearance level.")
        return
    if level == 2:
        st.info(f"Detected {len(entities)} entities. Entity details require higher clearance.")
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

# --- MODEL LOADING ---
@st.cache_resource(show_spinner=False)
def load_models():
    with st.spinner("Loading AI models..."):
        ner_pipeline = pipeline("ner", model="Davlan/distilbert-base-multilingual-cased-ner-hrl", aggregation_strategy="simple")
        classifier_pipeline = pipeline("zero-shot-classification", model="valhalla/distilbart-mnli-12-1")
    return ner_pipeline, classifier_pipeline

# --- CORE APP LOGIC ---
def analyze_text(text: str) -> dict:
    # Use cached models from session state if available
    if not st.session_state.models_loaded:
        ner_model, classifier_model = load_models()
        st.session_state.ner_model = ner_model
        st.session_state.classifier_model = classifier_model
        st.session_state.models_loaded = True
    else:
        ner_model = st.session_state.ner_model
        classifier_model = st.session_state.classifier_model
    
    # Process both tasks sequentially for now (can be optimized later)
    risk_level, risk_details, evidence = get_risk_assessment(text, classifier_model)
    entities = get_entities(text, ner_model)
    
    return {"risk_level": risk_level, "risk_details": risk_details, "evidence": evidence, "entities": entities}

def get_risk_styling(risk_level: str) -> dict:
    risk_level_lower = risk_level.lower()
    if "critical" in risk_level_lower:
        return {"color": "red", "text": "High Threat Potential", "delta_color": "inverse"}
    elif "suspicious" in risk_level_lower:
        return {"color": "orange", "text": "Suspicious Activity", "delta_color": "normal"}
    else:
        return {"color": "green", "text": "Low Threat Potential", "delta_color": "normal"}

# --- DASHBOARD RENDERING FUNCTION ---
def render_dashboard():
    st.markdown(f"### {svg_icon('dashboard', 20)} System-Wide Statistics", unsafe_allow_html=True)
    logs = load_all_logs()
    if not logs:
        st.warning("No analysis data found in the database. The dashboard will be empty.")
        return
    df = pd.DataFrame(logs)
    if 'created_at' not in df.columns or df['created_at'].isnull().all():
        st.warning("Dashboard requires a 'created_at' column with valid data.")
        return
    df['created_at'] = pd.to_datetime(df['created_at'])
    df['analysis_date'] = df['created_at'].dt.date
    def parse_entities(entities_str):
        try:
            return json.loads(entities_str) if isinstance(entities_str, str) else entities_str
        except (json.JSONDecodeError, TypeError):
            return []
    df['entities_list'] = df['entities'].apply(parse_entities)
    total_analyses = len(df)
    critical_analyses = len(df[df['analysis'] == 'Critical'])
    most_recent_analysis_time = df['created_at'].max().strftime("%Y-%m-%d %H:%M:%S")
    m1, m2, m3 = st.columns(3)
    m1.metric(label="Total Analyses Conducted", value=total_analyses)
    m2.metric(label="Critical Risk Detections", value=critical_analyses)
    m3.metric(label="Last Analysis Time", value=most_recent_analysis_time)
    st.divider()
    c1, c2 = st.columns(2, gap="large")
    with c1:
        st.markdown("**Risk Level Distribution**")
        risk_counts = df['analysis'].value_counts()
        if not risk_counts.empty:
            RISK_COLOR_MAP = {"Critical": "#FF4B4B", "Suspicious": "#FFD700", "Benign": "#2E8B57"}
            risk_df = risk_counts.reset_index()
            risk_df.columns = ['analysis', 'count']
            risk_df['color'] = risk_df['analysis'].map(RISK_COLOR_MAP)
            
            # --- FIX APPLIED HERE: Sort data to match chart's alphabetical sorting ---
            risk_df = risk_df.sort_values('analysis')
            
            st.bar_chart(risk_df, x='analysis', y='count', color='color')
        else:
            st.info("No risk data to display.")
    with c2:
        st.markdown("**Detected Entity Types**")
        all_entities = [entity[1] for sublist in df['entities_list'].dropna() for entity in sublist]
        if all_entities:
            entity_counts = pd.Series(all_entities).value_counts()
            fig = px.pie(entity_counts, values=entity_counts.values, names=entity_counts.index, hole=.3, color_discrete_map=ENTITY_COLORS)
            fig.update_layout(showlegend=False)
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No entities have been detected yet.")

# --- MAIN APP ---
st.set_page_config(page_title="Presto", page_icon="🚨")

# Initialize session state for models
if "models_loaded" not in st.session_state:
    st.session_state.models_loaded = False
if "ner_model" not in st.session_state:
    st.session_state.ner_model = None
if "classifier_model" not in st.session_state:
    st.session_state.classifier_model = None

st.markdown(f"""
<div style="display:flex; align-items:center; gap:10px;">
  {svg_icon('siren', 46, '#c1121f')}
  <h1 style="margin:0;">Threat Intelligence Classifier</h1>
</div>
<p>Upload a text file to analyze content, identify entities, and assess the risk level.</p>
""", unsafe_allow_html=True)
st.divider()
if "role" not in st.session_state:
    st.session_state.role = None
if st.session_state.role is None:
    _, center_col, _ = st.columns([1, 1.5, 1])
    with center_col:
        selected_role = st.selectbox("**Select Your Security Clearance Level**", options=list(ROLES.keys()), help="Choose your role to determine what information you can access")
        if st.button("Confirm Role Selection", type="primary", use_container_width=True):
            st.session_state.role = selected_role
            st.rerun()
else:
    role_col1, role_col2 = st.columns([2, 1])
    with role_col1:
        st.selectbox("**Security Clearance Level**", options=[st.session_state.role], disabled=True, help="Role locked for this session")
    with role_col2:
        role_config = ROLES.get(st.session_state.role, ROLES["Observer"])
        st.markdown(f"""
        <div style="padding: 10px; background-color: {role_config['color']}15; border: 1px solid {role_config['color']}; border-radius: 8px;">
            <p style="margin: 0; font-size: 12px; color: {role_config['color']};">
                <strong>Clearance Level {role_config['level']}</strong><br>
                {role_config['description']}
            </p>
        </div>
        """, unsafe_allow_html=True)

# --- SIDEBAR ---
with st.sidebar:
    st.markdown(f"### {svg_icon('file-text', 18)}Past Analyses", unsafe_allow_html=True)
    if st.session_state.role:
        if st.session_state.role == "Operative":
            logs = load_logs_by_role(st.session_state.role, limit=5)
            if logs:
                for log in logs:
                    first_entity = "No Entities"
                    if log.get("entities"):
                        try:
                            entities_list = json.loads(log["entities"]) if isinstance(log["entities"], str) else log["entities"]
                            if entities_list: first_entity = entities_list[0][0]
                        except Exception:
                            first_entity = "Error"
                    expander_label = f"{first_entity} | {log.get('analysis', '')}"
                    with st.expander(expander_label):
                        st.markdown(f"""
                        <div style="padding:4px 0;">
                            <div><strong>Content:</strong> {(log.get("text","")[:200] + "...")}</div>
                            <div style="margin-top:4px;"><strong>Entities:</strong> {log.get("entities","[]")}</div>
                        </div>
                        """, unsafe_allow_html=True)
                        _, btn_col = st.columns([3, 1])
                        with btn_col:
                            if st.button("🗑️", key=f"delete_{log['id']}", help="Delete this log entry", use_container_width=True):
                                delete_log(log['id'])
                                st.rerun()
                st.divider()
                if st.button("🗑️ Delete All History", type="secondary", use_container_width=True):
                    if st.session_state.get('confirm_delete_all', False):
                        delete_all_logs()
                        st.session_state.confirm_delete_all = False
                        st.rerun()
                    else:
                        st.session_state.confirm_delete_all = True
                        st.warning("Click again to confirm deletion of ALL history")
            else:
                st.info("No logs yet. Upload a file to see results here.")
        else:
            logs = load_logs_by_role(st.session_state.role, limit=3)
            if logs:
                st.info(f"Recent Analysis Count: {len(logs)}")
                st.info("Full analysis history requires Operative clearance level.")
            else:
                st.info("Access to analysis history requires Operative clearance level.")

# --- MAIN CONTENT AREA ---
if st.session_state.role is None:
    st.warning("Please select your security clearance level before proceeding.")
    st.stop()
with st.container(border=True):
    st.markdown(f"**{svg_icon('file-text', 16)}Upload a document for analysis**", unsafe_allow_html=True)
    uploaded_file = st.file_uploader("", type=["txt"], help="Only .txt files are supported.")
if uploaded_file is not None:
    text = uploaded_file.read().decode("utf-8")
    with st.spinner('Analyzing text...'):
        analysis_results = analyze_text(text)
    if st.session_state.role == "Operative":
        save_log(text=text, analysis=analysis_results["risk_level"], entities=analysis_results["entities"])
    st.divider()
    render_role_badge(st.session_state.role)
    filtered_output = filter_output_by_role(st.session_state.role, text, analysis_results["entities"], analysis_results["risk_details"])
    analysis_tab, dashboard_tab = st.tabs(["🔍 Analysis Results", "📊 Dashboard"])
    with analysis_tab:
        col_text, col_analysis = st.columns(2, gap="large")
        with col_text:
            st.markdown(f"### {svg_icon('file-text', 18)}Document Content", unsafe_allow_html=True)
            with st.container(height=350, border=True):
                if filtered_output["content"] == "[REDACTED]":
                    st.warning("Document content is not available at your clearance level.")
                else:
                    st.write(filtered_output["content"])
        with col_analysis:
            st.markdown(f"### {svg_icon('bar-chart', 18)}Analysis Results", unsafe_allow_html=True)
            risk_styling = get_risk_styling(analysis_results["risk_level"])
            st.markdown(f"""
            <div style="text-align: center; padding: 20px; border: 2px solid {risk_styling['color']}; border-radius: 10px; background-color: {risk_styling['color']}15;">
                <h2 style="color: {risk_styling['color']}; margin: 0;">{analysis_results["risk_level"]}</h2>
                <p style="color: {risk_styling['color']}; font-weight: bold; margin: 5px 0;">{risk_styling['text']}</p>
                <p style="color: #666; font-size: 14px; margin: 0;">{filtered_output["risk_details"]}</p>
            </div>
            """, unsafe_allow_html=True)
            st.divider()
            st.markdown(f"### {svg_icon('tags', 18)}Detected Entities", unsafe_allow_html=True)
            render_entities_by_role(analysis_results["entities"], st.session_state.role)
    with dashboard_tab:
        render_dashboard()
else:
    if st.session_state.role:
        st.info("Ready for analysis! Please upload a file to begin.")
        st.markdown("---")
        render_dashboard()
    else:
        st.info("Welcome! Please select your security clearance level to begin.")