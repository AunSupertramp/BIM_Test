import streamlit as st
import pandas as pd
import xlrd
from reportlab.platypus import Table, Image, Spacer, Paragraph, PageTemplate, Frame, BaseDocTemplate
from reportlab.lib import colors
from reportlab.lib.pagesizes import landscape, A3
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.units import inch
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import inch
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import (Table, TableStyle, Frame, 
                                PageTemplate, BaseDocTemplate, Image as ReportlabImage, 
                                Paragraph, Spacer)
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from PIL import Image as pil_image
import xml.etree.ElementTree as ET
import time
from io import BytesIO
import os
import shutil
import tempfile
from bs4 import BeautifulSoup
import datetime

EXTRACTED_FLAG = False


st.set_page_config(page_title='Naviswork Clash Issues Report (Cloud11)', page_icon=":partly_sunny_rain:", layout='centered')

css_file = "styles/main.css"
with open(css_file) as f:
    st.markdown("<style>{}</style>".format(f.read()), unsafe_allow_html=True)

pdfmetrics.registerFont(TTFont('Sarabun', r'./Font/THSarabunNew.ttf'))
pdfmetrics.registerFont(TTFont('Sarabun-Bold', r'./Font/THSarabunNew Bold.ttf'))



def adjust_convert_date_format(date_str):
    # Check if the date is already in 'YYYY-MM-DD' format
    if len(date_str) == 10 and date_str[4] == '-' and date_str[7] == '-':
        # Convert 'YYYY-MM-DD' to 'YYYYMMDD'
        date_str = date_str.replace("-", "")

    # Adjusted function to handle the date format 'YYMMDD'
    try:
        # If the string is in 'YYMMDD' format, convert it to 'YYYYMMDD'
        if len(date_str) == 6:
            date_str = "20" + date_str

        # Now convert 'YYYYMMDD' to a datetime object
        date_obj = datetime.datetime.strptime(date_str, "%Y%m%d")

        # Format to 'DD/MM/YYYY'
        return date_obj.strftime("%d/%m/%Y")
    except:
        return None







def process_html_to_dfs(html_content):
    soup = BeautifulSoup(html_content, 'html.parser')
    h2_tags = soup.find_all('h2')
    data = []

    for h2 in h2_tags:
        view_name = h2.text.strip()
        img = h2.find_next('img')
        img_src = img['src'].split('/')[-1] if img else None  # Extract just the filename from the src
        #clash_id = view_name.split('_')[0]  # Extract the ID by splitting the view name on underscore
        data.append((view_name, img_src))

    full_df = pd.DataFrame(data, columns=[ 'View Name', 'Image'])
    
    # Filter the rows based on the view name patterns
    # Using regex=True to escape special characters properly
    df1 = full_df[full_df['View Name'].str.count('_') <= 3]
    view_name_components1 = df1['View Name'].str.split('_', expand=True)

  
    # Directly extract and assign 'ID' from 'View Name'
    #df1['ID'] = view_name_components1[0]
    #df1['Merge ID'] = df1['ID']

    return df1





# Function to process HTML content
def process_html_content(html_content):
    df1 = process_html_to_dfs(html_content)

    soup = BeautifulSoup(html_content, 'html.parser')
    h2_tags = soup.find_all('h2')
    data = []

    for h2 in h2_tags:
        img = h2.find_next('img')
        img_src = img['src'].split('/')[-1] if img else None
        data.append((h2.text.strip(), img_src))

    df = pd.DataFrame(data, columns=['View Name', 'Image'])
    df = df[df['View Name'].str.count('_') >= 3]
    filtered_no_asterisk_df = df[~df['View Name'].str.contains('\*')]
    df=filtered_no_asterisk_df



    return df




    

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

#DATE_FORMATS = ["%Y-%m-%d", "%m/%d/%Y", "%d/%m/%Y"]
DATE_FORMATS = ["%d/%m/%Y"]
def try_parsing_date(text):
    for fmt in DATE_FORMATS:
        try:
            return pd.to_datetime(text, format=fmt).strftime("%d/%m/%Y")
        except ValueError:
            pass
    # If all formats fail, return the original string
    return text




pdfmetrics.registerFont(TTFont('Sarabun', r'./Font/THSarabunNew.ttf'))
pdfmetrics.registerFont(TTFont('Sarabun-Bold', r'./Font/THSarabunNew Bold.ttf'))

