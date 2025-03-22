import streamlit as st
import pandas as pd
import plotly.express as px
import os

# User credentials
USER_EMAIL = "user@wscom.edu"
USER_PASSWORD = "nbme123"

# Initialize session state variables
if "logged_in" not in st.session_state:
    st.session_state["logged_in"] = False
if "login_attempt" not in st.session_state:
    st.session_state["login_attempt"] = False
if "logout_triggered" not in st.session_state:
    st.session_state["logout_triggered"] = False

# Login page function
def login():
    st.markdown("""
        <h2 style='text-align: center;'>Wharton Street College of Medicine</h2>
        <h4 style='text-align: center;'>(Home of the Mummy's)</h4>
        <h3 style='text-align: center;'>🔐 Login to Access Dashboard</h3>
    """, unsafe_allow_html=True)

    email = st.text_input("Email", key="login_email", value="")
    password = st.text_input("Password", key="login_password", type="password", value="")  # ✅ Fixed issue here

    if st.button("Login"):
        if email == USER_EMAIL and password == USER_PASSWORD:
            st.session_state["logged_in"] = True
            st.session_state["login_attempt"] = False  # Reset failed attempt
            st.rerun()
        else:
            st.session_state["login_attempt"] = True

    if st.session_state["login_attempt"]:
        st.error("Invalid email or password. Please try again.")

# Logout function (triggered via button)
def trigger_logout():
    st.session_state["logout_triggered"] = True

# Check if user clicked logout
if st.session_state["logout_triggered"]:
    st.session_state["logged_in"] = False
    st.session_state["login_attempt"] = False
    st.session_state["logout_triggered"] = False  # Reset trigger
    st.rerun()

# Authentication check
if not st.session_state["logged_in"]:
    login()
    st.stop()  # Stop execution until logged in

# Logout button in sidebar
st.sidebar.button("Logout", on_click=trigger_logout)

# Custom CSS to properly position title at the top left without overlapping the table
st.markdown(
    """
    <style>
        .title-container {
            text-align: left;
            font-size: 18px;
            font-weight: bold;
            padding-bottom: 10px;
        }
        .metric-container {
            border: 2px solid #ddd;
            padding: 15px;
            border-radius: 10px;
            background-color: #f9f9f9;
            margin-top: 10px;
        }
    </style>
    """,
    unsafe_allow_html=True
)

# Streamlit App Title
st.markdown("<div class='title-container'>📊 Wharton Street College of Medicine Dashboard</div>", unsafe_allow_html=True)

# Load Data
file_path = os.path.join(os.getcwd(), "Synthetic Dashboard Data.xlsx")
xls = pd.ExcelFile(file_path)
students_df = pd.read_excel(xls, sheet_name="students")
national_comparison_df = pd.read_excel(xls, sheet_name="national_comparison")

# Load Exam Scores Data
exam_sheets = ["CAS", "SE", "NSAS", "USMLE"]
exam_scores_df = pd.concat([pd.read_excel(xls, sheet_name=sheet) for sheet in exam_sheets], ignore_index=True)
test_details_df = pd.read_excel(xls, sheet_name="test_details")

# Merge Exam Scores with Student Data and Test Details
exam_scores_df = exam_scores_df.merge(students_df, on="student_id", how="left")
exam_scores_df = exam_scores_df.merge(test_details_df, on="test_id", how="left")

# Sort student names alphabetically
students_df["full_name"] = students_df["last_name"] + ", " + students_df["first_name"]
students_df = students_df.sort_values(by=["full_name"])
exam_scores_df["full_name"] = exam_scores_df["last_name"] + ", " + exam_scores_df["first_name"]
exam_scores_df = exam_scores_df.sort_values(by=["full_name"])

# Sort student IDs in ascending order
students_df = students_df.sort_values(by=["student_id"])
exam_scores_df = exam_scores_df.sort_values(by=["student_id"])

# Compute Aggregate Exam Statistics
exam_scores_df["exam_year"] = exam_scores_df["test_date"].dt.year
exam_scores_df["pass"] = exam_scores_df.apply(lambda x: 1 if x["test_id"] == "USMLE1" and x["Result"] == "Pass" else 0, axis=1)

aggregate_stats = exam_scores_df.groupby(["test_id", "exam_name", "exam_year", "campus"]).agg(
    mean_score=("Score", "mean"),
    median_score=("Score", "median"),
    sd_score=("Score", "std"),
    min_score=("Score", "min"),
    max_score=("Score", "max"),
    num_students=("student_id", "count"),
    school_pass_rate=("pass", "mean")
).reset_index()
aggregate_stats["school_pass_rate"] = aggregate_stats["school_pass_rate"].round(2)  # Convert to percentage

