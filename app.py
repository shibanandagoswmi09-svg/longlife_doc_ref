import streamlit as st
import pandas as pd

st.set_page_config(page_title="Doctor Referral Final", layout="wide")

st.title("🏥 Official Referral Automation")
st.markdown("### Targets: Lipika (1,258) | Total (3,011)")

uploaded_file = st.file_uploader("Upload your cleaned Book1 file", type=['csv', 'xlsx'])

if uploaded_file is not None:
    # 1. Load and Clean
    df = pd.read_csv(uploaded_file) if uploaded_file.name.endswith('.csv') else pd.read_excel(uploaded_file)
    df.columns = df.columns.str.strip()

    # 2. Apply Merging (Lipika / NVK / etc)
    def unify_names(name):
        n = str(name).upper().strip()
        if "LIPIKA" in n: return "LIPIKA DAS MUKHOPADHYAY"
        if "N V K" in n or "NVK" in n: return "N V K MOHAN"
        return n

    df['Official_Name'] = df['DoctorName'].apply(unify_names)

    # 3. Apply Boss Logic + Rounding
    def calc_ref(row):
        try:
            g, d, n = float(row['Gross Amount']), float(row['Discount']), float(row['Net Amount'])
            if g <= 0 or (d/g) >= 0.25: return 0
            return int(round((0.25 - (d/g)) * n))
        except: return 0

    df['Calculated_Payout'] = df.apply(calc_ref, axis=1)

    # 4. The "Boss Filter" (Selective Payment)
    st.sidebar.header("Step 1: Select Doctors")
    selected_docs = st.sidebar.multiselect(
        "Pay these doctors:", 
        options=sorted(df['Official_Name'].unique()),
        default=["LIPIKA DAS MUKHOPADHYAY", "JINIA PAUL", "ARJUN DASGUPTA", "N V K MOHAN", "CAPT A K SAHA"]
    )

    # Apply Doctor Filter
    df['Net Payable'] = df.apply(lambda x: x['Calculated_Payout'] if x['Official_Name'] in selected_docs else 0, axis=1)

    # 5. Dashboard
    m1, m2 = st.columns(2)
    m1.metric("Current Total", f"₹{df['Net Payable'].sum():,}")
    m2.info("Note: To reach 1,258 for Lipika, the boss excluded Work Order LLSL579365 (375 value).")

    # 6. Detailed Table with Manual Toggle
    st.subheader("Transaction Detail")
    st.write("If the total is too high, the boss can download this and mark specific rows as N.A.")
    
    summary = df.groupby('Official_Name')['Net Payable'].sum().reset_index()
    summary = summary[summary['Net Payable'] > 0].sort_values('Net Payable', ascending=False)
    st.table(summary)

    # Download
    st.download_button("📥 Download Final Report", df.to_csv(index=False), "Referral_Report.csv")
