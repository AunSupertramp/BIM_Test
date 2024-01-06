import streamlit as st
import pyautogui
import threading
import time
import pandas as pd
import io





st.set_page_config(page_title='Naviswork Clash Issues Report & Note (UOB)', page_icon=":atm:", layout='centered')

css_file = "styles/main.css"
with open(css_file) as f:
    st.markdown("<style>{}</style>".format(f.read()), unsafe_allow_html=True)




def enter_emails(emails):
    for email in emails:
        if not running:
            break
        pyautogui.write(email)
        pyautogui.press('enter')
        time.sleep(1.5)

def start_process(emails):
    global running
    running = True
    threading.Thread(target=enter_emails, args=(emails,)).start()

def stop_process():
    global running
    running = False

def read_emails(file, file_type):
    """ Read emails from a specific column in a CSV or Excel file. """
    try:
        if file_type == 'csv':
            df = pd.read_csv(file)
        elif file_type == 'excel':
            df = pd.read_excel(file)
        return df  # Return the dataframe
    except Exception as e:
        st.error(f"An error occurred while reading the file: {e}")
        return None

st.title('Email Automation App')

# File uploader
uploaded_file = st.file_uploader("Upload a CSV or Excel file with email addresses", type=['csv', 'xlsx'])

if uploaded_file is not None:
    file_type = 'csv' if uploaded_file.name.endswith('.csv') else 'excel'
    df = read_emails(uploaded_file, file_type)
    if df is not None:
        st.dataframe(df)  # Display the dataframe in the app
        emails = df['Email'].tolist()  # Extracting emails from the 'Email' column
        if emails and st.button('Start Process'):
            start_process(emails)
            st.success('Process started. Switch to the target application window.')

if st.button('Stop Process'):
    stop_process()
    st.warning('Process stopped.')
