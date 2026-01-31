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
    
    # Clean whitespace from headers
    df.columns = df.columns.str.strip()
    
    # 1. Clean String Columns
    # We strip spaces and handle NaN values
    text_cols = ['Department Name', 'Program', 'Status', 
                 'Did you pass UG/PG with in the stipulated time (UG: 3 years and PG: 2 Years)']
    for col in text_cols:
        if col in df.columns:
            df[col] = df[col].astype(str).str.strip()

    # 2. Year Column Cleaning
    year_col = "Year of graduation (UG/PG pass)"
    df[year_col] = pd.to_numeric(df[year_col], errors='coerce')
    
    # 3. Salary Column (Column M) Cleaning
    salary_col = [c for c in df.columns if "Annual CTC" in c][0]
    df['clean_salary'] = df[salary_col].astype(str).replace(r'[\s,₹Rs\.]', '', regex=True)
    df['clean_salary'] = pd.to_numeric(df['clean_salary'], errors='coerce')
    
    # 4. Create a "Short Code" for Departments (First 4 Letters)
    # This groups "Botany", "Botany ", "BOTANY" together as "BOTA"
    df['dept_short'] = df['Department Name'].str[:4].str.upper()
    
    return df

try:
    df = load_data()

    # Column Mapping
    dept_col = 'Department Name'
    prog_col = 'Program'
    year_col = 'Year of graduation (UG/PG pass)'
    pass_col = 'Did you pass UG/PG with in the stipulated time (UG: 3 years and PG: 2 Years)'
    status_col = 'Status'

    st.title("🎓 Graduation Outcome Analysis")

    # --- Sidebar Filters ---
    st.sidebar.header("Search Filters")
    
    # Pre-defined list as requested
    valid_depts = [
        "Botany", "Chemistry", "Commerce", "Communicative English", 
        "Economics", "English", "Hindi", "History", "Malayalam", 
        "Mathematics", "Microbiology", "Physics", "Zoology"
    ]
    
    sel_dept = st.sidebar.selectbox("Select Department", sorted(valid_depts))
    sel_prog = st.sidebar.selectbox("Select Program", ["UG", "PG"])
    
    years = sorted([int(y) for y in df[year_col].dropna().unique()], reverse=True)
    sel_year = st.sidebar.selectbox("Select Year of Graduation", years)

    # --- THE FILTERING LOGIC ---
    
    # Filter by First 4 letters of the selected department
    dept_code = sel_dept[:4].upper()
    
    # Apply filters: Department (4-char match) + Program + Year
    filtered_df = df[
        (df['dept_short'] == dept_code) & 
        (df[prog_col] == sel_prog) & 
        (df[year_col] == sel_year)
    ]

    # --- COUNTING LOGIC ---
    # 1. Total Passed: Must be "Yes" in Column F
    passed_mask = (filtered_df[pass_col].str.lower() == 'yes')
    passed_count = len(filtered_df[passed_mask])
    
    # 2. Placed: Must be "Placed / Employed" in Column G AND "Yes" in Column F
    placed_count = len(filtered_df[
        (filtered_df[status_col] == 'Placed / Employed') & (passed_mask)
    ])
    
    # 3. Higher Studies: Must be "Higher Studies" in Column G AND "Yes" in Column F
    higher_studies_count = len(filtered_df[
        (filtered_df[status_col] == 'Higher Studies') & (passed_mask)
    ])

    # --- SALARY LOGIC (Program and Year Only) ---
    salary_filter = df[
        (df[prog_col] == sel_prog) & 
        (df[year_col] == sel_year) &
        (df[status_col] == 'Placed / Employed') &
        (df['clean_salary'] > 0)
    ]
    salary_data = salary_filter['clean_salary']

    # --- DISPLAY ---
    st.header(f"Results for {sel_dept}")
    st.write(f"**Program:** {sel_prog} | **Year:** {sel_year}")
    
    c1, c2, c3 = st.columns(3)
    c1.metric("Passed (Stipulated Time)", passed_count)
    c2.metric("Placed / Employed", placed_count)
    c3.metric("Higher Studies", higher_studies_count)

    st.markdown("---")
    st.subheader(f"Salary Stats ({sel_prog} - {sel_year})")
    
    if not salary_data.empty:
        s1, s2, s3 = st.columns(3)
        s1.metric("Median CTC", f"₹{salary_data.median():,.0f}")
        s2.metric("Min CTC", f"₹{salary_data.min():,.0f}")
        s3.metric("Max CTC", f"₹{salary_data.max():,.0f}")
    else:
        st.warning("No salary data available for these filters.")

    # Validation Table (For your peace of mind to check against the sheet)
    with st.expander("Show student list for this selection"):
        st.dataframe(filtered_df[[dept_col, prog_col, year_col, pass_col, status_col]])

except Exception as e:
    st.error(f"Critical Error: {e}")
