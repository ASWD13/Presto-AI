# Presto: AI-Powered Threat Intelligence Classifier

Transform raw intercepted communications into actionable intelligence

Demo : https://prestoai.streamlit.app

## Project Overview

Presto is an intelligent threat classification and analysis platform for defense and security workflows.
It leverages transformer-based NLP to classify intercepted communications into Benign, Suspicious, or Critical, while Named Entity Recognition (NER) highlights key entities such as people, organizations, locations, and weapons.

With Role-Based Access Control (RBAC), Presto reveals information progressively based on clearance levels—supporting secure collaboration between Observers, Analysts, Commanders, and Operatives.

## Features

### AI-Powered Intelligence Processing

- **Risk Classification** — Categorizes documents into Benign, Suspicious, or Critical
- **Named Entity Recognition (NER)** — Extracts entities (people, places, weapons, organizations)
- **Multilingual Support** — Handles English, Hindi, and Hinglish
- **Context-Aware Views** — Output filtered according to user role

### Secure Role-Based Access Control (RBAC)
| Role | Access Level |
|------|--------------|
| Observer | Sees only the risk level |
| Analyst | Sees document + risk level |
| Commander | Sees document + risk + entities |
| Operative | Full access, including detailed risk notes and analysis history |

### Interactive Dashboard

- Upload .txt reports
- Real-time AI classification
- Color-coded risk visualization
- Entity chips with progressive disclosure

### Enterprise & Defense Ready

- Secure logging of past analyses
- RBAC aligned with defense workflows
- Scalable: plug in new models/data sources
- Future-proof: designed for integration with intel pipelines

## Project Structure

```
presto-threat-intelligence/
├─ app/
│  └─ main.py    # Streamlit UI + RBAC + orchestration
├─ models/
│  ├─ classifier.py    # get_risk_assessment()
│  └─ NER.py          # get_entities()
├─ db.py      # save_log, load_logs_by_role, delete_log, delete_all_logs
├─ requirements.txt
└─ README.md
```

## Models Used

- **Threat Classification**: joeddav/xlm-roberta-large-xnli
- **Named Entity Recognition**: Davlan/xlm-roberta-base-ner-hrl
- **Framework**: Hugging Face Transformers + Streamlit

## Installation & Setup

### Prerequisites

- Python 3.9+
- pip package manager

### Clone the Repository
```bash
git clone https://github.com/your-username/presto-threat-intelligence.git
cd presto-threat-intelligence
```

### Set Up Environment (recommended)
Create and activate a virtual environment:
```bash
python -m venv venv

# Mac/Linux
source venv/bin/activate

# Windows (Powershell)
venv\\Scripts\\Activate.ps1

# Windows (cmd)
venv\\Scripts\\activate
```

### Install Dependencies
```bash
pip install -r requirements.txt
```

### Start the Application
```bash
streamlit run app/main.py
```
The app will be available at: http://localhost:8501

## Quick Start Workflow

1. Select your role (Observer / Analyst / Commander / Operative)
2. Upload a .txt file with intercepted communication
3. Review AI results (risk level, entities, details per clearance)

## Role-based Output Matrix

| Role | Access |
|------|---------|
| Observer | Risk level only |
| Analyst | Risk + Document |
| Commander | Risk + Entities + Document |
| Operative | Full unrestricted view + Risk details + Logs |

## Usage Examples

### Classifying an Intercepted Report
1. Select a role
2. Upload a .txt input
3. Inspect:
   - Risk Level: Benign / Suspicious / Critical
   - Entities: PER / ORG / LOC / WEAPON (visibility depends on role)
   - Risk Details: reasoning/evidence (Operative only)

### Intelligence Log Management (Operative only)
- View recent analyses in the sidebar
- Delete an individual entry or clear all
- Use history to track threat trends over time

### RBAC Behavior (Detailed)
- Observer (L1) — Redacted: content, entities, risk details
- Analyst (L2) — Full content, no entities, risk details redacted
- Commander (L3) — Content + entities, risk details redacted
- Operative (L4) — No redactions; can view and manage logs

### Configuration Notes
- Caching: Models are cached with @st.cache_resource for faster reloads
- Entity Colors: Customizable via ENTITY_COLORS in the code
- SVG Icons: Lightweight inline SVGs for UI polish (no asset files needed)

## Technologies Used

### Backend Intelligence
- Hugging Face Transformers
  - joeddav/xlm-roberta-large-xnli → Threat Classification
  - Davlan/xlm-roberta-base-ner-hrl → Named Entity Recognition
- Python 3.9+
- SQLite (or swap with PostgreSQL/MongoDB)

### Frontend
- Streamlit — Interactive web dashboard
- Matplotlib — Risk visualization blocks (if/when used)

### Development Tools
- Virtualenv — Environment isolation
- Git & GitHub — Version control
- Pylint / Flake8 — Code quality

## Health Check & Troubleshooting

### Model download is slow / times out
Pre-download models with transformers and set HF_HOME cache.

### CUDA not found (optional)
Install CPU-only PyTorch or configure GPU per your environment.

### Streamlit not launching
Ensure you activated the virtual environment and installed requirements.

## Contributing

We welcome contributions to Presto!

### Getting Started
1. Fork the repository
2. Clone your fork locally
3. Create a feature branch
4. Install dependencies and run the app

### Development Workflow
- Branch Naming: feature/rbac-upgrade, fix/logging-bug
- Code Style: Follow PEP8 and run linting before commits
- Testing: Verify classification, RBAC, and logging with sample files
- Docs: Update README for user-impacting changes

### Pull Request Process
1. Write clear commit messages
2. Provide a detailed PR description
3. Add screenshots for UI changes
4. Ensure backward compatibility

## Links & Resources

- Documentation: Coming Soon
- Issues: Bug Reports (open issues in your GitHub repo)
- Discussions: Community Forum (planned)





*Presto – Turning intelligence into action, securely.*
