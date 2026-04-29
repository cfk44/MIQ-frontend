import requests
import os
import re
import shap
import random
import matplotlib.pyplot as plt
import pandas as pd
import streamlit as st
import numpy as np
from pprint import  pprint

# Define the base URI of the API
#   - Potential sources are in `.streamlit/secrets.toml` or in the Secrets section
#     on Streamlit Cloud
#   - The source selected is based on the shell variable passend when launching streamlit
#    (shortcuts are included in Makefile). By default it takes the cloud API url

if 'BASE_URI' in os.environ:
    BASE_URI = os.environ.get('BASE_URI')
else:
    BASE_URI = st.secrets['cloud_api_uri']
# Add a '/' at the end if it's not there
BASE_URI = BASE_URI if BASE_URI.endswith('/') else BASE_URI + '/'
# Define the url to be used by requests.get to get a prediction (adapt if needed)
url_base = BASE_URI + 'predict'

#Page setup
st.set_page_config(page_title="MarathonIQ", layout="wide")

with open('.streamlit/style.css') as f:
    st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)

# Just displaying the source for the API. Remove this in your final version.

#st.markdown(f"Working with {url_base}")

#st.markdown("Now, the rest is up to you. Start creating your page.")

# ============================================================
# PAGE SETUP
# ============================================================

st.markdown("""
    <div style="
        background: transparent;
        padding: 1rem 0 0.5rem 0;
        margin: 0;
        text-align: center;
    ">
        <h1 style="color: black; margin-bottom: 0.5rem;">
            🏃🏻‍♂️‍➡️ MarathonIQ 🏃🏾‍♀️‍➡️
        </h1>
        <p style="color: black; font-size: 1.2rem;">
            Tell us about your training and we'll predict your finish time, plus show which factors drive it most.
        </p>
    </div>
""", unsafe_allow_html=True)
st.markdown("---")

# ============================================================
# SECTION 1 — USER INPUTS
# ============================================================

st.header("Your Profile")
level = st.radio("", ["🌞 First Marathon", "🏆 Already Ran a Marathon"], horizontal=True)

if level == "🌞 First Marathon":
    url = url_base + '/general'
    # --- MUST HAVE ---
    st.subheader("Tell us about your training")
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
        st.caption("Optional inputs — if not provided, values will be automatically set to 0 or to the median of our dataset.")

        col3, col4 = st.columns(2)

        with col3:
            vo2_max = st.number_input("VO2 Max", 30, 85, 45)
            resting_heart_rate = st.number_input("Resting Heart Rate (bpm)", 30, 100, 68)
            previous_marathon_count = st.number_input("Previous Marathons", 0, 100, 0)

        with col4:
            recovery_score = st.selectbox(
                "Recovery Score - Body Battery - Readiness Score - Nightly Recharge",
                options=[0, 3, 6, 7, 9],
                format_func=lambda x: {0: "I don't track this",
                                       3: "Low — fatigued",
                                       6: "Moderate — somewhat tired",
                                       7: "Good — well rested",
                                       9: "High — fully recovered"}[x]
            )

            run_club_attendance = st.selectbox(
                "Run Club Attendance",
                options=[12, 37, 62, 87],
                format_func=lambda x: {12: "Never",
                                       37: "Rarely — once a month or less",
                                       62: "Sometimes — a few times a month",
                                       87: "Often — weekly or more"}[x]
            )
            marathon_weather = st.selectbox(
                "Race Day Weather",
                options=["Neutral", "Cold", "Hot", "Rainy", "Windy"]
            )

    # Build feature vector
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

    #response = requests.get(url, params=feature_vector)

# ============================================================
# DOING THE SAME FOR THE EXPERT MODEL
# ============================================================

