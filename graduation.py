import streamlit as st
import pandas as pd
import numpy as np

# Page configuration
st.set_page_config(page_title="Graduation Outcome Dashboard", layout="wide")

# Google Sheet CSV Export Link
SHEET_ID = "1LNHrVooUxwzmO9lQ3w8tlbZTtHQbCbMXemk8qGcycLQ"
SHEET_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv"

@st.cache_data
def load_data():
    # Read the sheet
    df = pd.read_csv(SHEET_URL)
    
    # Standardize column names (removing extra spaces)
    df.columns = df.columns.str.strip()
    
    # Mapping specific columns based on your requirements
    # Column E: Year of graduation
    # Column F: Stipulated time pass (Yes/No)
    # Column G: Status (Placed / Higher Studies)
    # Column M: Annual CTC
    
    # 1. Clean Year Column
    year_col = "Year of graduation (UG/PG pass)"
    df[year_col] = pd.to_numeric(df[year_col], errors='coerce')
    
    # 2. Identify and Clean Salary Column (Column M)
    # We look for the column starting with "Annual CTC"
    salary_col = [c for c in df.columns if "Annual CTC" in c][0]
    
    # Convert to numeric: remove any stray symbols just in case user ignored instructions
    df['clean_salary'] = df[salary_col].astype(str).replace(r'[\s,₹Rs\.]', '', regex=True)
    df['clean_salary'] = pd.to_numeric(df['clean_salary'], errors='coerce')
    
    return df, salary_col

try:
    df, full_salary_header = load_data()

    st.title("🎓 Graduation Outcome Analysis")
    st.markdown("---")

    # --- Sidebar Filters ---
    st.sidebar.header("Data Selection")
    
    depts = sorted(df['Department Name'].dropna().unique().tolist())
    progs = sorted(df['Program'].dropna().unique().tolist())
    years = sorted([int(y) for y in df['Year of graduation (UG/PG pass)'].dropna().unique()], reverse=True)

    sel_dept = st.sidebar.selectbox("Department", depts)
    sel_prog = st.sidebar.selectbox("Program (UG/PG)", progs)
    sel_year = st.sidebar.selectbox("Year of Graduation", years)

    # --- Defined Column Names ---
    pass_col = "Did you pass UG/PG with in the stipulated time (UG: 3 years and PG: 2 Years)"
    status_col = "Status"
    year_col = "Year of graduation (UG/PG pass)"

    # --- Filtering Logic ---
    # Filter for counts (Dept + Program + Year)
    main_filter = df[
        (df['Department Name'] == sel_dept) &
        (df['Program'] == sel_prog) &
        (df[year_col] == sel_year)
    ]

    # Filter for Salary (Program + Year ONLY)
    salary_filter = df[
        (df['Program'] == sel_prog) &
        (df[year_col] == sel_year)
    ]

    # --- Metrics Calculation ---
    # 1. Students who passed in stipulated time (F = Yes)
    passed_count = len(main_filter[main_filter[pass_col].str.strip().str.lower() == 'yes'])
    
    # 2. Higher Studies (Status = Higher Studies AND F = Yes)
    higher_studies = len(main_filter[
        (main_filter[status_col] == 'Higher Studies') & 
        (main_filter[pass_col].str.strip().str.lower() == 'yes')
    ])
    
    # 3. Placed (Status = Placed / Employed AND F = Yes)
    placed_count = len(main_filter[
        (main_filter[status_col] == 'Placed / Employed') & 
        (main_filter[pass_col].str.strip().str.lower() == 'yes')
    ])

    # 4. Salary Stats (Based on Salary Filter)
    # Only calculate for students with 'Placed / Employed' status and valid salary
    salary_data = salary_filter[
        (salary_filter[status_col] == 'Placed / Employed') & 
        (salary_filter['clean_salary'] > 0)
    ]['clean_salary']

    # --- Display UI ---
    st.subheader(f"Results for {sel_dept} ({sel_prog}) - {sel_year}")
    
    c1, c2, c3 = st.columns(3)
    with c1:
        st.metric("Total Passed (Stipulated Time)", passed_count)
    with c2:
        st.metric("Placed / Employed", placed_count)
    with c3:
        st.metric("Higher Studies", higher_studies)

    st.markdown("---")
    st.subheader(f"Salary Benchmarks: {sel_prog} - {sel_year}")
    st.caption("Calculated across all departments for the selected Program and Year.")

    if not salary_data.empty:
        s1, s2, s3 = st.columns(3)
        s1.metric("Median CTC", f"₹{salary_data.median():,.0f}")
        s2.metric("Minimum CTC", f"₹{salary_data.min():,.0f}")
        s3.metric("Maximum CTC", f"₹{salary_data.max():,.0f}")
    else:
        st.warning("No salary data available for the current selection.")

    # --- Data Transparency ---
    with st.expander("View Filtered Raw Data"):
        st.dataframe(main_filter)

except Exception as e:
    st.error(f"An error occurred: {e}")
    st.info("Ensure the Google Sheet is shared as 'Anyone with the link can view'.")