# Merge with National Comparison Data
aggregate_stats = aggregate_stats.merge(national_comparison_df, on="test_id", how="left")

# Ensure session state keys exist before rendering filters
filter_defaults = {
    "selected_name": "All",
    "selected_id": "All",
    "selected_year": "All",
    "selected_campus": "All",
    "selected_name_exam": "All",
    "selected_id_exam": "All",
    "selected_year_exam": "All",
    "selected_test_id": "All",
    "exam_date_option": "All",
    "selected_exam": "All",
    "selected_exam_year": "All",
    "selected_campus": "All",
    "selected_name_trends": "All",  # Ensure USMLE filters reset correctly
    "selected_id_trends": "All",
    "selected_name_trends_2ck": "All",
    "selected_id_trends_2ck": "All"
}

for key, value in filter_defaults.items():
    if key not in st.session_state:
        st.session_state[key] = value


# Sidebar Navigation ("Student Roster is hidden")
st.sidebar.title("Navigation")
page = st.sidebar.radio("Select a Page", ["Critical KPIs", "Student Exam Scores", "Aggregate Exam Statistics", "USMLE Step 1 Trends", "USMLE Step 2 CK Trends"])

def reset_filters():
    for key, value in filter_defaults.items():
        st.session_state[key] = value
    
    # Reset date inputs separately
    st.session_state["selected_exam_date"] = None
    st.session_state["start_date"] = None
    st.session_state["end_date"] = None
    
    st.rerun()  # Force UI refresh to update dropdowns


if page == "Critical KPIs":
    st.subheader("📊 Critical KPIs")
    
    # ----- Key Subject Exams -----
    st.markdown("### 🧠 Key Comprehensive Subject Exams")
    exams_of_interest = ["CBSE1", "CBSE2", "CCSE"]
    exam_averages = exam_scores_df[exam_scores_df["test_id"].isin(exams_of_interest)].groupby("test_id").agg(
        avg_score=("Score", "mean"),
        num_students=("Score", "count")
    ).reset_index()

    cols = st.columns(len(exam_averages))
    for idx, row in exam_averages.iterrows():
        with cols[idx]:
            st.metric(label=f"{row['test_id']} Average", value=f"{round(row['avg_score'], 1)}")
            st.caption(f"👨‍🎓 {row['num_students']} students")

    # Optional: Bar chart for visual comparison
    fig = px.bar(
        exam_averages,
        x="test_id",
        y="avg_score",
        text="avg_score",
        title="Average Scores by Subject Exam"
    )
    fig.update_traces(texttemplate='%{text:.1f}', textposition='outside')
    fig.update_layout(
        yaxis_title="Average Score",
        xaxis_title="Exam",
        height=300,
        margin=dict(l=20, r=20, t=40, b=20)
    )
    st.plotly_chart(fig, use_container_width=True)

    # ----- USMLE Results -----
    st.markdown("### 🏥 USMLE Exams")
    col1, col2 = st.columns(2)

    # USMLE Step 1 Pass Rate
    with col1:
        usmle1_data = exam_scores_df[exam_scores_df["test_id"] == "USMLE1"]
        usmle1_pass_rate = (usmle1_data["pass"].mean() * 100) if not usmle1_data.empty else 0
        usmle1_students = usmle1_data.shape[0]
        st.metric(label="USMLE Step 1 Pass Rate", value=f"{round(usmle1_pass_rate, 1)}%")
        st.caption(f"🧑‍⚕️ {usmle1_students} students")

    # USMLE Step 2 CK Average Score
    with col2:
        usmle2ck_data = exam_scores_df[exam_scores_df["test_id"] == "USMLE2CK"]
        usmle2ck_avg_score = usmle2ck_data["Score"].mean() if not usmle2ck_data.empty else 0
        usmle2ck_students = usmle2ck_data.shape[0]
        st.metric(label="USMLE Step 2 CK Avg Score", value=f"{round(usmle2ck_avg_score, 1)}")
        st.caption(f"👩‍⚕️ {usmle2ck_students} students")