else:
    url = url_base + '/expert'
    # --- MUST HAVE ---
    st.subheader("Tell us about your training")
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
        st.caption("Optional inputs — if not provided, values will be automatically set to 0 or to the median of our dataset.")

        col3, col4 = st.columns(2)

        with col3:
            vo2_max = st.number_input("VO2 Max", 30, 85, 45)
            resting_heart_rate = st.number_input("Resting Heart Rate (bpm)", 30, 100, 68)
            previous_marathon_count = st.number_input("Previous Marathons", 0, 100, 0)

        with col4:
            recovery_score = st.selectbox(
                "Recovery Score - Body Battery - Readiness Score - Nightly Recharge",
                options=[0, 3, 6, 7, 9],
                format_func=lambda x: {0: "I don't track this",
                                       3: "Low — fatigued",
                                       6: "Moderate — somewhat tired",
                                       7: "Good — well rested",
                                       9: "High — fully recovered"}[x]
            )
            run_club_attendance = st.selectbox(
                "Run Club Attendance",
                options=[12, 37, 62, 87],
                format_func=lambda x: {12: "Never",
                                       37: "Rarely — once a month or less",
                                       62: "Sometimes — a few times a month",
                                       87: "Often — weekly or more"}[x]
            )
            marathon_weather = st.selectbox(
                "Race Day Weather",
                options=["Neutral", "Cold", "Hot", "Rainy", "Windy"]
            )


    # Build feature vector
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

    #response = requests.get(url, params=feature_vector)

# ============================================================
# SECTION 3 — API CALL + PREDICTION
# ============================================================

missing_fields = []

if age == 0:
    missing_fields.append("Age")
if running_experience_months == 0:
    missing_fields.append("Running Experience")
if level == "🏆 Already Ran a Marathon":
    if personal_best_minutes is None or personal_best_minutes == 0:
        missing_fields.append("Personal Best")
if weekly_mileage_km < 10:
    missing_fields.append("Weekly Mileage (minimum 10km/week)")

if st.button("🏁 Predict My Finish Time"):

    if missing_fields:
        st.warning(f"⚠️ Please complete: {', '.join(missing_fields)}")

    else:
        with st.spinner("Crunching your training data..."):
            #st.write(feature_vector)
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
                    value=f"{hours}h {minutes:02d}min ➡️ {pace_min}:{pace_sec:02d} min/km"
                )

                if shap_values:
                    st.subheader("What's driving your time")

                    # Feature name mapping → display labels
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

                    fig, ax = plt.subplots(figsize=(10, 6))
                    shap.plots.waterfall(explanation, max_display=10, show=False)
                    ax = plt.gca()
                    ax.set_xlabel("Time (min)", labelpad=25)

                    import re
                    for text in fig.findobj(plt.Text):
                        actual = text.get_text()
                        if ('f(x)' in actual
                            or 'E[f(X)]' in actual
                            or re.search(r'=\s*[\d\.]+', actual)):
                            text.set_visible(False)

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

                    st.caption("*Based on a synthetic dataset of 80,000 simulated runners, informed by sports medicine assumptions. Predictions can deviate significantly from actual finish time depending on the inputs provided. Not a substitute for structured training or professional coaching.*")
                    st.caption("*For VO2 Max, Resting HR, and Recovery Score, the median values of the dataset are assumed if not provided (Median VO2 Max = 45, Resting HR = 68, Recovery Score = Good). These contribute to the prediction even when shown as 0 in your input.*")



                gif = random.choice([
                    "media/forest.gif",
                    "media/rocket.gif",
                    "media/wonderwoman.gif"
                ])
                st.markdown(
                    f'<div style="text-align: center;"><img src="data:image/gif;base64,{__import__("base64").b64encode(open(gif, "rb").read()).decode()}" width="400"></div>',
                    unsafe_allow_html=True
                )

        else:
            st.error(f"API error: {response.status_code}")

        #with st.expander("🔍 Debug — Feature Vector"):
            #st.json(feature_vector)
else:
    st.info("Fill in your stats above to see your prediction!")
