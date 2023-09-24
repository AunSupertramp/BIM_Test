import streamlit as st
import pandas as pd
from reportlab.platypus import Table, Image, Spacer, Paragraph, PageTemplate, Frame, BaseDocTemplate
from reportlab.lib import colors
from reportlab.lib.pagesizes import landscape, A3
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.units import inch
from PIL import Image as pil_image
import xml.etree.ElementTree as ET
import zipfile
import time
from io import BytesIO
import os
import shutil
import tempfile
from bs4 import BeautifulSoup
import datetime

EXTRACTED_FLAG = False

st.set_page_config(page_title='Clash Issues Report', page_icon=":station:", layout='centered')


if 'notes' not in st.session_state:
    st.session_state.notes = {}
if 'usage' not in st.session_state:
    st.session_state.usage = {}
if 'due_dates' not in st.session_state:  # Initialize session state for due dates
    st.session_state.due_dates = {}

css_file = "styles/main.css"
with open(css_file) as f:
    st.markdown("<style>{}</style>".format(f.read()), unsafe_allow_html=True)

pdfmetrics.registerFont(TTFont('Sarabun', r'./Font/THSarabunNew.ttf'))
pdfmetrics.registerFont(TTFont('Sarabun-Bold', r'./Font/THSarabunNew Bold.ttf'))

def validate_date(date_str):
    """Check if the provided date string is in the format 'YYYY-MM-DD'."""
    try:
        datetime.datetime.strptime(date_str, '%Y-%m-%d')
        return True
    except ValueError:
        return False


def adjust_convert_date_format(date_str):
    # Check if the date is already in 'YYYY-MM-DD' format
    if len(date_str) == 10 and date_str[4] == '-' and date_str[7] == '-':
        return date_str
    # Adjusted function to handle the date format 'YYMMDD'
    try:
        formatted_date = "20" + date_str[:2] + "-" + date_str[2:4] + "-" + date_str[4:6]
        return formatted_date  # We already have it in 'YYYY-MM-DD' format, so no need for extra conversion
    except:
        return "INVALID"

def process_html_content(html_content):
    soup = BeautifulSoup(html_content, 'html.parser')
    h2_tags = soup.find_all('h2')
    data = []

    for h2 in h2_tags:
        img = h2.find_next('img')
        img_src = img['src'].split('/')[-1] if img else None  # Extract just the filename from the src
        data.append((h2.text.strip(), img_src))

    df = pd.DataFrame(data, columns=['View Name', 'Image'])

    df = df[~df['View Name'].str.contains('/')]
    df = df[~df['View Name'].str.startswith("____")]


    multiple_underscores_df = df[df['View Name'].str.count('_') > 2]
    filtered_no_asterisk_df = multiple_underscores_df[~multiple_underscores_df['View Name'].str.contains('\*')]
    
    split_columns = filtered_no_asterisk_df['View Name'].str.split('_', expand=True)
    renamed_columns = {
        0: "Clash ID",
        1: "Date Found",
        2: "Main Zone",
        3: "Level",
        4: "Description",
    }
    split_columns = split_columns.rename(columns=renamed_columns)
    expanded_df = pd.concat([filtered_no_asterisk_df, split_columns], axis=1)

    expanded_df['Date Found'] = expanded_df['Date Found'].apply(adjust_convert_date_format)
    expanded_df = expanded_df[(expanded_df['Date Found'] != "INVALID") & (expanded_df['Date Found'].apply(validate_date))]

    if 'Date Found' in expanded_df.columns:
        expanded_df['Formatted Date'] = expanded_df['Date Found'].apply(adjust_convert_date_format)
    else:
        expanded_df['Formatted Date'] = None

    

    filtered_date_df = expanded_df.dropna(subset=['Formatted Date'])
    filtered_date_df['Issues Status'] = ""

    desired_order = ["Clash ID", "View Name", "Date Found", "Main Zone", "Level", 
                    "Description","Image"]
    
    # Only reorder columns that are present in the DataFrame
    available_columns = [col for col in desired_order if col in filtered_date_df.columns]
    reordered_df = filtered_date_df[available_columns]

    return reordered_df
    

