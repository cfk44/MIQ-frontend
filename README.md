# MIQ — Marathon IQ · Frontend

Streamlit frontend for [MarathonIQ](https://github.com/cfk44/MIQ-backend) — the intelligent marathon finish time predictor.

🏃 **[Try it live →](https://marathoniq.streamlit.app)**

---

## Overview

This repo contains the Streamlit UI for MIQ. It connects to the FastAPI backend deployed on GCP Cloud Run, sends a runner's training profile, and displays the predicted finish time alongside a SHAP waterfall chart showing the factors driving it.

For model details, architecture, and dataset information see the [backend repo →](https://github.com/cfk44/MIQ-backend)

---

## Branch Structure

| Branch | Description |
|---|---|
| `master` | Production — deployed to Streamlit Cloud |
| `design-upgrade-01` | Design upgrade from demo to production UI — documents the full design iteration |

The `design-upgrade-01` branch is preserved as a record of the design process: copy rework, theming, CSS architecture, component cleanup, and the move from a demo-grade UI to a production-ready interface.

---

## Design System

The production UI was redesigned from scratch in `design-upgrade-01`. Key decisions:

- **Aesthetic:** Aston Martin × Apple — clean, minimal, high contrast
- **Fonts:** Space Grotesk (body) + JetBrains Mono (labels, metrics, monospace elements)
- **Palette:** `#FAFAF7` background · `#004225` accent · `#0A0A0A` text
- **Theming:** `config.toml` sets Streamlit base theme; `style.css` handles all component-level overrides
- **Copy:** Mission-framing ("briefing", "mission profile") — purposeful but not overplayed

---

## Local Setup

**Prerequisites:** Python 3.10.6 via [pyenv](https://github.com/pyenv/pyenv)

```bash
# Clone and set up environment
git clone https://github.com/cfk44/MIQ_FrontEnd
cd MIQ_FrontEnd
pyenv virtualenv 3.10.6 MIQ-frontend
pyenv activate MIQ-frontend
pip install -r requirements.txt

# Set up secrets
cp .streamlit/secrets.toml.sample .streamlit/secrets.toml
# Edit secrets.toml and fill in your Cloud Run URL
```

---

## Running Locally

```bash
# Against local backend (uvicorn must be running on :8000)
make streamlit_local

# Against deployed Cloud Run backend
make streamlit_cloud
```

---

## Configuration & Secrets

All backend URLs live in one place: `.streamlit/secrets.toml` (local) or the Streamlit Cloud dashboard (deployed). Never committed.

```toml
local_api_uri = "http://127.0.0.1:8000"
cloud_api_uri = "YOUR_CLOUD_RUN_URL"
```

Resolution order in `app.py` (first match wins):

| Priority | Source | Used by |
|---|---|---|
| 1 | `API_URI` env var → key in `secrets.toml` | Makefile targets |
| 2 | `BASE_URI` env var → explicit URL | Ad-hoc shell testing |
| 3 | `st.secrets['cloud_api_uri']` (default) | Deployed Streamlit Cloud |

---

## Deployment (Streamlit Cloud)

1. Push to `master`
2. [share.streamlit.io](https://share.streamlit.io) → New app → connect `cfk44/MIQ_FrontEnd`
3. Set main file: `app.py`, branch: `master`
4. App settings → Secrets → paste:
```toml
cloud_api_uri = "YOUR_CLOUD_RUN_URL"
```
5. Deploy

---

## Related

- [Backend repo](https://github.com/cfk44/MIQ-backend)
- [Live app](https://marathoniq.streamlit.app)
