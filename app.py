import streamlit as st
import pandas as pd
from sqlalchemy import create_engine, text

# MySQL connection
engine = create_engine("mysql+pymysql://root:Vani%4019112023%21@localhost:3306/Police")

# Load data from MySQL
@st.cache_data
def load_data():
    with engine.connect() as conn:
        result = conn.execute(text("SELECT * FROM police_stops"))
        return pd.DataFrame(result.fetchall(), columns=result.keys())

df = load_data()

# App title
st.set_page_config(page_title="SecureCheck Dashboard", layout="wide")
st.title("🚔 SecureCheck: Police Stop Records")

# Sidebar filters
st.sidebar.header("🔍 Filter Records")

# Dynamic filter options
country_options = ["All"] + sorted(df['country_name'].dropna().unique().tolist())
violation_options = ["All"] + sorted(df['violation'].dropna().unique().tolist())
gender_options = ["All"] + sorted(df['driver_gender'].dropna().unique().tolist())

# Filter widgets
selected_country = st.sidebar.selectbox("Country", country_options)
selected_violation = st.sidebar.selectbox("Violation", violation_options)
selected_gender = st.sidebar.selectbox("Driver Gender", gender_options)

# Apply filters
filtered_df = df.copy()
if selected_country != "All":
    filtered_df = filtered_df[filtered_df['country_name'] == selected_country]
if selected_violation != "All":
    filtered_df = filtered_df[filtered_df['violation'] == selected_violation]
if selected_gender != "All":
    filtered_df = filtered_df[filtered_df['driver_gender'] == selected_gender]

# Display filtered data
st.subheader("📋 Filtered Vehicle Logs")
st.dataframe(filtered_df, use_container_width=True)

# Top violations chart
st.subheader("📈 Top 5 Violations")
top_violations = filtered_df['violation'].value_counts().head(5)
if not top_violations.empty:
    st.bar_chart(top_violations)
else:
    st.info("No data available to display chart.")

    # Insert Record Form
st.subheader("📥 Add New Police Stop Record")

with st.form("insert_form"):
    col1, col2 = st.columns(2)
    with col1:
        stop_date = st.date_input("Stop Date")
        stop_time = st.time_input("Stop Time")
        country = st.text_input("Country Name")
        gender = st.selectbox("Driver Gender", ["M", "F"])
        age_raw = st.number_input("Driver Age (Raw)", min_value=0)
        age = st.number_input("Driver Age", min_value=0)
        race = st.text_input("Driver Race")
        violation_raw = st.text_input("Violation Raw")
        violation = st.text_input("Violation")
    with col2:
        search_conducted = st.checkbox("Search Conducted")
        search_type = st.text_input("Search Type")
        outcome = st.text_input("Stop Outcome")
        is_arrested = st.checkbox("Arrest Made")
        duration = st.selectbox("Stop Duration", ["0-15 Min", "16-30 Min", "30+ Min"])
        drugs_related = st.checkbox("Drug-Related Stop")
        vehicle_number = st.text_input("Vehicle Number")

    submitted = st.form_submit_button("Insert Record")

    if submitted:
        stop_datetime = f"{stop_date} {stop_time}"
        query = text("""
            INSERT INTO police_stops (
                stop_datetime, country_name, driver_gender, driver_age_raw, driver_age,
                driver_race, violation_raw, violation, search_conducted, search_type,
                stop_outcome, is_arrested, stop_duration, drugs_related_stop, vehicle_number
            ) VALUES (
                :stop_datetime, :country_name, :driver_gender, :driver_age_raw, :driver_age,
                :driver_race, :violation_raw, :violation, :search_conducted, :search_type,
                :stop_outcome, :is_arrested, :stop_duration, :drugs_related_stop, :vehicle_number
            )
        """)
        with engine.connect() as conn:
            conn.execute(query, {
                "stop_datetime": stop_datetime,
                "country_name": country,
                "driver_gender": gender,
                "driver_age_raw": age_raw,
                "driver_age": age,
                "driver_race": race,
                "violation_raw": violation_raw,
                "violation": violation,
                "search_conducted": search_conducted,
                "search_type": search_type,
                "stop_outcome": outcome,
                "is_arrested": is_arrested,
                "stop_duration": duration,
                "drugs_related_stop": drugs_related,
                "vehicle_number": vehicle_number
            })
            conn.commit()
        st.success("✅ Record inserted successfully!")

        st.subheader("🚗 Top 10 Drug-Related Vehicles")

query = text("""
    SELECT 
        vehicle_number,
        COUNT(*) AS stop_count
    FROM police_stops
    WHERE drugs_related_stop = TRUE
    GROUP BY vehicle_number
    ORDER BY stop_count DESC
    LIMIT 10
""")

with engine.connect() as conn:
    result = conn.execute(query)
    drug_df = pd.DataFrame(result.fetchall(), columns=result.keys())

st.dataframe(drug_df)



st.subheader("🧍 Arrest Rate by Gender and Race")

