
# app.py
import streamlit as st
import pandas as pd
import os
from PIL import Image

st.set_page_config(page_title='Clash Issues', page_icon=":1234:", layout='centered')
css_file="styles/main.css"
# Upload the CSV file
uploaded_file = st.file_uploader("Choose a CSV file", type="csv")

if uploaded_file is not None:
    data = pd.read_csv(uploaded_file)

    # Replace the local paths with the correct path to your image folder
    data['ImagePath'] = data['ImagePath'].str.replace(r'C:\\Users\\AtomRyzen\\Desktop\\PowerBI_ReportApp\\', '/path/to/your/image/folder')

    # Display the data
    for idx, row in data.iterrows():
        st.write(f"Clash ID: {row['Clash ID']}")
        st.write(f"View Name: {row['ViewName']}")
        image_path = os.path.join(row['ImagePath'])
        try:
            image = Image.open(image_path)
            st.image(image, caption=row['ViewName'], use_column_width=True)
        except Exception as e:
            st.write(f"Error: {e}")
            st.write("Could not load image: ", image_path)
        st.write("---")  # Line separator
else:
    st.write("Please upload a CSV file.")