def formatted_paragraph(text, styles):
    bold_style = ParagraphStyle("BoldStyle", parent=styles["Normal"], fontName="Sarabun-Bold")
    light_style = ParagraphStyle("LightStyle", parent=styles["Normal"], fontName="Sarabun")

    # Split the text into bold and light parts using the custom tags
    parts = text.split("<l>")
    bold_text = parts[0].replace("<b>", "").replace("</b>", "").strip()
    light_text = parts[1].replace("</l>", "").strip()

    # Create Paragraph objects for each part
    bold_part = Paragraph(bold_text, style=bold_style)
    light_part = Paragraph(light_text, style=light_style)

    return bold_part, light_part


def generate_pdf(df, project_name):
    class MyDocTemplate(BaseDocTemplate):
        def __init__(self, filename, **kwargs):
            BaseDocTemplate.__init__(self, filename, **kwargs)
            page_width, page_height = A4
            frame_width = page_width
            frame_height = 0.8 * page_height
            frame_x = (page_width - frame_width) / 2
            frame_y = (page_height - frame_height) / 2
            frame = Frame(frame_x, frame_y, frame_width, frame_height, id='F1')
            template = PageTemplate('normal', [frame], onPage=self.add_page_decorations)
            self.addPageTemplates([template])
        def add_page_decorations(self, canvas, doc):
            with pil_image.open(logo_path) as img:
                width, height = img.size
            aspect = width / height
            new_height = 0.25 * inch
            new_width = new_height * aspect
            canvas.drawImage(logo_path, 0.2*inch, doc.height + 1.5*inch, width=new_width, height=new_height)
            canvas.setFont("Sarabun-Bold", 26)
            # Adjusting the Y position (doc.height + ...) to a smaller value will lower the project name
            canvas.drawCentredString(page_width/2, doc.height + 1.0*inch, project_name)
            timestamp = time.strftime("%Y/%m/%d")
            canvas.setFont("Sarabun-Bold", 10)
            canvas.drawRightString(page_width - 0.2*inch, page_height - 0.2*inch, f"Generated on: {timestamp}")

    logo_path = r"./Media/1-Aurecon-logo-colour-RGB-Positive.png"
    output = BytesIO()
    pdf = MyDocTemplate(output, pagesize=A4)
    story = []
    header_data = ["No.", "Image", "Details"]
    styles = getSampleStyleSheet()
 
    data = [header_data]
    for idx, (index, row) in enumerate(df.iterrows(), 1):
        img_data = row['Image']
        if img_data != "Image not found":
            if isinstance(img_data, BytesIO):  # If it's already a BytesIO object
                image_stream = img_data
            else:
                image_stream = BytesIO(img_data.getvalue())
            img_data.seek(0)  # Reset the file pointer to the start
            image_path = ReportlabImage(image_stream, width=2.4*inch, height=2.4*inch)
        else:
            image_path = "Image Not Found"

        details_list = []
        texts = [
            f"<b>ID:</b> <l>{row['ID']}</l>",
            #f"<b>View Name:</b> <l>{row['View Name']}</l>",
            f"<b>Title:</b> <l>{row['Title']}</l>",
            f"<b>Zone:</b> <l>{row['Zone']}</l>",
            f"<b>Floor Level:</b> <l>{row['Floor Level']}</l>",
            f"<b>Priority:</b> <l>{row['Priority']}</l>",
            f"<b>Status:</b> <l>{row['Status']}</l>",
            f"<b>Discipline:</b> <l>{row['Discipline']}</l>",
            f"<b>Assigned to:</b> <l>{row['Assigned to']}</l>",
            #f"<b>Group:</b> <l>{row['Group']}</l>",

            #f"<b>Due Date:</b> <l>{row['Due Date']}</l>"
        ]
        for text in texts:
            bold_part, light_part = formatted_paragraph(text, styles)
            details_list.append(bold_part)
            details_list.append(light_part)
        details_list.append(Spacer(1, 0.1*inch))


        data.append([str(idx), image_path, details_list])


    page_width, page_height = A4 
    col_widths = [(0.05 * page_width), (0.3 * page_width), (0.3* page_width)]
    table_style = TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), '#4F709C'),
        ('TEXTCOLOR', (0, 0), (-1, 0), '#e2dbdc'),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('FONTNAME', (0, 0), (-1, 0), 'Sarabun-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 18),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), '#ffffff'),
        ('GRID', (0, 0), (-1, -1), 1, '#2B2B2B'),
        ('FONTNAME', (0, 1), (-1, -1), 'Sarabun'),
        ('FONTSIZE', (1, 1), (1, -1), 16),
        ('ALIGN', (0, 0), (0, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (0, 0), 'Sarabun-Bold'),
        ('FONTSIZE', (0, 0), (0, -1), 16)
    ])
    table = Table(data, colWidths=col_widths, repeatRows=1, style=table_style)
    story.append(table)
    pdf.build(story)
    return output.getvalue()












