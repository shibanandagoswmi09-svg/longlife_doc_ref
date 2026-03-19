import streamlit as st
import pandas as pd
import re

st.set_page_config(page_title="Dynamic Referral System", layout="wide")

st.title("🏥 Doctor Referral Calculator (With Name Merging)")

uploaded_file = st.file_uploader("Upload Referral File (CSV or Excel)", type=['csv', 'xlsx'])

if uploaded_file is not None:
    # 1. Load Data
    df = pd.read_csv(uploaded_file) if uploaded_file.name.endswith('.csv') else pd.read_excel(uploaded_file)
    df.columns = df.columns.str.strip()

    # 2. Name Normalization Function (THE FIX)
    def clean_doctor_name(name):
        name = str(name).upper().strip()
        # Regex to catch variations: Lipika + Muk...
        if "LIPIKA" in name and ("MUKH" in name or "DAS" in name):
            return "LIPIKA DAS MUKHOPADHYAY"
        # Add other merges here if needed
        return name

    # Apply the name merging
    df['DoctorName_Cleaned'] = df['DoctorName'].apply(clean_doctor_name)

    # 3. Automated Logic Function
    def apply_referral_logic(row):
        try:
            gross = float(row['Gross Amount'])
            discount = float(row['Discount'])
            net = float(row['Net Amount'])
            if gross <= 0: return 0
            
            disc_pct = discount / gross
            return (0.25 - disc_pct) * net if disc_pct < 0.25 else 0
        except:
            return 0

    df['Potential Referral'] = df.apply(apply_referral_logic, axis=1)

    # 4. Dynamic Doctor Selection
    all_doctors = sorted(df['DoctorName_Cleaned'].unique())
    
    st.sidebar.header("Payment Settings")
    # We pre-select the 'merged' name for the boss
    selected_payables = st.sidebar.multiselect(
        "Check Doctors to Pay:", 
        options=all_doctors,
        default=["LIPIKA DAS MUKHOPADHYAY", "JINIA PAUL", "ARJUN DASGUPTA"]
    )

    # 5. Final Calculation
    df['Net Payable'] = df.apply(
        lambda x: x['Potential Referral'] if x['DoctorName_Cleaned'] in selected_payables else 0, 
        axis=1
    )

    # 6. Display Dashboard
    
    
    m1, m2, m3 = st.columns(3)
    m1.metric("Total Patients", len(df))
    m2.metric("Total Payout", f"₹{df['Net Payable'].sum():,.2f}")
    m3.metric("Doctors Being Paid", len(selected_payables))

    st.subheader("Final Summary (Merged Names)")
    summary = df.groupby('DoctorName_Cleaned').agg({
        'Gross Amount': 'sum',
        'Net Amount': 'sum',
        'Net Payable': 'sum'
    }).reset_index()
    
    summary_view = summary[summary['Net Payable'] > 0].sort_values(by='Net Payable', ascending=False)
    st.table(summary_view)

    # 7. Export
    st.subheader("Export Result")
    final_csv = df.to_csv(index=False).encode('utf-8')
    st.download_button(
        label="📥 Download Corrected Report",
        data=final_csv,
        file_name=f"Corrected_Referral_{uploaded_file.name}",
        mime='text/csv'
    )
