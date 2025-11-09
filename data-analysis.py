import streamlit as st
import pandas as pd
import re

st.title("Smart Excel Data Analyzer")

uploaded_file = st.file_uploader("Upload Excel File", type=["xlsx", "xls"])


def detect_column_type(values):
    email_pattern = r"[^@]+@[^@]+\.[^@]+"
    date_candidates = 0
    email_candidates = 0
    numeric_candidates = 0

    for v in values:
        if pd.isnull(v):
            continue
        v = str(v).strip()

        if re.match(email_pattern, v):
            email_candidates += 1
        try:
            pd.to_datetime(v)
            date_candidates += 1
        except:
            pass
        if v.isdigit():
            numeric_candidates += 1

    if email_candidates > len(values) * 0.5:
        return "email"
    if date_candidates > len(values) * 0.4:
        return "date"
    if numeric_candidates > len(values) * 0.6:
        return "number"
    return "text"


def validate_df(df):
    issues = []

    for col in df.columns:
        col_type = detect_column_type(df[col])

        for idx, val in df[col].items():
            sval = str(val).strip() if pd.notnull(val) else ""

            if pd.isnull(val) or sval == "":
                issues.append([idx+1, col, sval, "Missing Value"])
                continue

            if col_type == "email" and not re.match(r"[^@]+@[^@]+\.[^@]+", sval):
                issues.append([idx+1, col, sval, "Invalid Email Format"])

            if col_type == "date":
                try:
                    pd.to_datetime(sval)
                except:
                    issues.append([idx+1, col, sval, "Invalid Date Format"])

            if col_type == "number":
                if not sval.replace(".", "", 1).isdigit():
                    issues.append([idx+1, col, sval, "Non-Numeric Value"])

    return pd.DataFrame(issues, columns=["Row", "Column", "Value", "Issue"])


if uploaded_file:
    df = pd.read_excel(uploaded_file)
    st.success("✅ File Loaded")
    st.dataframe(df)

    issues_df = validate_df(df)

    st.subheader("🔎 Detailed Row Level Issues")
    if issues_df.empty:
        st.success("✅ No issues found!")
    else:
        st.dataframe(issues_df)

        # Column Summary with Issue Types
        summary = issues_df.groupby("Column").agg(
            Issues_Found=("Issue", "count"),
            Unique_Issues=("Issue", lambda x: ", ".join(sorted(set(x)))),
        ).reset_index()

        summary["Total Rows"] = len(df)
        summary["% Bad"] = (summary["Issues_Found"] / summary["Total Rows"] * 100).round(2)

        st.subheader("📊 Column Quality Summary (With Bad Data Description)")
        st.dataframe(summary)

        st.download_button(
            "Download Detailed Issue Report",
            data=issues_df.to_csv(index=False),
            file_name="issue_details.csv",
            mime="text/csv"
        )

        st.download_button(
            "Download Column Summary Report",
            data=summary.to_csv(index=False),
            file_name="column_summary.csv",
            mime="text/csv"
        )
