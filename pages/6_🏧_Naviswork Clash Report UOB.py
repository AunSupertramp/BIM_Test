import streamlit as st
from bs4 import BeautifulSoup
import pandas as pd
import xml.etree.ElementTree as ET
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
import zipfile
import time
from io import BytesIO
import os
import shutil
import tempfile


st.set_page_config(page_title='Naviswork Clash Report For UOB', page_icon=":atm:", layout='centered')
css_file = "styles/main.css"
with open(css_file) as f:
    st.markdown("<style>{}</style>".format(f.read()), unsafe_allow_html=True)

# Function to adjust and convert date format
def adjust_convert_date_format(date_str):
    if len(date_str) == 10 and date_str[4] == '-' and date_str[7] == '-':
        return date_str
    try:
        formatted_date = date_str[:4] + "-" + date_str[4:6] + "-" + date_str[6:]
        return formatted_date
    except:
        return None

# Function to process HTML content
def process_html_content(html_content):
    soup = BeautifulSoup(html_content, 'html.parser')
    h2_tags = soup.find_all('h2')
    data = []

    for h2 in h2_tags:
        img = h2.find_next('img')
        img_src = img['src'].split('/')[-1] if img else None
        data.append((h2.text.strip(), img_src))

    df = pd.DataFrame(data, columns=['View Name', 'Image'])
    df = df[df['View Name'].str.count('_') >= 2]
    view_name_components = df['View Name'].str.split('_', expand=True)
    df['Clash ID'] = view_name_components[0]
    df['Level'] = view_name_components[1]
    df['Date Found'] = view_name_components[2]
    df['Discipline'] = view_name_components[3]
    df['Description'] = view_name_components[4]
    df['Unique ID'] = df['Clash ID'] + '_' + df['Level']
    df['Date Found'] = df['Date Found'].apply(adjust_convert_date_format)
    df['Issues Status'] = ""

    return df

# Function to extract view details with levels from XML content
def extract_view_details_with_levels(root):
    stack = [(root, [], None)]
    results = []

    while stack:
        element, folder_names, parent_name = stack.pop()
        current_folder_name = element.attrib.get('name', parent_name)
        
        if element.tag == 'view':
            view_name = element.attrib.get('name', None)
            issues_type = folder_names[-4] if len(folder_names) >= 4 else None
            issues_status = folder_names[-3] if len(folder_names) >= 3 else None
            assign_to = folder_names[-2] if len(folder_names) >= 2 else None
            sub_zone = folder_names[-1] if folder_names else None
            results.append((view_name, sub_zone, assign_to, issues_status, issues_type))
        else:
            stack.extend([(child, folder_names + [current_folder_name], current_folder_name) for child in element])
    
    return results
def generate_pdf(df, project_name):
    class MyDocTemplate(BaseDocTemplate):
        def __init__(self, filename, **kwargs):
            BaseDocTemplate.__init__(self, filename, **kwargs)
            page_width, page_height = landscape(A3)
            frame_width = page_width - 2*0.7*inch
            frame_height = page_height - 2*0.7*inch
            frame = Frame(0.7*inch, 0.7*inch, frame_width, frame_height, id='F1')
            template = PageTemplate('normal', [frame], onPage=self.add_page_decorations)
            self.addPageTemplates([template])

        def add_page_decorations(self, canvas, doc):
            with pil_image.open(logo_path) as img:
                width, height = img.size
            aspect = width / height
            new_height = 0.25 * inch
            new_width = new_height * aspect

            canvas.drawImage(logo_path, 0.2*inch, doc.height + 1.5*inch, width=new_width, height=new_height)

            canvas.setFont("Sarabun-Bold", 30)
            canvas.drawCentredString(doc.width/2 + 0.5*inch, doc.height + 1.2*inch + 0.25*inch, project_name)

            timestamp = time.strftime("%Y/%m/%d %H:%M:%S")
            canvas.setFont("Sarabun-Bold", 10)
            canvas.drawRightString(doc.width + inch, doc.height + inch + 0.75*inch, f"Generated on: {timestamp}")

    logo_path = r"./Media/1-Aurecon-logo-colour-RGB-Positive.png"

    output = BytesIO()
    pdf = MyDocTemplate(output, pagesize=landscape(A3))

    styles = getSampleStyleSheet()
    cell_style = styles["Normal"]
    cell_style.fontName = "Sarabun"
    cell_style.alignment = TA_LEFT

    content = []

    header_style = ParagraphStyle(
        "HeaderStyle",
        parent=styles["Normal"],
        fontName="Sarabun-Bold",
        fontSize=18,
        textColor=colors.white,
        alignment=TA_LEFT,
        spaceAfter=12,
        leftIndent=6,
        leading=16,
    )

    table_style = [
        ('BACKGROUND', (0, 0), (-1, 0), colors.blue),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.white),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('FONTNAME', (0, 0), (-1, -1), 'Sarabun'),
        ('FONTSIZE', (0, 0), (-1, 0), 16),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('STYLE', (0, 0), (-1, -1), cell_style),
    ]

    header_data = [Paragraph(cell, header_style) for cell in df.columns.tolist()]
    column_order = ["Clash ID", "Image", "View Name", "Date Found", "Main Zone", "Sub Zone", "Level",
                    "Issues Type", "Issues Status", "Description", "Discipline", "Assign To"]
    header_data_reordered = [header_data[df.columns.get_loc(col)] for col in column_order]
    content = []

    for _, row in df.iterrows():
        img_data = row['Image']
        if img_data != "Image not found":
            if isinstance(img_data, BytesIO):  # If it's already a BytesIO object
                image_stream = img_data
            else:
                image_stream = image_dict.get(img_data, BytesIO(b"Image not found"))
            image_stream.seek(0)  # Reset the file pointer
            img = Image(image_stream, width=150, height=150)
        else:
            img = 'Image not found'

        row_data = [
            Paragraph(str(row["Clash ID"]), cell_style),
            img,
            Paragraph(str(row["View Name"]), cell_style),
            Paragraph(str(row["Date Found"]), cell_style),
            Paragraph(str(row["Main Zone"]), cell_style),
            Paragraph(str(row["Sub Zone"]), cell_style),
            Paragraph(str(row["Level"]), cell_style),
            Paragraph(str(row["Issues Type"]), cell_style),
            Paragraph(str(row["Issues Status"]), cell_style),
            Paragraph(str(row["Description"]), cell_style),
            Paragraph(str(row["Discipline"]), cell_style),
            Paragraph(str(row["Assign To"]), cell_style),
            
        ]
        content.append(row_data)

    data = [header_data_reordered] + content
    col_widths = [100, 170, 80, 80, 80, 80, 80, 80, 80, 90, 80, 80]
    table = Table(data, colWidths=col_widths, repeatRows=1, style=table_style)
    elems = [Spacer(1, 0.5*inch), table]
    pdf.build(elems)
    output.seek(0)
    return output

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
# Streamlit App
st.title('HTML and XML Data Processor')

