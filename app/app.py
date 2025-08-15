import streamlit as st
import time # Imported to simulate model processing time

# --- CONFIGURATION ---
# Centralize entity color mapping for easy updates
ENTITY_COLORS = {
    "LOCATION": "#0068C9",
    "WEAPON": "#FF4B4B",
    "ORGANIZATION": "#2E8B57",
    "PERSON": "#FFA500",
    # Add other entity types and their colors here
    "DEFAULT": "#696969"  # A fallback color
}

# --- MODEL LOGIC (Placeholder Functions) ---

@st.cache_data # Cache the analysis to avoid re-running on the same text
def analyze_text(text: str) -> dict:
    """
    A placeholder function to simulate NLP model analysis.
    
    In the future, this is where you'll integrate your actual NER
    and classification models.

    Args:
        text (str): The input text from the uploaded file.

    Returns:
        dict: A dictionary containing the analysis results.
    """
    # Simulate a delay for model processing
    time.sleep(2) 
    
    # --- Replace this dummy data with your model's output ---
    risk_level = "Critical"
    risk_details = "High Threat Detected"
    entities = [("Delhi", "LOCATION"), ("AK-47", "WEAPON")]
    # --- End of dummy data ---

    return {
        "risk_level": risk_level,
        "risk_details": risk_details,
        "entities": entities
    }


# --- UI RENDERING ---

def render_entities(entities: list):
    """Generates and displays styled HTML for detected entities."""
    entity_html = ""
    for entity, label in entities:
        # Use the color from the config, with a fallback for unknown labels
        color = ENTITY_COLORS.get(label.upper(), ENTITY_COLORS["DEFAULT"])
        entity_html += f"""
        <span style="display: inline-block; margin: 5px; padding: 6px 12px; background-color: transparent; border: 1px solid {color}; border-radius: 15px; font-size: 1em;">
            {entity}
            <span style="color: {color}; font-weight: bold; margin-left: 6px;">{label}</span>
        </span>
        """
    st.markdown(entity_html, unsafe_allow_html=True)


# --- MAIN APP LAYOUT ---

# Set page config once at the top
st.set_page_config(page_title="Threat Classifier", page_icon="🚨", layout="wide")

# Header
st.title("🚨 Threat Intelligence Classifier")
st.markdown("Upload a text file to analyze its content, identify key entities, and assess the risk level.")
st.divider()

# File Uploader
with st.container(border=True):
    uploaded_file = st.file_uploader(
        "**Upload a document for analysis**",
        type=["txt"],
        help="Only .txt files are supported at the moment."
    )

# Analysis & Display
if uploaded_file is not None:
    text = uploaded_file.read().decode("utf-8")

    # Show a spinner while the "model" is processing the text
    with st.spinner('Analyzing text... This may take a moment.'):
        analysis_results = analyze_text(text)

    st.divider()

    col_text, col_analysis = st.columns(2, gap="large")

    # Left Column: Document Content
    with col_text:
        st.subheader("📄 Document Content")
        with st.container(height=350, border=True):
            st.write(text)

    # Right Column: Analysis Results
    with col_analysis:
        st.subheader("📊 Analysis Results")

        # Display risk level from the analysis results
        st.metric(
            label="**Risk Level**",
            value=analysis_results["risk_level"],
            delta=analysis_results["risk_details"],
            delta_color="inverse"
        )

        st.divider()

        st.subheader("🔍 Detected Entities")
        
        # Render entities using the dedicated function
        render_entities(analysis_results["entities"])

else:
    # A welcoming message when no file is uploaded
    st.info("👋 Welcome! Please upload a file to begin the analysis.")