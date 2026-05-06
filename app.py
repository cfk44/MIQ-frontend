import streamlit as st

# ============================================================
# PAGE CONFIG — must be first Streamlit call
# ============================================================
st.set_page_config(page_title="MarathonIQ", layout="wide")

import requests
import os
import re
import shap
import matplotlib.pyplot as plt
from matplotlib.colors import to_rgb
import numpy as np

# ============================================================
# BACKEND URL SETUP
# ============================================================
# Resolution order (first match wins):
#   1. API_URI env var → key name to look up in .streamlit/secrets.toml
#                        (used by Makefile targets: streamlit_local, streamlit_cloud)
#   2. BASE_URI env var → explicit URL override
#                        (used for ad-hoc local testing via shell)
#   3. Default fallback → cloud_api_uri from secrets
#                        (used by deployed Streamlit Cloud app)

if 'API_URI' in os.environ:
    BASE_URI = st.secrets[os.environ['API_URI']]
elif 'BASE_URI' in os.environ:
    BASE_URI = os.environ.get('BASE_URI')
else:
    BASE_URI = st.secrets['cloud_api_uri']

# Normalize trailing slash and build prediction endpoint
BASE_URI = BASE_URI if BASE_URI.endswith('/') else BASE_URI + '/'
url_base = BASE_URI + 'predict'

# ============================================================
# STYLES
# ============================================================
with open('.streamlit/style.css') as f:
    st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)

# ============================================================
# HEADER
# ============================================================
st.markdown("""
    <div style="text-align: center; padding: 2rem 0 0.5rem 0;">
        <div style="
            font-family: 'JetBrains Mono', monospace;
            font-size: 4rem;
            font-weight: 500;
            letter-spacing: 0.05em;
            color: #0A0A0A;
            line-height: 1;
        ">MIQ</div>
        <div style="
            font-family: 'JetBrains Mono', monospace;
            font-size: 0.7rem;
            font-weight: 400;
            letter-spacing: 0.4em;
            text-transform: uppercase;
            color: #6A6A6A;
            margin-top: 0.5rem;
        ">Marathon · IQ</div>
    </div>
""", unsafe_allow_html=True)

st.markdown("""
    <div style="text-align: center; padding: 0.5rem 0 1rem 0;">
        <p style="color: black; font-size: 1.2rem;">
            Your Intelligent Quartermaster for running.<br>
            Brief MIQ on your marathon mission — get your predicted finish time and actionable insights on the factors driving it.
        </p>
    </div>
""", unsafe_allow_html=True)

st.markdown("---")

# ============================================================
# SECTION 1 — USER INPUTS
# ============================================================

st.header("Mission Profile")

# Default — overridden by radio below (fixes Pylance scope warning)
level = "Beginner"
level = st.radio("Experience Level", ["Beginner", "Expert"], horizontal=True, label_visibility="collapsed")