# Input for project name
project_name = st.text_input("Project Name", value="")
main_zone = st.text_input("Main Zone", value="")

# File Uploaders
html_file = st.file_uploader("Upload HTML File", type=['html'])
xml_file = st.file_uploader("Upload XML File", type=['xml'])
# Image uploader and dictionary to hold uploaded images
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

if html_file and xml_file:
    html_content = html_file.read().decode('utf-8')
    html_df = process_html_content(html_content)

    tree = ET.parse(xml_file)
    root = tree.getroot()
    view_details_with_levels = extract_view_details_with_levels(root)
    xml_df = pd.DataFrame(view_details_with_levels, columns=['View Name', 'Sub Zone', 'Assign To', 'Issues Status', 'Issues Type'])

    xml_df['Clash ID'] = xml_df['View Name'].str.split('_').str[0]
    xml_df['Level'] = xml_df['View Name'].str.split('_').str[1]
    xml_df['Unique ID'] = xml_df['Clash ID'] + '_' + xml_df['Level']

    merged_df = pd.merge(html_df, xml_df, on='Unique ID', how='inner', suffixes=('_html', '_xml'))
    merged_df = merged_df.drop(columns=['Clash ID_xml', 'Level_xml'])
    merged_df = merged_df.rename(columns={'Issues Status_xml': 'Issues Status', 'View Name_html': 'View Name','Clash ID_html':'Clash ID','Level_html':'Level'})
    merged_df = merged_df[~merged_df['View Name'].str.contains('__', na=False)]
    merged_df['Main Zone'] = main_zone
    column_order = ["Unique ID","Clash ID", "View Name", "Date Found", "Main Zone", "Sub Zone", "Level", 
                    "Issues Type", "Issues Status", "Description", "Discipline", "Assign To", "Image"]
    merged_df = merged_df[column_order]

    if not merged_df.empty and "Issues Status" in merged_df.columns:
        available_statuses = merged_df["Issues Status"].unique().tolist()
    else:
        available_statuses = []
    selected_statuses = st.multiselect("Select Issues Status for Export:", available_statuses, default=available_statuses)
    
    if "Issues Status" in merged_df.columns:
        filtered_df = merged_df[merged_df["Issues Status"].isin(selected_statuses)]
    else:
        filtered_df = merged_df

    if "Issues Status" in filtered_df.columns:
        filtered_df_display = filtered_df[filtered_df["Issues Status"].isin(selected_statuses)]
    else:
        filtered_df_display = filtered_df
    
    st.table(filtered_df_display.head(10))

    if st.button("Generate CSV"):
        csv_data = filtered_df.to_csv(index=False, encoding='utf-8-sig')
        st.download_button(
            label="Download CSV",
            data=csv_data.encode(),
            file_name=f"{project_name}_ClashReport.csv",
            mime="text/csv"
        )
    if st.button("Generate Report"):
        pdf_data = generate_pdf(filtered_df, project_name)
        st.download_button(
            label="Download PDF Report",
            data=pdf_data,
            file_name=f"{time.strftime('%Y%m%d')}_ClashReport_{project_name}.pdf",
            mime="application/pdf"
        )
else:
    st.write("Please upload both HTML and XML files to proceed.")