import streamlit as st
import pandas as pd
import time

st.set_page_config(page_title='CSV Merge For PP25 & PP26', page_icon=":green_book:", layout='centered')
st.title("CSV Merge For PP25 & PP26")
css_file = "styles/main.css"
with open(css_file) as f:
    st.markdown("<style>{}</style>".format(f.read()), unsafe_allow_html=True)
# Step 1: File Uploaders
project_name = st.text_input("Enter Project Name:", value='')
main_file = st.file_uploader("Upload the main CSV file", type=['csv'])
report_file = st.file_uploader("Upload the Clash Tracking Report CSV file", type=['csv'])



if main_file and report_file:
    # Load the CSV files into pandas dataframes
    df_main = pd.read_csv(main_file)
    df_report = pd.read_csv(report_file)
    
    # Step 2: Button to Execute
    if st.button('Merge Files'):
        # Merge the dataframes on the clash ID column (replace 'Clash ID' with the actual column name)
        result_df = df_main.merge(df_report[['Clash ID', 'Notes', 'Usage', 'Due Date']], on='Clash ID', how='left')
        
        # Save the result dataframe in the session state
        st.session_state['result_df'] = result_df
        
        # Display the merged dataframe (you can also use st.write or st.table)
        st.dataframe(result_df)
        
if 'result_df' in st.session_state:
    # Generate CSV button with data from session state
    if st.button("Generate CSV"):
        csv_data = st.session_state['result_df'].to_csv(index=False, encoding='utf-8-sig')
        st.download_button(
            label="Download CSV",
            data=csv_data.encode(),
            file_name=f"{time.strftime('%Y%m%d')}_CSV-MergedWithNote_{project_name}.csv",
            mime="text/csv"
        )