if level == "Beginner":
    url = url_base + '/general'

    st.subheader("Training Briefing")
    col1, col2 = st.columns(2)
    with col1:
        age = st.number_input("Age", 18, 100, 35)
        running_experience_months = st.number_input("Running Experience (months)", 0, 240, 0)
        weekly_mileage_km = st.number_input("Weekly Mileage (km/week)", 0, 200, 0)

    with col2:
        injury_count = st.number_input("Injuries this training cycle", 0, 10, 0)
        injury_severity = st.selectbox(
            "Injury Severity",
            options=[0, 1, 2, 3],
            format_func=lambda x: {0: "None", 1: "Minor", 2: "Moderate", 3: "Severe"}[x]
        )
        course_difficulty = st.selectbox(
            "Course Difficulty",
            options=[1, 2, 3],
            format_func=lambda x: {1: "Flat", 2: "Mixed", 3: "Hilly"}[x]
        )

    with st.expander("+ Expand Your Briefing (optional)"):
        st.caption("Optional inputs — if not provided, values will be automatically set to 0 or to the median of our dataset.")
        col3, col4 = st.columns(2)

        with col3:
            vo2_max = st.number_input("VO2 Max", 30, 85, 45)
            resting_heart_rate = st.number_input("Resting Heart Rate (bpm)", 30, 100, 68)
            previous_marathon_count = st.number_input("Previous Marathons", 0, 100, 0)

        with col4:
            recovery_score = st.selectbox(
                "Recovery Score - Nightly Recharge",
                options=[0, 3, 6, 7, 9],
                format_func=lambda x: {
                    0: "I don't track this",
                    3: "Low — fatigued",
                    6: "Moderate — somewhat tired",
                    7: "Good — well rested",
                    9: "High — fully recovered, ready to push hard"
                }[x]
            )
            run_club_attendance = st.selectbox(
                "Run Club Attendance",
                options=[12, 37, 62, 87],
                format_func=lambda x: {
                    12: "Never",
                    37: "Rarely — once a month or less",
                    62: "Sometimes — a few times a month",
                    87: "Often — weekly or more"
                }[x]
            )
            marathon_weather = st.selectbox(
                "Race Day Weather",
                options=["Neutral", "Cold", "Hot", "Rainy", "Windy"]
            )

    feature_vector = {
        'age':                        age,
        'running_experience_months':  running_experience_months,
        'weekly_mileage_km':          weekly_mileage_km,
        'injury_count':               injury_count,
        'injury_severity':            injury_severity,
        'course_difficulty':          course_difficulty,
        'vo2_max':                    vo2_max,
        'resting_heart_rate_bpm':     resting_heart_rate,
        'recovery_score':             recovery_score,
        'previous_marathon_count':    previous_marathon_count,
        'run_club_attendance_rate':   run_club_attendance,
        'marathon_weather_Cold':      1 if marathon_weather == 'Cold'  else 0,
        'marathon_weather_Hot':       1 if marathon_weather == 'Hot'   else 0,
        'marathon_weather_Rainy':     1 if marathon_weather == 'Rainy' else 0,
        'marathon_weather_Windy':     1 if marathon_weather == 'Windy' else 0,
    }

