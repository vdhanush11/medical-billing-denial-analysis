
# 📌 Medical Billing Denial Analysis App

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import streamlit as st
from fuzzywuzzy import fuzz

# 1️⃣ Robust Loader + Preprocessor

def load_and_preprocess(file):
    import io

    # Read raw content first
    content = file.read()
    file.seek(0)  # Reset pointer after reading

    # Convert to pandas with no header to analyze
    try:
        preview = pd.read_csv(io.BytesIO(content) if isinstance(content, bytes) else io.StringIO(content),
                              header=None, nrows=20, engine='python')
    except Exception:
        preview = pd.read_excel(io.BytesIO(content) if isinstance(content, bytes) else io.StringIO(content),
                                header=None, nrows=20)

    # Detect first row with enough non-empty cells
    header_row = 0
    for i, row in preview.iterrows():
        if row.dropna().shape[0] >= 2:
            header_row = i
            break

    # Read full file with header_row
    try:
        if file.name.endswith(".csv"):
            df = pd.read_csv(file, header=header_row, engine='python')
        else:
            df = pd.read_excel(file, header=header_row)
    except pd.errors.EmptyDataError:
        st.error("⚠️ No valid data found in this file.")
        return pd.DataFrame(), {}

    # Clean column names
    df.columns = (
        df.columns.astype(str)
        .str.strip()
        .str.replace("#", "")
        .str.replace("\n", "")
        .str.replace(" ", "_")
        .str.lower()
    )

    # --- Fuzzy matching & preprocessing (same as before) ---
    standard_cols = {
        "CPT_Code": ["cpt", "cpt_code", "procedure"],
        "Insurance_Company": ["insurance", "payer", "insurance_company"],
        "Physician_Name": ["physician", "provider", "doctor", "physician_name"],
        "Payment_Amount": ["payment", "paid", "payment_amount", "amount_paid"],
        "Balance": ["balance", "amt_due", "outstanding", "due"],
        "Denial_Reason": ["denial", "reason", "denial_reason"],
    }

    detected_mapping = {}
    from fuzzywuzzy import fuzz
    for std_col, variants in standard_cols.items():
        best_match = None
        highest_ratio = 0
        for col in df.columns:
            for var in variants:
                ratio = fuzz.ratio(col.lower(), var.lower())
                if ratio > highest_ratio:
                    highest_ratio = ratio
                    best_match = col
        if highest_ratio >= 70:
            df.rename(columns={best_match: std_col}, inplace=True)
            detected_mapping[std_col] = best_match
        else:
            detected_mapping[std_col] = "MISSING"

    # Numeric columns
    for col in ["Payment_Amount", "Balance"]:
        if col in df.columns:
            df[col] = (
                df[col]
                .astype(str)
                .str.replace(r"[\$,]", "", regex=True)
                .replace("", "0")
                .astype(float)
            )
        else:
            df[col] = 0.0

    # Denied flag
    if "Denial_Reason" in df.columns:
        df["Denied"] = df["Denial_Reason"].notnull().astype(int)
    else:
        df["Denied"] = (df["Payment_Amount"] == 0).astype(int)

    return df, detected_mapping



# 2️⃣ Insights Functions

def identify_top_denials(df):
    if "CPT_Code" not in df.columns:
        return None
    cpt_summary = df.groupby("CPT_Code").agg(
        claims=("Denied", "count"),
        denials=("Denied", "sum"),
        denial_rate=("Denied", "mean"),
    )
    cpt_summary["denial_rate"] *= 100
    return cpt_summary.sort_values("denial_rate", ascending=False)

def detect_root_causes(df):
    if "Denial_Reason" not in df.columns:
        return ["⚠️ No Denial_Reason column found"]
    reasons = df["Denial_Reason"].dropna().value_counts()
    insights = []
    for reason, count in reasons.items():
        if "modifier" in reason.lower():
            insights.append("Modifier issue → Fix: Add correct CPT modifiers.")
        elif "lcd" in reason.lower() or "ncd" in reason.lower():
            insights.append("LCD/NCD mismatch → Fix: Validate coverage policies.")
        elif "bundling" in reason.lower() or "ncci" in reason.lower():
            insights.append("Bundling edits (NCCI) → Fix: Use coding scrubber tools.")
        elif "documentation" in reason.lower() or "missing" in reason.lower():
            insights.append("Lack of documentation → Fix: Improve provider documentation.")
        elif "auth" in reason.lower():
            insights.append("Prior authorization → Fix: Verify payer requirements.")
        elif "credential" in reason.lower():
            insights.append("Credentialing issue → Fix: Verify provider enrollment.")
        elif "fee schedule" in reason.lower():
            insights.append("Charge exceeds fee schedule → Fix: Review payer contracts.")
        elif "non-covered" in reason.lower():
            insights.append("Non-covered service → Fix: Verify coverage before billing.")
    return insights if insights else ["• No major root causes detected."]