if page == "Student Roster":
    st.sidebar.title("Filters")
    if st.sidebar.button("Reset Filters"):
        reset_filters()
    student_names_sorted = sorted(list(exam_scores_df["full_name"].unique()), key=lambda x: x.split(", ")[0])
    selected_name = st.sidebar.selectbox("Select Student Name", ["All"] + student_names_sorted, key="selected_name")
    selected_id = st.sidebar.selectbox("Select Student ID", ["All"] + sorted(students_df["student_id"].unique()), key="selected_id")
    selected_year = st.sidebar.selectbox("Select Year of Study", ["All"] + sorted(students_df["year"].unique()), key="selected_year")
    selected_campus = st.sidebar.selectbox("Select Campus", ["All"] + sorted(students_df["campus"].unique()), key="selected_campus")
    
    filtered_df = students_df.copy()
    if selected_name != "All":
        filtered_df = filtered_df[filtered_df["full_name"] == selected_name]
    if selected_id != "All":
        filtered_df = filtered_df[filtered_df["student_id"] == int(selected_id)]
    if selected_year != "All":
        filtered_df = filtered_df[filtered_df["year"] == int(selected_year)]
    if selected_campus != "All":
        filtered_df = filtered_df[filtered_df["campus"] == selected_campus]
    st.subheader("📜 School Roster")
    st.dataframe(filtered_df[["student_id", "first_name", "last_name", "year", "campus"]])

elif page == "Student Exam Scores":
    st.sidebar.title("Filters")
    if st.sidebar.button("Reset Filters"):
        reset_filters()

    student_names_sorted = sorted(list(exam_scores_df["full_name"].unique()), key=lambda x: x.split(", ")[0])
    selected_name = st.sidebar.selectbox("Select Student Name", ["All"] + student_names_sorted, key="selected_name")
    selected_id = st.sidebar.selectbox("Select Student ID", ["All"] + sorted(exam_scores_df["student_id"].unique()), key="selected_id_exam")
    selected_year = st.sidebar.selectbox("Select Year of Study", ["All"] + sorted(exam_scores_df["year"].unique()), key="selected_year_exam")
    selected_test_id = st.sidebar.selectbox("Select Test ID", ["All"] + sorted(exam_scores_df["test_id"].unique()), key="selected_test_id")

    # ✅ Define `exam_date_option` inside this block only
    exam_date_option = st.sidebar.radio("Filter by Exam Date", ["All", "Exact Date", "Date Range"], key="exam_date_option")

    # ✅ Initialize date variables inside this block
    selected_exam_date = None
    start_date = None
    end_date = None

    if exam_date_option == "Exact Date":
        selected_exam_date = st.sidebar.date_input("Select Exam Date", key="selected_exam_date")

    elif exam_date_option == "Date Range":
        start_date = st.sidebar.date_input("Start Date", key="start_date")
        end_date = st.sidebar.date_input("End Date", key="end_date")

    # ✅ Filtering Logic
    filtered_df = exam_scores_df.copy()

    if selected_name != "All":
        filtered_df = filtered_df[filtered_df["full_name"] == selected_name]
    if selected_id != "All":
        filtered_df = filtered_df[filtered_df["student_id"] == int(selected_id)]
    if selected_year != "All":
        filtered_df = filtered_df[filtered_df["year"] == int(selected_year)]
    if selected_test_id != "All":
        filtered_df = filtered_df[filtered_df["test_id"] == selected_test_id]

    # ✅ Apply filters only if necessary
    if exam_date_option == "Exact Date" and selected_exam_date:
        filtered_df = filtered_df[filtered_df["test_date"] == pd.to_datetime(selected_exam_date)]

    if exam_date_option == "Date Range" and start_date and end_date:
        filtered_df = filtered_df[
            (filtered_df["test_date"] >= pd.to_datetime(start_date)) &
            (filtered_df["test_date"] <= pd.to_datetime(end_date))
        ]

    st.subheader("📝 Student Exam Scores")

    # ✅ Updated: Added "campus" column to the displayed DataFrame
    st.dataframe(filtered_df[[
        "student_id", "first_name", "last_name", "year", "campus",  # <- Added "campus"
        "test_id", "exam_name", "Score", "Result", "test_date"
    ]])


