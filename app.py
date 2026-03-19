import streamlit as st
import pandas as pd

st.set_page_config(page_title="Dynamic Referral System", layout="wide")

st.title("🏥 Dynamic Doctor Referral Calculator")
st.info("Upload any monthly file. The system will detect doctors and apply the 25% logic automatically.")

uploaded_file = st.file_uploader("Upload Referral File (CSV or Excel)", type=['csv', 'xlsx'])

if uploaded_file is not None:
    # 1. Load Data Dynamically
    if uploaded_file.name.endswith('.csv'):
        df = pd.read_csv(uploaded_file)
    else:
        df = pd.read_excel(uploaded_file)
    
    # Clean column names to prevent errors if there are hidden spaces
    df.columns = df.columns.str.strip()

    # 2. Automated Logic Function
    def apply_referral_logic(row):
        try:
            gross = float(row['Gross Amount'])
            discount = float(row['Discount'])
            net = float(row['Net Amount'])
            
            if gross <= 0: return 0
            
            # Logic: (25% - Actual Discount %) * Net
            disc_pct = discount / gross
            if disc_pct < 0.25:
                return (0.25 - disc_pct) * net
            return 0
        except:
            return 0

    # Calculate 'Potential Referral' for EVERY row first
    df['Potential Referral'] = df.apply(apply_referral_logic, axis=1)

    # 3. Dynamic Doctor Selection (The "Future-Proof" Part)
    # This detects every unique doctor name in the uploaded file
    all_doctors = sorted(df['DoctorName'].unique())
    
    st.sidebar.header("Settings")
    selected_payables = st.sidebar.multiselect(
        "Select Doctors to Pay (White List):", 
        options=all_doctors,
        default=[d for d in all_doctors if d in ["JINIA PAUL", "ARJUN DASGUPTA", "N V K MOHAN"]] # Pre-select known ones
    )

    # 4. Filter and Finalize
    # Set Net Payable to 0 if the doctor isn't selected in the sidebar
    df['Net Payable'] = df.apply(
        lambda x: x['Potential Referral'] if x['DoctorName'] in selected_payables else 0, 
        axis=1
    )

    # 5. Display Dashboard
    m1, m2, m3 = st.columns(3)
    m1.metric("Total Gross", f"₹{df['Gross Amount'].sum():,.2f}")
    m2.metric("Total Net Amount", f"₹{df['Net Amount'].sum():,.2f}")
    m3.metric("Total Payout (Selected)", f"₹{df['Net Payable'].sum():,.2f}", delta_color="normal")

    st.subheader("Summary by Doctor")
    summary = df.groupby('DoctorName').agg({
        'Gross Amount': 'sum',
        'Net Amount': 'sum',
        'Net Payable': 'sum'
    }).reset_index()
    
    # Show only those with a payout or those selected
    summary_view = summary[summary['Net Payable'] > 0].sort_values(by='Net Payable', ascending=False)
    st.dataframe(summary_view, use_container_width=True)

    # 6. Export Feature
    st.subheader("Export Result")
    final_csv = df.to_csv(index=False).encode('utf-8')
    st.download_button(
        label="📥 Download Processed Report for Boss",
        data=final_csv,
        file_name=f"Processed_Referral_{uploaded_file.name}",
        mime='text/csv'
    )