# ============================================================
# EXPERT MODE
# ============================================================
else:
    url = url_base + '/expert'

    st.subheader("Training Briefing")
    col1, col2 = st.columns(2)
    with col1:
        age = st.number_input("Age", 18, 100, 35)
        running_experience_months = st.number_input("Running Experience (months)", 0, 240, 0)
        weekly_mileage_km = st.number_input("Weekly Mileage (km/week)", 0, 200, 0)
        personal_best = st.text_input("Personal Best (HH:MM:SS)", value="00:00:00", max_chars=8)
        st.caption("ex: 03:45:30")
        if personal_best and len(personal_best) == 8:
            parts = personal_best.split(":")
            personal_best_minutes = int(parts[0]) * 60 + int(parts[1]) + round(int(parts[2]) / 60)
        else:
            personal_best_minutes = None

    with col2:
        injury_count = st.number_input("Injuries this training cycle", 0, 10, 0)
        injury_severity = st.selectbox(
            "Injury Severity",
            options=[0, 1, 2, 3],
            format_func=lambda x: {0: "None", 1: "Minor", 2: "Moderate", 3: "Severe"}[x]
        )
        course_difficulty = st.selectbox(
            "Course Difficulty",
            options=[1, 2, 3],
            format_func=lambda x: {1: "Flat", 2: "Mixed", 3: "Hilly"}[x]
        )

    with st.expander("+ Expand Your Briefing (optional)"):
        st.caption("Optional inputs — if not provided, values will be automatically set to 0 or to the median of our dataset.")
        col3, col4 = st.columns(2)

        with col3:
            vo2_max = st.number_input("VO2 Max", 30, 85, 45)
            resting_heart_rate = st.number_input("Resting Heart Rate (bpm)", 30, 100, 68)
            previous_marathon_count = st.number_input("Previous Marathons", 0, 100, 0)

        with col4:
            recovery_score = st.selectbox(
                "Recovery Score - Nightly Recharge",
                options=[0, 3, 6, 7, 9],
                format_func=lambda x: {
                    0: "I don't track this",
                    3: "Low — fatigued",
                    6: "Moderate — somewhat tired",
                    7: "Good — well rested",
                    9: "High — fully recovered"
                }[x]
            )
            run_club_attendance = st.selectbox(
                "Run Club Attendance",
                options=[12, 37, 62, 87],
                format_func=lambda x: {
                    12: "Never",
                    37: "Rarely — once a month or less",
                    62: "Sometimes — a few times a month",
                    87: "Often — weekly or more"
                }[x]
            )
            marathon_weather = st.selectbox(
                "Race Day Weather",
                options=["Neutral", "Cold", "Hot", "Rainy", "Windy"]
            )

    feature_vector = {
        'age':                        age,
        'running_experience_months':  running_experience_months,
        'weekly_mileage_km':          weekly_mileage_km,
        'personal_best_minutes':      personal_best_minutes,
        'injury_count':               injury_count,
        'injury_severity':            injury_severity,
        'course_difficulty':          course_difficulty,
        'vo2_max':                    vo2_max,
        'resting_heart_rate_bpm':     resting_heart_rate,
        'recovery_score':             recovery_score,
        'previous_marathon_count':    previous_marathon_count,
        'run_club_attendance_rate':   run_club_attendance,
        'marathon_weather_Cold':      1 if marathon_weather == 'Cold'  else 0,
        'marathon_weather_Hot':       1 if marathon_weather == 'Hot'   else 0,
        'marathon_weather_Rainy':     1 if marathon_weather == 'Rainy' else 0,
        'marathon_weather_Windy':     1 if marathon_weather == 'Windy' else 0,
    }

# ============================================================
# SECTION 2 — VALIDATION + API CALL + PREDICTION
# ============================================================

missing_fields = []

if age == 0:
    missing_fields.append("Age")
if running_experience_months == 0:
    missing_fields.append("Running Experience")
if level == "Expert":
    if personal_best_minutes is None or personal_best_minutes == 0:
        missing_fields.append("Personal Best")
if weekly_mileage_km < 10:
    missing_fields.append("Weekly Mileage (minimum 10km/week)")

