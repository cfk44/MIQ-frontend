import requests
import os
import streamlit as st
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

st.markdown(f"Working with {url_base}")

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
            🏃 MarathonIQ 🏃
        </h1>
        <p style="color: black; font-size: 1.2rem;">
            What actually predicts your marathon time?
        </p>
    </div>
""", unsafe_allow_html=True)
st.markdown("---")

# ============================================================
# SECTION 1 — USER INPUTS
# ============================================================

st.header("Your Training Profile")
level = st.radio("", ["🌞 First Marathon", "🏆 Already Ran a Marathon"], horizontal=True)

if level == "🌞 First Marathon":
    url = url_base + '/general'
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

        with col4:
            previous_marathon_count = st.slider("Previous Marathons", 0, 20, 0)
            run_club_attendance = st.slider("Run Club Attendance (%)", 0, 100, 0)
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

    response = requests.get(url, params=feature_vector)

# ============================================================
# DOING THE SAME FOR THE EXPERT MODEL
# ============================================================

else:
    url = url_base + '/expert'
    # --- MUST HAVE ---
    st.subheader("Required - add personal best")
    col1, col2 = st.columns(2)

    with col1:
        age = st.slider("Age", 18, 75, 35)
        running_experience_months = st.slider("Running Experience (months)", 0, 240, 24)
        weekly_mileage_km = st.slider("Weekly Mileage (km)", 0, 150, 40)
        personal_best = st.time_input("Personal Best", value=None)
        if personal_best is not None:
            personal_best_minutes = personal_best.hour * 60 + personal_best.minute
        else:
            personal_best_minutes = None

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
            vo2_max = st.slider("VO2 Max", min_value=0, max_value=80, value=0, step=1)
            resting_heart_rate = st.slider("Resting Heart Rate (bpm)", 0, 100, 0)
            recovery_score = st.slider("Recovery Score (1-10)", 0.0, 10.0, 0.0)

        with col4:
            previous_marathon_count = st.slider("Previous Marathons", 0, 20, 0)
            run_club_attendance = st.slider("Run Club Attendance (%)", 0, 100, 0)
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

    response = requests.get(url, params=feature_vector)

# ============================================================
# SECTION 3 — API CALL + PREDICTION
# ============================================================

missing_fields = []

if age == 0:
    missing_fields.append("Age")
if running_experience_months == 0:
    missing_fields.append("Running Experience")
if weekly_mileage_km == 0:
    missing_fields.append("Weekly Mileage")
if level == "🏆 Already Ran a Marathon":
    if personal_best_minutes is None or personal_best_minutes == 0:
        missing_fields.append("Personal Best")

st.markdown("---")

if st.button("🏁 Predict My Finish Time"):

    if missing_fields:
        st.warning(f"⚠️ Please complete: {', '.join(missing_fields)}")

    else:
        with st.spinner("Calculating..."):
            st.write(feature_vector)
            response = requests.post(url, json=feature_vector)

        if response.status_code == 200:
            result = response.json()
            prediction = result.get("predicted_finish_time", None)

            if prediction is not None:
                hours = int(prediction // 60)
                minutes = int(prediction % 60)

                st.markdown("---")
                st.metric(
                    label="Predicted Finish Time",
                    value=f"{hours}h {minutes:02d}min"
                )

                st.info("📊 Feature breakdown — coming soon")

        else:
            st.error(f"API error: {response.status_code}")

        with st.expander("🔍 Debug — Feature Vector"):
            st.json(feature_vector)