query = text("""
    SELECT 
        driver_gender,
        driver_race,
        COUNT(*) AS total_stops,
        SUM(CASE WHEN is_arrested = TRUE THEN 1 ELSE 0 END) AS total_arrests,
        ROUND(SUM(CASE WHEN is_arrested = TRUE THEN 1 ELSE 0 END) / COUNT(*) * 100, 2) AS arrest_rate
    FROM police_stops
    GROUP BY driver_gender, driver_race
    ORDER BY arrest_rate DESC
""")

with engine.connect() as conn:
    result = conn.execute(query)
    gender_race_df = pd.DataFrame(result.fetchall(), columns=result.keys())

st.dataframe(gender_race_df)


st.subheader("🕒 Stops by Hour of Day")

query = text("""
    SELECT 
        HOUR(stop_datetime) AS hour,
        COUNT(*) AS stop_count
    FROM police_stops
    GROUP BY hour
    ORDER BY hour
""")

with engine.connect() as conn:
    result = conn.execute(query)
    hour_df = pd.DataFrame(result.fetchall(), columns=result.keys())

st.dataframe(hour_df)


st.subheader("⚖️ Violations with Highest Arrest Rates")

query = text("""
    SELECT 
        violation,
        COUNT(*) AS total_stops,
        SUM(CASE WHEN is_arrested = TRUE THEN 1 ELSE 0 END) AS total_arrests,
        ROUND(SUM(CASE WHEN is_arrested = TRUE THEN 1 ELSE 0 END) / COUNT(*) * 100, 2) AS arrest_rate
    FROM police_stops
    GROUP BY violation
    HAVING total_stops > 5
    ORDER BY arrest_rate DESC
""")

with engine.connect() as conn:
    result = conn.execute(query)
    violation_df = pd.DataFrame(result.fetchall(), columns=result.keys())

st.dataframe(violation_df)


st.subheader("🌍 Country-wise Drug Stop Trends")

query = text("""
    SELECT 
        country_name,
        COUNT(*) AS total_stops,
        SUM(CASE WHEN drugs_related_stop = TRUE THEN 1 ELSE 0 END) AS drug_stops,
        ROUND(SUM(CASE WHEN drugs_related_stop = TRUE THEN 1 ELSE 0 END) / COUNT(*) * 100, 2) AS drug_stop_rate
    FROM police_stops
    GROUP BY country_name
    HAVING total_stops > 5
    ORDER BY drug_stop_rate DESC
""")

with engine.connect() as conn:
    result = conn.execute(query)
    country_df = pd.DataFrame(result.fetchall(), columns=result.keys())

st.dataframe(country_df)


st.subheader("📅 Monthly Stop Trends")

query = text("""
    SELECT 
        DATE_FORMAT(stop_datetime, '%Y-%m') AS month,
        COUNT(*) AS stop_count
    FROM police_stops
    GROUP BY month
    ORDER BY month
""")

with engine.connect() as conn:
    result = conn.execute(query)
    month_df = pd.DataFrame(result.fetchall(), columns=result.keys())

st.dataframe(month_df)


st.subheader("🧠 Search Conducted vs Arrest Likelihood")

query = text("""
    SELECT 
        search_conducted,
        COUNT(*) AS total_stops,
        SUM(CASE WHEN is_arrested = TRUE THEN 1 ELSE 0 END) AS total_arrests,
        ROUND(SUM(CASE WHEN is_arrested = TRUE THEN 1 ELSE 0 END) / COUNT(*) * 100, 2) AS arrest_rate
    FROM police_stops
    GROUP BY search_conducted
""")

with engine.connect() as conn:
    result = conn.execute(query)
    search_df = pd.DataFrame(result.fetchall(), columns=result.keys())

st.dataframe(search_df)


st.subheader("🧍 Race-wise Drug Stop Rate")

query = text("""
    SELECT 
        driver_race,
        COUNT(*) AS total_stops,
        SUM(CASE WHEN drugs_related_stop = TRUE THEN 1 ELSE 0 END) AS drug_stops,
        ROUND(SUM(CASE WHEN drugs_related_stop = TRUE THEN 1 ELSE 0 END) / COUNT(*) * 100, 2) AS drug_stop_rate
    FROM police_stops
    GROUP BY driver_race
    HAVING total_stops > 5
    ORDER BY drug_stop_rate DESC
""")

with engine.connect() as conn:
    result = conn.execute(query)
    race_df = pd.DataFrame(result.fetchall(), columns=result.keys())

st.dataframe(race_df)


st.subheader("🚨 Repeat-Offender Vehicle Tracker")

query = text("""
    SELECT 
        vehicle_number,
        COUNT(*) AS stop_count,
        SUM(CASE WHEN is_arrested = TRUE THEN 1 ELSE 0 END) AS arrests,
        SUM(CASE WHEN drugs_related_stop = TRUE THEN 1 ELSE 0 END) AS drug_stops
    FROM police_stops
    GROUP BY vehicle_number
    HAVING stop_count > 3
    ORDER BY stop_count DESC
""")