if page == "USMLE Step 1 Trends":
    st.sidebar.title("Filters")
    if st.sidebar.button("Reset Filters"):
        reset_filters()
    
    # Filters for Student Name and Student ID
    student_names_sorted = sorted(list(exam_scores_df["full_name"].unique()), key=lambda x: x.split(", ")[0])
    selected_name = st.sidebar.selectbox("Select Student Name", ["All"] + student_names_sorted, key="selected_name")
    selected_id = st.sidebar.selectbox("Select Student ID", ["All"] + sorted(exam_scores_df["student_id"].unique()), key="selected_id_trends")
    
    # Filter dataset for USMLE-related tests
    usmle_tests = ["CBSE1", "CBSSA1", "CBSE2", "CBSSA2", "USMLE1"]
    filtered_df = exam_scores_df[exam_scores_df["test_id"].isin(usmle_tests)].copy()
    
    # Apply Filters
    if selected_name != "All":
        filtered_df = filtered_df[filtered_df["full_name"] == selected_name]
    if selected_id != "All":
        filtered_df = filtered_df[filtered_df["student_id"] == int(selected_id)]
    
    # Display selected student's name and ID regardless of filter choice
    if not filtered_df.empty:
        student_info = filtered_df.iloc[0]
        st.markdown(f"### Selected Student: {student_info['full_name']} (ID: {student_info['student_id']})")
    
    # Display student USMLE Step 1 Result if available
    usmle_result = filtered_df[filtered_df["test_id"] == "USMLE1"]
    if not usmle_result.empty:
        usmle_result_text = usmle_result.iloc[0]["Result"]
        usmle_date = usmle_result.iloc[0]["test_date"]
        
        st.markdown(f"### USMLE Step 1 Result: {usmle_result_text}")
        if not pd.isna(usmle_date):
            st.markdown(f"### USMLE Step 1 Test Date: {usmle_date.strftime('%Y-%m-%d')}")
    else:
        st.markdown("### USMLE Step 1 has not been taken yet")
    
    # Remove USMLE1 from the score trends plot since it doesn't have numeric scores
    filtered_df = filtered_df[filtered_df["test_id"] != "USMLE1"]
    
    # Plot score trends over time with custom colors
    if not filtered_df.empty:
        fig = px.line(
            filtered_df, x="test_date", y="Score", color="test_id",
            markers=True, title="USMLE Step 1 Preparation Score Trends"
        )

        # Define custom colors for CBSSA1 & CBSSA2 (blue), CBSE1 & CBSE2 (red)
        color_map = {
            "CBSSA1": "blue",
            "CBSSA2": "blue",
            "CBSE1": "red",
            "CBSE2": "red"
        }

        # Update traces with custom colors
        for trace in fig.data:
            test_id = trace.name  # Extract test_id (legend name)
            if test_id in color_map:
                trace.marker.color = color_map[test_id]

        # Increase marker size for better visibility
        fig.update_traces(marker=dict(size=12))

        # Adjust figure size and layout
        fig.update_layout(
            xaxis_title="Exam Date",
            yaxis_title="Score",
            legend_title="Exam Type",
            width=1000,
            height=600,
            margin=dict(l=50, r=50, t=50, b=50),
        )

        st.plotly_chart(fig, use_container_width=True)  # Expands to available space in Streamlit
    else:
        st.warning("No data available for the selected filters.")


