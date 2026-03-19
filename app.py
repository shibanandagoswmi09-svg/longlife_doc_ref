import streamlit as st
import pandas as pd

st.set_page_config(page_title="Doctor Referral Automation", layout="wide")

st.title("🏥 Doctor Referral Payout Calculator")
st.markdown("Upload the referral module file to calculate payouts based on the 25% discount logic.")

uploaded_file = st.file_uploader("Choose a CSV or Excel file", type=['csv', 'xlsx'])

if uploaded_file is not None:
    # Load data
    if uploaded_file.name.endswith('.csv'):
        df = pd.read_csv(uploaded_file)
    else:
        df = pd.read_excel(uploaded_file)

    # Referral Calculation Logic
    def calculate_referral(row):
        try:
            gross = float(row['Gross Amount'])
            discount = float(row['Discount'])
            net = float(row['Net Amount'])
            
            if gross <= 0: return 0
            
            disc_pct = discount / gross
            if disc_pct >= 0.25:
                return 0
            else:
                # Referral = (25% - discount%) * Net Amount
                return (0.25 - disc_pct) * net
        except:
            return 0

    # Apply calculations
    df['Referral Amount'] = df.apply(calculate_referral, axis=1)

    # Create Summary
    summary = df.groupby('DoctorName')['Referral Amount'].sum().reset_index()
    summary = summary.sort_values(by='Referral Amount', ascending=False)

    # Display Results
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Payout Summary")
        st.dataframe(summary, use_container_width=True)
    
    with col2:
        st.subheader("Key Metrics")
        st.metric("Total Referral Payout", f"₹{df['Referral Amount'].sum():,.2f}")
        st.metric("Doctors to Pay", len(summary[summary['Referral Amount'] > 0]))

    # Download Buttons
    st.download_button(
        label="Download Full Processed Report",
        data=df.to_csv(index=False).encode('utf-8'),
        file_name='Referral_Calculations.csv',
        mime='text/csv',
    )