with engine.connect() as conn:
    result = conn.execute(query)
    repeat_df = pd.DataFrame(result.fetchall(), columns=result.keys())

st.dataframe(repeat_df)


st.subheader("📈 Year-over-Year Stop Comparison")

query = text("""
    SELECT 
        YEAR(stop_datetime) AS year,
        COUNT(*) AS stop_count
    FROM police_stops
    GROUP BY year
    ORDER BY year
""")

with engine.connect() as conn:
    result = conn.execute(query)
    year_df = pd.DataFrame(result.fetchall(), columns=result.keys())

st.dataframe(year_df)


st.subheader("🕵️ Search Type vs Arrest Rate")

query = text("""
    SELECT 
        search_type,
        COUNT(*) AS total_stops,
        SUM(CASE WHEN is_arrested = TRUE THEN 1 ELSE 0 END) AS total_arrests,
        ROUND(SUM(CASE WHEN is_arrested = TRUE THEN 1 ELSE 0 END) / COUNT(*) * 100, 2) AS arrest_rate
    FROM police_stops
    WHERE search_type IS NOT NULL
    GROUP BY search_type
    ORDER BY arrest_rate DESC
""")

with engine.connect() as conn:
    result = conn.execute(query)
    search_type_df = pd.DataFrame(result.fetchall(), columns=result.keys())

st.dataframe(search_type_df)


st.subheader("🧠 Stop Duration vs Arrest Likelihood")

query = text("""
    SELECT 
        CASE 
            WHEN stop_duration < 5 THEN '<5 min'
            WHEN stop_duration BETWEEN 5 AND 10 THEN '5–10 min'
            WHEN stop_duration BETWEEN 11 AND 20 THEN '11–20 min'
            WHEN stop_duration BETWEEN 21 AND 30 THEN '21–30 min'
            ELSE '>30 min'
        END AS duration_range,
        COUNT(*) AS total_stops,
        SUM(CASE WHEN is_arrested = TRUE THEN 1 ELSE 0 END) AS total_arrests,
        ROUND(SUM(CASE WHEN is_arrested = TRUE THEN 1 ELSE 0 END) / COUNT(*) * 100, 2) AS arrest_rate
    FROM police_stops
    WHERE stop_duration IS NOT NULL
    GROUP BY duration_range
    ORDER BY arrest_rate DESC
""")

with engine.connect() as conn:
    result = conn.execute(query)
    duration_df = pd.DataFrame(result.fetchall(), columns=result.keys())

st.dataframe(duration_df)


st.subheader("📍 Violation Trends Over Time")

query = text("""
    SELECT 
        violation,
        DATE_FORMAT(stop_datetime, '%Y-%m') AS month,
        COUNT(*) AS stop_count
    FROM police_stops
    GROUP BY violation, month
    ORDER BY violation, month
""")

with engine.connect() as conn:
    result = conn.execute(query)
    trend_df = pd.DataFrame(result.fetchall(), columns=result.keys())

st.dataframe(trend_df)

from sqlalchemy import Table, Column, Integer, String, Boolean, DateTime, Time, MetaData

metadata = MetaData()

police_stops = Table("police_stops", metadata,
    Column("stop_datetime", DateTime),
    Column("driver_age", Integer),
    Column("driver_race", String),
    Column("driver_gender", String),
    Column("vehicle_number", String),
    Column("violation", String),
    Column("is_arrested", Boolean),
    Column("drugs_related_stop", Boolean),
    Column("search_conducted", Boolean),
    Column("search_type", String),
    Column("stop_duration", DateTime),
    Column("country_name", String)
)
from sqlalchemy import create_engine, insert
from datetime import datetime, time

engine = create_engine("mysql+pymysql://root:Vani%4019112023%21@localhost:3306/Police")


from sqlalchemy import create_engine, insert, Table, MetaData
from datetime import datetime

engine = create_engine("your_database_connection_string")
metadata = MetaData()
metadata.reflect(bind=engine)

police_stops = metadata.tables["police_stops"]

sample_data = [
    {
        "stop_datetime": datetime(2025, 10, 1, 14, 30),
        "driver_age": 28,
        "driver_race": "Asian",
        "driver_gender": "Male",
        "vehicle_number": "TN01AB1234",
        "violation": "Speeding",
        "is_arrested": True,
        "drugs_related_stop": False,
        "search_conducted": True,
        "search_type": "Vehicle",
        "stop_duration": 15,
        "country_name": "India"
    },
    {
        "stop_datetime": datetime(2025, 10, 2, 9, 15),
        "driver_age": 35,
        "driver_race": "Black",
        "driver_gender": "Female",
        "vehicle_number": "TN02XY5678",
        "violation": "Expired Registration",
        "is_arrested": False,
        "drugs_related_stop": True,
        "search_conducted": False,
        "search_type": None,
        "stop_duration": 10,
        "country_name": "India"
    }
]

with engine.connect() as conn:
    for record in sample_data:
        conn.execute(insert(police_stops).values(**record))
    conn.commit()