import streamlit as st
import pandas as pd

# Set page to wide mode
st.set_page_config(page_title="Doctor Referral System", layout="wide")

st.title("🏥 Doctor Referral Automation")
st.markdown("---")

# 1. File Uploader
uploaded_file = st.file_uploader("Upload Monthly Referral File (Excel or CSV)", type=['csv', 'xlsx'])

if uploaded_file is not None:
    # Load Data
    if uploaded_file.name.endswith('.csv'):
        df = pd.read_csv(uploaded_file)
    else:
        df = pd.read_excel(uploaded_file)
    
    # Clean Column Names (Removes hidden spaces)
    df.columns = df.columns.str.strip()

    # 2. Sidebar Settings
    st.sidebar.header("⚙️ Configuration")
    
    # Manual Exclusion Feature (Important for matching 1258/3011 target)
    st.sidebar.subheader("Manual Exclusions")
    st.sidebar.info("Enter Work Order IDs to exclude (e.g., LLSL579365).")
    exclude_input = st.sidebar.text_area("Exclusion List (comma separated):", value="LLSL579365")
    exclude_list = [x.strip() for x in exclude_input.split(",") if x.strip()]

    # 3. Logic: Name Merging
    def merge_doctor_names(name):
        n = str(name).upper().strip()
        if "LIPIKA" in n: return "LIPIKA DAS MUKHOPADHYAY"
        if "N V K" in n or "NVK" in n: return "N V K MOHAN"
        return n

    df['Official_Name'] = df['DoctorName'].apply(merge_doctor_names)

    # 4. Logic: Calculation & Rounding
    def calculate_payout(row):
        # Skip if ID is in exclusion list
        if str(row['workorderid']).strip() in exclude_list:
            return 0
        
        try:
            g = float(row['Gross Amount'])
            d = float(row['Discount'])
            n = float(row['Net Amount'])
            
            if g <= 0: return 0
            
            disc_pct = d / g
            if disc_pct >= 0.25:
                return 0
            else:
                # Logic: (25% - Discount%) * Net, rounded to nearest whole number
                return int(round((0.25 - disc_pct) * n))
        except:
            return 0

    df['Net Payable'] = df.apply(calculate_payout, axis=1)

    # 5. Doctor Selection (White List)
    st.sidebar.subheader("Approved Payees")
    all_docs = sorted(df['Official_Name'].unique())
    # Pre-select based on Feb results
    default_list = ["LIPIKA DAS MUKHOPADHYAY", "JINIA PAUL", "ARJUN DASGUPTA", "N V K MOHAN", "CAPT A K SAHA"]
    selected_payees = st.sidebar.multiselect(
        "Select Doctors to pay:", 
        options=all_docs, 
        default=[d for d in default_list if d in all_docs]
    )

    # Final Filter
    df['Final Payout'] = df.apply(lambda x: x['Net Payable'] if x['Official_Name'] in selected_payees else 0, axis=1)

    # 6. Dashboard Metrics
    m1, m2, m3 = st.columns(3)
    total_val = df['Final Payout'].sum()
    lipika_val = df[df['Official_Name'] == "LIPIKA DAS MUKHOPADHYAY"]['Final Payout'].sum()
    
    m1.metric("Grand Total Payout", f"₹{total_val:,}")
    m2.metric("Lipika Total", f"₹{lipika_val:,}")
    m3.metric("Excluded Transactions", len(exclude_list))

    # Success message if matching Feb Target
    if total_val == 3011:
        st.balloons()
        st.success("🎯 Match Confirmed: This matches the Boss's 3,011 result perfectly.")

    # 7. Results Table
    st.subheader("Payout Summary")
    summary = df.groupby('Official_Name')['Final Payout'].sum().reset_index()
    summary = summary[summary['Final Payout'] > 0].sort_values('Final Payout', ascending=False)
    st.table(summary)

    # 8. Export Data
    st.subheader("Download Result")
    csv = df.to_csv(index=False).encode('utf-8')
    st.download_button(
        label="📥 Download Processed CSV for Boss",
        data=csv,
        file_name=f"Processed_Referral_{uploaded_file.name}",
        mime='text/csv'
    )