def extract_images_from_zip(uploaded_zip_file):
    extracted_images = []
    
    # Create a temporary directory to extract files into
    with tempfile.TemporaryDirectory() as tmpdirname:
        # Save the uploaded file to a temporary file
        temp_zip_path = os.path.join(tmpdirname, 'temp.zip')
        with open(temp_zip_path, 'wb') as f:
            f.write(uploaded_zip_file.getvalue())
        
        # Extract the zip file
        shutil.unpack_archive(temp_zip_path, tmpdirname)

        # Walk through the extracted files and pick up images
        for subdir, _, files in os.walk(tmpdirname):
            for file in files:
                if file.lower().endswith(('.jpg', '.jpeg', '.png')):
                    file_path = os.path.join(subdir, file)
                    with open(file_path, 'rb') as f:
                        extracted_images.append((file, f.read()))

    return extracted_images

def main():
    st.title('Clash Report Generator (P Iff)')
    project_name = st.text_input("Enter Project Name:")
    html_file = st.file_uploader("Upload HTML File", type=['html'])
    if html_file:
        html_content = html_file.read().decode()
        df = process_html_content(html_content)
    else:
        df = pd.DataFrame()

    # Check if the DataFrame is not empty before performing operations on it
    if not df.empty:
        st.sidebar.header("Filter Options")
        filter_cols = ['Clash ID', 'View Name', 'Main Zone', 'Level']
        selected_values = {}
        
        # Ensure columns exist before accessing them
        for col in filter_cols:
            if col in df.columns:
                unique_values = df[col].unique().tolist()
                selected_values[col] = st.sidebar.selectbox(f'Select {col}', ['All'] + unique_values)
        
        # Filtering the data based on the selected values
        for col, value in selected_values.items():
            if value != 'All' and col in df.columns:
                df = df[df[col] == value]    

    
    uploaded_files = st.file_uploader("Upload Images or ZIP of Images", type=['jpg', 'jpeg', 'png', 'zip', 'application/x-zip-compressed'], accept_multiple_files=True)

    image_dict = {}
    for uploaded_file in uploaded_files:
        file_type = uploaded_file.type
        if file_type in ['application/zip', 'application/x-zip-compressed']:
            extracted_images = extract_images_from_zip(uploaded_file)
            for img_name, img_data in extracted_images:
                image_dict[img_name] = BytesIO(img_data)
        elif file_type in ['image/jpeg', 'image/jpg', 'image/png']:
            image_dict[uploaded_file.name] = uploaded_file
        else:
            st.write(f"Unsupported file type: {file_type}")
    
    # Replace the "Image" column with the actual image objects for processing
    display_df = df.copy()
    if "Image" in display_df.columns:
        display_df["Image"] = display_df["Image"].apply(lambda x: "Image Data" if isinstance(x, BytesIO) else x)

    st.dataframe(df)

    ROWS_PER_PAGE = 10
    total_rows = len(display_df)
    total_pages = -(-total_rows // ROWS_PER_PAGE)
    # Only display the slider if there's more than one page
    if total_pages > 1:
        selected_page = st.slider('Select a page:', 1, total_pages)
    else:
        selected_page = 1  # This is a ceiling division

    start_idx = (selected_page - 1) * ROWS_PER_PAGE
    end_idx = start_idx + ROWS_PER_PAGE
    current_rows = display_df.iloc[start_idx:end_idx]
    for idx, row in current_rows.iterrows():
        img_name = row['Image']
        if img_name in image_dict:
            img = pil_image.open(image_dict[img_name])
            col1, col2 = st.columns([3, 3])
            with col1:
                st.write(f"<b>{row['View Name']}</b>", unsafe_allow_html=True)
                st.image(img, use_column_width=True)
            with col2:
                st.write(f"<b>Clash ID:</b> {row['Clash ID']}", unsafe_allow_html=True)
                st.write(f"<b>Date Found:</b> {row['Date Found']}", unsafe_allow_html=True)
                st.write(f"<b>Description:</b> {row['Description']}", unsafe_allow_html=True)

                #if df.at[idx, 'Issues Status'] == 'Resolved':
                    #df.at[idx, 'Usage'] = 'Resolved'

            st.markdown("---")
        else:
            st.write("Image not found")

    if st.button("Generate CSV"):
        csv_data = df.to_csv(encoding='utf-8-sig', index=False).encode('utf-8-sig')
        st.download_button(
            label="Download CSV",
            data=BytesIO(csv_data),
            file_name=f"{time.strftime('%Y%m%d')}_CSV-TRB_{project_name}.csv",
            mime="text/csv"
        )
       

if __name__ == "__main__":
    main()