st.title('Naviswork Cloud 11')
project_name = st.text_input("Enter Project Name:", value="Cloud 11")
merged_df = pd.DataFrame()
df_view = pd.DataFrame() 
html_file = st.file_uploader("Upload HTML File", type=['html'])
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



if html_file:
    html_content = html_file.read().decode('utf-8-sig')
    html_df = process_html_content(html_content)
    
    # Filter rows where 'View Name' starts with 'A' or 'B'
    html_df = html_df[html_df['View Name'].str.startswith(('A', 'B'))]
    
    # Remove rows where 'View Name' contains special characters
    html_df = html_df[~html_df['View Name'].str.contains(r'[/*\-+=]', regex=True)]
    
    # Remove rows where 'View Name' starts with an underscore
    html_df = html_df[~html_df['View Name'].str.startswith('_')]
    
    # Extract 'ID' from 'View Name'
    html_df['ID'] = html_df['View Name'].str.extract(r'(^[^_]+)')
    
    # Define the desired column order, including 'ID'
    column_order = ["ID","View Name","Image"]
    merged_df = html_df[column_order]

    # Display the table with the first 3 rows
    st.table(merged_df.head(3))




    

else:
    st.write("Please upload both HTML")
       


# Replace the "Image" column with the filenames for display in Streamlit table
merged_df_display = merged_df.copy()
# Replace the "Image" column with the actual image objects for processing
if "Image" in merged_df.columns:
    merged_df["Image"] = merged_df["Image"].apply(lambda x: image_dict.get(x, "Image not found"))


# File uploader that accepts Excel files
report_file = st.file_uploader("Upload the Clash Tracking Report file", type=['xls', 'xlsx'])

# List of sheet names to choose from
sheet_names = ['POD', 'YRB', 'WG', 'TRB', 'OFF-N', 'OFF-S']

# Dropdown menu to select sheet name
selected_sheet = st.selectbox("Select Sheet Name", sheet_names)

if not merged_df.empty and uploaded_files and report_file:
    if report_file.name.endswith('.xlsx'):
        # Load the Excel file
        df_report = pd.read_excel(report_file, engine='openpyxl', sheet_name=selected_sheet, skiprows=2, header=0, index_col=0)
    elif report_file.name.endswith('.xls'):
        # Load the Excel file
        df_report = pd.read_excel(report_file, engine='xlrd', sheet_name=selected_sheet, skiprows=2, header=0, index_col=0)
    else:
        st.error("Unsupported file type. Please upload an Excel file with .xls or .xlsx extension.")
    
    # Display the DataFrame
    # Merging merged_df into df_report
    df_Cloud = pd.merge(df_report, merged_df_display, how='inner', left_on='ID', right_on='ID')

# Filter the data based on user selection
    filter_columns = ['ID', 'Status', 'Priority', 'Discipline', 'Zone', 'Assigned to', 'Floor Level']
    
    filter_values = {}
    for column in filter_columns:
        unique_values = df_Cloud[column].unique().tolist()
        # Add an option for filtering all values
        unique_values.insert(0, "All")
        selected_values = st.multiselect(f"Select Value(s) to Filter in {column}", unique_values)
        if selected_values and "All" not in selected_values:
            filter_values[column] = selected_values

    if filter_values:
        # Initialize a mask of True values
        mask = pd.Series([True] * len(df_Cloud), index=df_Cloud.index)
        # Apply filters
        for column, values in filter_values.items():
            mask &= df_Cloud[column].isin(values)
        df_Cloud = df_Cloud[mask]



    st.table(df_Cloud)


    if "Image" in df_Cloud.columns:
        df_Cloud["Image"] = df_Cloud["Image"].apply(lambda x: image_dict.get(x, "Image not found"))



    if st.button("Export CSV"):
    # Drop 'Image' and 'Image_Plan' columns from the DataFrame copy
        df_export = df_Cloud
        
        # Convert the modified DataFrame to CSV format
        df_export= df_Cloud.to_csv(encoding='utf-8-sig', index=False).encode('utf-8-sig')
        
        # Create a download button for the CSV data
        st.download_button(
            label="Download CSV",
            data=BytesIO(df_export),
            file_name=f"{datetime.datetime.now().strftime('%Y%m%d')}_CSV-Note_{project_name}.csv",
            mime="text/csv"
        )



    if st.button("Generate ReportA4"):
        pdf_data = generate_pdf(df_Cloud, project_name)
        st.download_button(
            label="Download PDF Report",
            data=pdf_data,
            file_name=f"{datetime.datetime.now().strftime('%Y%m%d')}_PDF-ClashNoteReport_{project_name}.pdf",
            mime="application/pdf"
        )