if page == "USMLE Step 2 CK Trends":
    st.sidebar.title("Filters")
    if st.sidebar.button("Reset Filters"):
        reset_filters()
    
    # Filters for Student Name and Student ID
    student_names_sorted = sorted(list(exam_scores_df["full_name"].unique()), key=lambda x: x.split(", ")[0])
    selected_name = st.sidebar.selectbox("Select Student Name", ["All"] + student_names_sorted, key="selected_name")
    selected_id = st.sidebar.selectbox("Select Student ID", ["All"] + sorted(exam_scores_df["student_id"].unique()), key="selected_id_trends_2ck")
    
    # ✅ Ensure CCSE is included
    usmle_tests_2ck = ["CCSSA", "CCSE", "CCSE", "USMLE2CK"]
    filtered_df = exam_scores_df[exam_scores_df["test_id"].isin(usmle_tests_2ck)].copy()
    
    # Apply Filters
    if selected_name != "All":
        filtered_df = filtered_df[filtered_df["full_name"] == selected_name]
    if selected_id != "All":
        filtered_df = filtered_df[filtered_df["student_id"] == int(selected_id)]

    # Debugging: Check if CCSSA, CCSE, and USMLE2CK appear
    st.write("Filtered Test IDs:", filtered_df["test_id"].unique())

    # Display selected student's name and ID
    if not filtered_df.empty:
        student_info = filtered_df.iloc[0]
        st.markdown(f"### Selected Student: {student_info['full_name']} (ID: {student_info['student_id']})")
    
    # Display student USMLE Step 2 CK Score if available
    usmle_result = filtered_df[filtered_df["test_id"] == "USMLE2CK"]
    if not usmle_result.empty:
        usmle_score = usmle_result.iloc[0]["Score"] if pd.notna(usmle_result.iloc[0]["Score"]) else "No recorded score"
        usmle_date = usmle_result.iloc[0]["test_date"]
        
        st.markdown(f"### USMLE Step 2 CK Score: {usmle_score}")
        if pd.notna(usmle_date):
            st.markdown(f"### USMLE Step 2 CK Test Date: {usmle_date.strftime('%Y-%m-%d')}")
    else:
        st.markdown("### USMLE Step 2 CK has not been taken yet")
    
    # Plot score trends over time
    if not filtered_df.empty:
        fig = px.line(
            filtered_df, x="test_date", y="Score", color="test_id",
            markers=True, title="USMLE Step 2 CK Preparation Score Trends"
        )

        # ✅ Define custom colors
        color_map = {
            "CCSSA": "blue",   # 🔵 CCSSA
            "CCSE": "red",      # 🔴 CCSE
            "USMLE2CK": "green" # 🟢 USMLE2CK
        }

        # ✅ Apply custom colors
        for trace in fig.data:
            test_id = trace.name  # Extract test_id (legend name)
            if test_id in color_map:
                trace.marker.color = color_map[test_id]

        # Increase marker size for better visibility
        fig.update_traces(marker=dict(size=12))  

        # Adjust figure size and layout
        fig.update_layout(
            xaxis_title="Exam Date",
            yaxis_title="Score",
            legend_title="Exam Type",
            width=1000,
            height=600,
            margin=dict(l=50, r=50, t=50, b=50),
        )

        st.plotly_chart(fig, use_container_width=True)
    else:
        st.warning("No data available for the selected filters.")

elif page == "Aggregate Exam Statistics":
    st.sidebar.title("Filters")
    if st.sidebar.button("Reset Filters"):
        reset_filters()
    selected_exam = st.sidebar.selectbox("Select Exam", ["All"] + sorted(aggregate_stats["test_id"].unique()), key="selected_exam")
    selected_exam_year = st.sidebar.selectbox("Select Exam Year", ["All"] + sorted(aggregate_stats["exam_year"].unique()), key="selected_exam_year")
    selected_campus = st.sidebar.selectbox("Select Campus", ["All", "Both"] + sorted(aggregate_stats["campus"].unique()), key="selected_campus")
    
    # Apply Filters
    filtered_df = aggregate_stats.copy()
    if selected_exam != "All":
        filtered_df = filtered_df[filtered_df["test_id"] == selected_exam]
    if selected_exam_year != "All":
        filtered_df = filtered_df[filtered_df["exam_year"] == int(selected_exam_year)]
    if selected_campus == "Both":
        filtered_df = filtered_df.groupby(["test_id", "exam_name", "exam_year"]).agg(
            mean_score=("mean_score", "mean"),
            median_score=("median_score", "median"),
            sd_score=("sd_score", "mean"),
            min_score=("min_score", "min"),
            max_score=("max_score", "max"),
            num_students=("num_students", "sum"),
            school_pass_rate=("school_pass_rate", "mean"),
            natl_mean=("natl_mean", "mean"),
            natl_sd=("natl_sd", "mean"),
            natl_perc25=("natl_perc25", "mean"),
            natl_perc50=("natl_perc50", "mean"),
            natl_perc75=("natl_perc75", "mean"),
            natl_pass_rate=("natl_pass_rate", "mean")
        ).reset_index()
        filtered_df["campus"] = "Both"
    elif selected_campus != "All":
        filtered_df = filtered_df[filtered_df["campus"] == selected_campus]
    
    st.subheader("📊 Aggregate Exam Statistics")
    st.dataframe(filtered_df[[
        "test_id", "exam_name", "exam_year", "campus", "mean_score", "median_score", "sd_score",
        "min_score", "max_score", "num_students", "school_pass_rate", "natl_mean", "natl_sd", "natl_perc25", "natl_perc50", "natl_perc75", "natl_pass_rate"
    ]])
    
    # Add Field Descriptions Note
    st.markdown("""
    **Field Descriptions:**
    - **School-Level Metrics:** mean_score, median_score, sd_score, min_score, max_score, num_students, school_pass_rate
    - **National-Level Metrics:** natl_mean (national), natl_sd (national), natl_perc25, natl_perc50, natl_perc75, natl_pass_rate
    """)
    