if st.button("Predict My Finish Time"):

    if missing_fields:
        st.warning(f"⚠️ Please complete: {', '.join(missing_fields)}")

    else:
        with st.spinner("Analysing your mission profile..."):
            response = requests.post(url, json=feature_vector)

        if response.status_code == 200:
            result = response.json()
            prediction = result.get("predicted_finish_time", None)
            shap_values = result.get('shap_values', {})
            base_value = result.get('base_value', 0)

            if prediction is not None:

                hours = int(prediction // 60)
                minutes = int(prediction % 60)
                pace = prediction / 42.195
                pace_min = int(pace)
                pace_sec = int(round((pace - pace_min) * 60))
                if pace_sec == 60:
                    pace_min += 1
                    pace_sec = 0

                st.markdown("---")
                st.metric(
                    label="Predicted Finish Time",
                    value=f"{hours}h {minutes:02d}min → {pace_min}:{pace_sec:02d} min/km"
                )

                if shap_values:
                    st.subheader("Factors Driving Your Time")

                    label_map = {
                        'age': 'Age',
                        'running_experience_months': 'Running Experience (months)',
                        'weekly_mileage_km': 'Weekly Mileage (km)',
                        'injury_count': 'Injuries',
                        'injury_severity': 'Injury Severity',
                        'course_difficulty': 'Course Difficulty',
                        'vo2_max': 'VO2 Max',
                        'resting_heart_rate_bpm': 'Resting HR (bpm)',
                        'recovery_score': 'Recovery Score',
                        'previous_marathon_count': 'Previous Marathons',
                        'run_club_attendance_rate': 'Run Club Attendance',
                        'marathon_weather_Cold': 'Cold Weather',
                        'marathon_weather_Hot': 'Hot Weather',
                        'marathon_weather_Rainy': 'Rainy Weather',
                        'marathon_weather_Windy': 'Windy Weather',
                        'personal_best_minutes': 'Personal Best (min)',
                    }

                    feature_names = list(shap_values.keys())
                    shap_array = np.array(list(shap_values.values()))
                    feature_values = [feature_vector.get(name, 0) for name in feature_names]
                    display_names = [label_map.get(name, name) for name in feature_names]

                    explanation = shap.Explanation(
                        values=shap_array,
                        base_values=base_value,
                        data=feature_values,
                        feature_names=display_names
                    )

                    plt.rcParams.update({
                        'font.family': 'monospace',
                        'font.size': 10,
                        'axes.edgecolor': '#B8B8B0',
                        'axes.linewidth': 0.5,
                        'axes.labelcolor': '#0A0A0A',
                        'xtick.color': '#6A6A6A',
                        'ytick.color': '#0A0A0A',
                        'figure.facecolor': '#FAFAF7',
                        'axes.facecolor': '#FAFAF7',
                    })

                    fig, ax = plt.subplots(figsize=(10, 6))
                    shap.plots.waterfall(explanation, max_display=10, show=False)
                    ax = plt.gca()
                    ax.set_xlabel("Time (min)", labelpad=25)

                    for text in fig.findobj(plt.Text):
                        actual = text.get_text()
                        if ('f(x)' in actual
                                or 'E[f(X)]' in actual
                                or re.search(r'=\s*[\d\.]+', actual)):
                            text.set_visible(False)

                    for axis in fig.axes:
                        for patch in axis.patches:
                            face = patch.get_facecolor()
                            if face[0] > 0.5 and face[1] < 0.3:
                                patch.set_facecolor('#6B1B1B')
                                patch.set_edgecolor('#6B1B1B')
                            elif face[2] > 0.5 and face[0] < 0.3:
                                patch.set_facecolor('#004225')
                                patch.set_edgecolor('#004225')

                    for axis in fig.axes:
                        for text in axis.texts:
                            txt = text.get_text()
                            try:
                                r, g, b = to_rgb(text.get_color())
                                if r > 0.85 and g > 0.85 and b > 0.85:
                                    continue
                            except (ValueError, TypeError):
                                continue
                            if txt.startswith('+'):
                                text.set_color('#6B1B1B')
                            elif txt.startswith('−') or txt.startswith('-'):
                                text.set_color('#004225')

                    ax.annotate(f"Your time = {prediction:.1f}",
                                xy=(prediction, 1), xycoords=('data', 'axes fraction'),
                                xytext=(0, 40), textcoords='offset points',
                                ha='center', fontsize=10, color='gray')
                    ax.annotate(f"Avg runner = {base_value:.1f}",
                                xy=(base_value, 0), xycoords=('data', 'axes fraction'),
                                xytext=(0, -40), textcoords='offset points',
                                ha='center', fontsize=10, color='gray')

                    st.pyplot(fig, bbox_inches='tight')
                    plt.close()

                    st.caption("*Based on a synthetic dataset of 80,000 simulated runners, informed by sports medicine assumptions. Predictions may deviate from actual finish time depending on inputs provided. Not a substitute for structured training or professional coaching.*")
                    st.caption("*For VO2 Max, Resting HR, and Recovery Score, median dataset values are assumed if not provided (Median VO2 Max = 45, Resting HR = 68, Recovery Score = Good). These factors remain active in your analysis even when shown as 0 in your briefing.*")

        else:
            st.error(f"API error: {response.status_code}")

else:
    st.info("Complete your briefing above to receive your prediction.")
