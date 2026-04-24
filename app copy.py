import os
import json
import requests
import pandas as pd
import streamlit as st

# ============================================================
# CONFIG — API
# ============================================================
if 'API_URI' in os.environ:
    BASE_URI = st.secrets[os.environ.get('API_URI')]
else:
    BASE_URI = st.secrets['cloud_api_uri']

BASE_URI = BASE_URI if BASE_URI.endswith('/') else BASE_URI + '/'
url = BASE_URI + 'predict'

# ============================================================
# CONFIG — FEATURE MEDIANS
# (hardcoded from training data — update if model is retrained)
# ============================================================
FEATURE_MEDIANS = {
    "vo2_max": 45.2,
    "resting_heart_rate_bpm": 68.0,
    "recovery_score": 6.0,
    "nutrition_score": 5.1
}

# ============================================================
# PAGE SETUP
# ============================================================
st.set_page_config(page_title="MarathonIQ", layout="wide")
st.title("🏃 MarathonIQ")
st.subheader("What actually predicts your marathon time?")
st.markdown("---")

# ============================================================
# SECTION 1 — USER INPUTS
# ============================================================
st.header("Your Training Profile")

# --- MUST HAVE ---
st.subheader("Required")
col1, col2 = st.columns(2)

with col1:
    age = st.slider("Age", 18, 75, 35)
    running_experience_months = st.slider("Running Experience (months)", 0, 240, 24)
    weekly_mileage_km = st.slider("Weekly Mileage (km)", 0, 150, 40)

with col2:
    injury_count = st.slider("Injuries this training cycle", 0, 10, 0)
    injury_severity = st.selectbox(
        "Injury Severity",
        options=[0, 1, 2, 3],
        format_func=lambda x: {0: "None", 1: "Minor",
                                2: "Moderate", 3: "Severe"}[x]
    )
    course_difficulty = st.selectbox(
        "Course Difficulty",
        options=[1, 2, 3],
        format_func=lambda x: {1: "Flat", 2: "Mixed", 3: "Hilly"}[x]
    )

# --- NICE TO HAVE ---
with st.expander("➕ Improve your prediction (optional)"):
    st.caption("These inputs are optional — we'll estimate them if left at 0")

    col3, col4 = st.columns(2)

    with col3:
        vo2_max = st.slider("VO2 Max", 0.0, 80.0, 0.0)
        resting_heart_rate = st.slider("Resting Heart Rate (bpm)", 0, 100, 0)
        recovery_score = st.slider("Recovery Score (1-10)", 0.0, 10.0, 0.0)
        nutrition_score = st.slider("Nutrition Score (1-10)", 0.0, 10.0, 0.0)

    with col4:
        previous_marathon_count = st.slider("Previous Marathons", 0, 20, 0)
        run_club_attendance = st.slider("Run Club Attendance (%)", 0, 100, 0)
        marathon_weather = st.selectbox(
            "Race Day Weather",
            options=["Neutral", "Cold", "Hot", "Rainy", "Windy"]
        )

# ============================================================
# SECTION 2 — IMPUTATION
# ============================================================
def impute_features(user_input: dict, marathon_weather: str) -> dict:

    # Median imputation — health metrics
    for col, median in FEATURE_MEDIANS.items():
        if user_input.get(col, 0) == 0:
            user_input[col] = median

    # Zero imputation — count/behavioural
    user_input['previous_marathon_count'] = user_input.get('previous_marathon_count', 0)
    user_input['run_club_attendance_rate'] = user_input.get('run_club_attendance_rate', 0)

    # Weather OHE
    user_input['marathon_weather_Cold']  = 1 if marathon_weather == 'Cold'  else 0
    user_input['marathon_weather_Hot']   = 1 if marathon_weather == 'Hot'   else 0
    user_input['marathon_weather_Rainy'] = 1 if marathon_weather == 'Rainy' else 0
    user_input['marathon_weather_Windy'] = 1 if marathon_weather == 'Windy' else 0

    return user_input

# Build feature vector
user_input = {
    'age':                        age,
    'running_experience_months':  running_experience_months,
    'weekly_mileage_km':          weekly_mileage_km,
    'injury_count':               injury_count,
    'injury_severity':            injury_severity,
    'course_difficulty':          course_difficulty,
    'vo2_max':                    vo2_max,
    'resting_heart_rate_bpm':     resting_heart_rate,
    'recovery_score':             recovery_score,
    'nutrition_score':            nutrition_score,
    'previous_marathon_count':    previous_marathon_count,
    'run_club_attendance_rate':   run_club_attendance,
}

feature_vector = impute_features(user_input, marathon_weather)

# ============================================================
# SECTION 3 — API CALL + PREDICTION
# ============================================================
st.markdown("---")

if st.button("🏁 Predict My Finish Time"):

    with st.spinner("Calculating..."):
        response = requests.get(url, params=feature_vector)

    if response.status_code == 200:
        result = response.json()
        prediction = result.get('prediction', None)

        if prediction:
            hours   = int(prediction // 60)
            minutes = int(prediction % 60)

            # ============================================================
            # SECTION 4 — DISPLAY (teammate builds visualisation here)
            # ============================================================
            st.markdown("---")
            st.metric(
                label="Predicted Finish Time",
                value=f"{hours}h {minutes:02d}min"
            )

            # TODO: SHAP waterfall chart
            st.info("📊 Feature breakdown — coming soon")

    else:
        st.error(f"API error: {response.status_code}")

    # Debug — remove before Demo Day
    with st.expander("🔍 Debug — Feature Vector"):
        st.json(feature_vector)