import streamlit as st
import pandas as pd

st.set_page_config(page_title="Doctor Referral Automation", layout="wide")

st.title("🏥 Doctor Referral Payout Calculator (Official Logic)")

# 1. Define the "Payable Doctors" list based on the Result Sheet
# This ensures only your boss's selected doctors get paid.
PAYABLE_DOCTORS = [
    "JINIA PAUL", 
    "ARJUN DASGUPTA", 
    "LIPIKA DAS MUKHOPADHYAY", 
    "LIPIKA DAS MUKHERJEE", 
    "LIPIKA DAS (MUKHOPADHYAY)",
    "N V K MOHAN",
    "CAPT A K SAHA"
]

uploaded_file = st.file_uploader("Upload Referral CSV or Excel", type=['csv', 'xlsx'])

if uploaded_file is not None:
    # Load data
    df = pd.read_csv(uploaded_file) if uploaded_file.name.endswith('.csv') else pd.read_excel(uploaded_file)
    
    # Standardize Column Names
    df.columns = df.columns.str.strip()

    # Calculation Logic
    def calculate_referral_logic(row):
        try:
            gross = float(row['Gross Amount'])
            discount = float(row['Discount'])
            net = float(row['Net Amount'])
            doc_name = str(row['DoctorName']).upper().strip()
            
            if gross <= 0: return 0, 0
            
            disc_pct = discount / gross
            
            # Theoretical Referral (Doc Ref column in boss's sheet)
            doc_ref = (0.25 - disc_pct) * net if disc_pct < 0.25 else 0
            
            # Net Payable (Only if doctor is in the approved list)
            net_payable = doc_ref if any(name in doc_name for name in PAYABLE_DOCTORS) else 0
            
            return round(doc_ref, 2), round(net_payable, 2)
        except:
            return 0, 0

    # Apply Logic
    df[['Doc Ref', 'Net Payable']] = df.apply(
        lambda x: pd.Series(calculate_referral_logic(x)), axis=1
    )

    # Sidebar Filters
    st.sidebar.header("Filters")
    if 'DATE' in df.columns:
        df['DATE'] = pd.to_datetime(df['DATE'], errors='coerce')
        months = df['DATE'].dt.strftime('%B %Y').dropna().unique()
        selected_month = st.sidebar.selectbox("Select Month", months)
        display_df = df[df['DATE'].dt.strftime('%B %Y') == selected_month]
    else:
        display_df = df

    # Summary Dashboard
    total_payout = display_df['Net Payable'].sum()
    st.metric("Total Net Payable to Approved Doctors", f"₹{total_payout:,.2f}")

    # Payout Table (Summary by Doctor)
    st.subheader("Summary Payout Table")
    summary = display_df.groupby('DoctorName')['Net Payable'].sum().reset_index()
    summary = summary[summary['Net Payable'] > 0].sort_values(by='Net Payable', ascending=False)
    st.table(summary)

    # Detailed Table
    with st.expander("View Full Calculation Details"):
        st.dataframe(display_df)

    # Download
    csv = display_df.to_csv(index=False).encode('utf-8')
    st.download_button("Download Processed Result", data=csv, file_name="Final_Referral_Payouts.csv")
