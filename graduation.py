import streamlit as st
import pandas as pd

# Page configuration
st.set_page_config(page_title="Graduation Outcome Dashboard", layout="wide")

# Google Sheet CSV Export Link
SHEET_ID = "1LNHrVooUxwzmO9lQ3w8tlbZTtHQbCbMXemk8qGcycLQ"
SHEET_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv"

@st.cache_data
def load_data():
    df = pd.read_csv(SHEET_URL)
    
    # 1. Clean whitespace from headers and text cells to prevent duplicates
    df.columns = df.columns.str.strip()
    df = df.apply(lambda x: x.str.strip() if x.dtype == "object" else x)
    
    # 2. Convert Year to numeric
    year_col = "Year of graduation (UG/PG pass)"
    df[year_col] = pd.to_numeric(df[year_col], errors='coerce')
    
    # 3. Handle Salary (Column M)
    salary_col = [c for c in df.columns if "Annual CTC" in c][0]
    df['clean_salary'] = df[salary_col].astype(str).replace(r'[\s,₹Rs\.]', '', regex=True)
    df['clean_salary'] = pd.to_numeric(df['clean_salary'], errors='coerce')
    
    return df

try:
    df = load_data()

    # Define Header Names
    pass_col = "Did you pass UG/PG with in the stipulated time (UG: 3 years and PG: 2 Years)"
    status_col = "Status"
    year_col = "Year of graduation (UG/PG pass)"
    dept_col = "Department Name"
    prog_col = "Program"

    st.title("🎓 Graduation Outcome Analysis")

    # --- Sidebar Filters ---
    st.sidebar.header("Filters")
    depts = sorted(df[dept_col].dropna().unique().tolist())
    progs = sorted(df[prog_col].dropna().unique().tolist())
    years = sorted([int(y) for y in df[year_col].dropna().unique()], reverse=True)

    sel_dept = st.sidebar.selectbox("Select Department", depts)
    sel_prog = st.sidebar.selectbox("Select Program", progs)
    sel_year = st.sidebar.selectbox("Select Year", years)

    # --- LOGIC 1: COUNTS (Filtered by Dept, Program, Year) ---
    dept_filtered_df = df[
        (df[dept_col] == sel_dept) &
        (df[prog_col] == sel_prog) &
        (df[year_col] == sel_year)
    ]

    # Calculate Counts
    passed_count = len(dept_filtered_df[dept_filtered_df[pass_col] == 'Yes'])
    placed_count = len(dept_filtered_df[(dept_filtered_df[status_col] == 'Placed / Employed') & (dept_filtered_df[pass_col] == 'Yes')])
    higher_studies_count = len(dept_filtered_df[(dept_filtered_df[status_col] == 'Higher Studies') & (dept_filtered_df[pass_col] == 'Yes')])

    # --- LOGIC 2: SALARY (Filtered by Program and Year ONLY) ---
    salary_filtered_df = df[
        (df[prog_col] == sel_prog) &
        (df[year_col] == sel_year)
    ]
    
    salary_values = salary_filtered_df[
        (salary_filtered_df[status_col] == 'Placed / Employed') & 
        (salary_filtered_df['clean_salary'] > 0)
    ]['clean_salary']

    # --- Display Metrics ---
    st.subheader(f"Data for {sel_dept} | {sel_prog} | {sel_year}")
    m1, m2, m3 = st.columns(3)
    m1.metric("Passed (Stipulated Time)", passed_count)
    m2.metric("Placed / Employed", placed_count)
    m3.metric("Higher Studies", higher_studies_count)

    st.markdown("---")
    
    st.subheader(f"Salary Benchmarks ({sel_prog} - {sel_year})")
    st.caption("Salary metrics are calculated based on the entire Program/Year across all departments.")
    
    if not salary_values.empty:
        s1, s2, s3 = st.columns(3)
        s1.metric("Median CTC", f"₹{salary_values.median():,.0f}")
        s2.metric("Min CTC", f"₹{salary_values.min():,.0f}")
        s3.metric("Max CTC", f"₹{salary_values.max():,.0f}")
    else:
        st.warning("No valid placement salary data found for this selection.")

except Exception as e:
    st.error(f"Something went wrong: {e}")
