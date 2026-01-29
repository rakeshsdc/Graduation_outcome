import streamlit as st
import pandas as pd
import numpy as np

# Page configuration
st.set_page_config(page_title="Graduation Outcome Dashboard", layout="wide")

# 1. Setup Data Loading
# Replacing the /edit... with /export?format=csv to read directly into pandas
SHEET_ID = "1LNHrVooUxwzmO9lQ3w8tlbZTtHQbCbMXemk8qGcycLQ"
SHEET_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv"

@st.cache_data
def load_data():
    df = pd.read_csv(SHEET_URL)
    # Clean column names (strip spaces)
    df.columns = df.columns.str.strip()
    
    # Identify specific columns by descriptions provided
    # Column E: Year of graduation (UG/PG pass)
    # Column F: Did you pass UG/PG with in the stipulated time (UG: 3 years and PG: 2 Years)
    # Column G: Status
    # Salary Column: "Annual CTC (₹ per year) : ..."
    
    # Cleaning data types
    df['Year of graduation (UG/PG pass)'] = pd.to_numeric(df['Year of graduation (UG/PG pass)'], errors='coerce')
    
    # Clean Salary Column (extract numbers only)
    salary_col = [c for c in df.columns if "Annual CTC" in c][0]
    df['clean_salary'] = df[salary_col].replace(r'[\s,₹Rs\.]', '', regex=True)
    df['clean_salary'] = pd.to_numeric(df['clean_salary'], errors='coerce')
    
    return df

try:
    df = load_data()

    st.title("🎓 Graduation Outcome Data Dashboard")

    # --- Sidebar Inputs ---
    st.sidebar.header("Filter Data")
    
    # Unique values for filters
    departments = sorted(df['Department Name'].unique().tolist())
    programs = sorted(df['Program'].unique().tolist())
    years = sorted([int(y) for y in df['Year of graduation (UG/PG pass)'].dropna().unique()])

    selected_dept = st.sidebar.selectbox("Select Department", departments)
    selected_prog = st.sidebar.selectbox("Select Program", programs)
    selected_year = st.sidebar.selectbox("Select Year of Graduation", years)

    # --- Filtering Logic ---
    # Filter 1: Main filter for Department, Program, and Year
    filtered_df = df[
        (df['Department Name'] == selected_dept) &
        (df['Program'] == selected_prog) &
        (df['Year of graduation (UG/PG pass)'] == selected_year)
    ]

    # Filter 2: Median Salary filter (Year and Program only, no Dept)
    salary_df = df[
        (df['Program'] == selected_prog) &
        (df['Year of graduation (UG/PG pass)'] == selected_year)
    ]

    # --- Calculations ---
    # Total students in the filtered selection
    total_students = len(filtered_df)
    
    # Column F check: Stipulated time (Column index 5 usually)
    pass_col = "Did you pass UG/PG with in the stipulated time (UG: 3 years and PG: 2 Years)"
    status_col = "Status"

    # Number of students who passed (F column == Yes)
    students_passed = len(filtered_df[filtered_df[pass_col].str.strip().str.lower() == 'yes'])
    
    # Higher Studies (G column == Higher Studies) - ONLY if passed (F == Yes)
    higher_studies = len(filtered_df[
        (filtered_df[status_col] == 'Higher Studies') & 
        (filtered_df[pass_col].str.strip().str.lower() == 'yes')
    ])
    
    # Placed (G column == Placed / Employed) - ONLY if passed (F == Yes)
    placed_students = len(filtered_df[
        (filtered_df[status_col] == 'Placed / Employed') & 
        (filtered_df[pass_col].str.strip().str.lower() == 'yes')
    ])

    # Salary Stats (Median, Min, Max) - Based on Program and Year (Salary_df)
    # Only calculate for students with 'Placed / Employed' status in the salary_df
    placed_salary_data = salary_df[
        (salary_df[status_col] == 'Placed / Employed') & 
        (salary_df['clean_salary'].notnull())
    ]['clean_salary']

    # --- UI Layout ---
    col1, col2, col3 = st.columns(3)
    col1.metric("Students Passed (Stipulated Time)", students_passed)
    col2.metric("Students Placed", placed_students)
    col3.metric("Higher Studies", higher_studies)

    st.markdown("---")
    st.subheader(f"Salary Statistics for {selected_prog} - {selected_year}")
    st.info("Note: Median, Min, and Max salary are calculated across all departments for the selected Program and Year.")

    if not placed_salary_data.empty:
        m1, m2, m3 = st.columns(3)
        m1.metric("Median Salary", f"₹{placed_salary_data.median():,.2f}")
        m2.metric("Minimum Salary", f"₹{placed_salary_data.min():,.2f}")
        m3.metric("Maximum Salary", f"₹{placed_salary_data.max():,.2f}")
    else:
        st.warning("No placement salary data available for the selected Program and Year.")

    # --- Raw Data View (Optional) ---
    with st.expander("View Filtered Data"):
        st.dataframe(filtered_df)

except Exception as e:
    st.error(f"Error loading data: {e}")
    st.write("Please ensure the Google Sheet link is public and the column names match your requirements.")