def recommend_strategies():
    return [
        "✔ Ensure correct CPT modifiers are applied.",
        "✔ Validate claims against payer LCD/NCD policies before submission.",
        "✔ Use coding scrubber tools to catch bundling edits (NCCI).",
        "✔ Improve provider documentation.",
        "✔ Confirm prior authorization requirements.",
        "✔ Verify provider credentialing and enrollment with each payer.",
        "✔ Educate front desk on capturing complete patient/insurance info.",
        "✔ Establish payer-specific denial appeal templates.",
    ]


# 3️⃣ Streamlit UI

st.title("📊 Medical Billing Denial Analysis")
uploaded_file = st.file_uploader("Upload CSV or Excel", type=["csv", "xlsx"])

if uploaded_file:
    df, detected_mapping = load_and_preprocess(uploaded_file)

    st.success(f"✅ Data loaded successfully! Shape: {df.shape}")

    with st.expander("🔎 Data Diagnostics"):
        st.write("Detected column mapping (standard → original):")
        st.json(detected_mapping)
        st.write("Columns after cleanup:")
        st.write(df.columns.tolist())
        st.write("Data preview:")
        st.dataframe(df.head())

  
    # 1️⃣ Identify Top Denied CPT Codes
  
    st.subheader("1️⃣ Identify Top Denied CPT Codes")
    cpt_summary = identify_top_denials(df)
    if cpt_summary is not None and not cpt_summary.empty:
        st.dataframe(cpt_summary.head(10))

        col1, col2 = st.columns(2)

        with col1:
            fig, ax = plt.subplots(figsize=(6, 4))
            cpt_summary["denial_rate"].sort_values(ascending=False).head(10).plot(
                kind="bar", ax=ax, color="tomato"
            )
            ax.set_ylabel("Denial Rate (%)")
            ax.set_title("Top CPT Codes by Denial Rate")
            plt.xticks(rotation=45, ha="right")
            st.pyplot(fig)

        with col2:
            fig, ax = plt.subplots(figsize=(6, 4))
            cpt_summary["denials"].sort_values(ascending=False).head(10).plot(
                kind="bar", ax=ax, color="orange"
            )
            ax.set_ylabel("Denials")
            ax.set_title("Top CPT Codes by Denial Count")
            plt.xticks(rotation=45, ha="right")
            st.pyplot(fig)
    else:
        st.warning("⚠️ CPT_Code column not found, skipping CPT analysis.")

    
    # 2️⃣ Detect Root Causes

    st.subheader("2️⃣ Detect Root Causes")
    insights = detect_root_causes(df)
    for item in insights:
        st.write(item)

  
    # 3️⃣ Recommend Fixes & Strategies
    
    st.subheader("3️⃣ Recommend Fixes & Strategies")
    for rec in recommend_strategies():
        st.write(rec)

    # 4️⃣ Visual Reports

    st.subheader("4️⃣ Visual Reports")

    if "Insurance_Company" in df.columns:
        payer_summary = df.groupby("Insurance_Company")["Denied"].mean() * 100
        fig, ax = plt.subplots(figsize=(6, 4))
        payer_summary.sort_values(ascending=False).plot(kind="bar", ax=ax, color="skyblue")
        ax.set_ylabel("Denial Rate (%)")
        ax.set_title("Denial Rates by Payer")
        plt.xticks(rotation=45, ha="right")
        st.pyplot(fig)

    if "Physician_Name" in df.columns:
        provider_summary = df.groupby("Physician_Name")["Denied"].mean() * 100
        fig, ax = plt.subplots(figsize=(6, 4))
        provider_summary.sort_values(ascending=False).plot(
            kind="bar", ax=ax, color="lightgreen"
        )
        ax.set_ylabel("Denial Rate (%)")
        ax.set_title("Denial Rates by Provider")
        plt.xticks(rotation=45, ha="right")
        st.pyplot(fig)

    if "Insurance_Company" in df.columns:
        lost_revenue = df.groupby("Insurance_Company")["Balance"].sum()
        fig, ax = plt.subplots(figsize=(6, 4))
        lost_revenue.sort_values(ascending=False).plot(kind="bar", ax=ax, color="red")
        ax.set_ylabel("Lost Revenue ($)")
        ax.set_title("Lost Revenue by Payer")
        plt.xticks(rotation=45, ha="right")
        st.pyplot(fig)

    if "CPT_Code" in df.columns and "Insurance_Company" in df.columns:
        pivot = df.pivot_table(
            index="CPT_Code", columns="Insurance_Company", values="Denied", aggfunc="mean"
        )
        fig, ax = plt.subplots(figsize=(8, 6))
        sns.heatmap(pivot * 100, annot=True, fmt=".1f", cmap="Reds", ax=ax)
        ax.set_title("Denial Rates Heatmap (CPT vs Payer)")
        st.pyplot(fig)
