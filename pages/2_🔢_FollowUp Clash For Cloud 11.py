import streamlit as st
import pandas as pd
from urllib.parse import unquote
from io import BytesIO

from reportlab.platypus import Table, Image, Spacer, Paragraph, PageTemplate, Frame, BaseDocTemplate
from reportlab.platypus import (SimpleDocTemplate, Table, TableStyle, Frame, 
                                PageTemplate, BaseDocTemplate, Image as ReportlabImage, 
                                Paragraph, Spacer)
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
from bs4 import BeautifulSoup
EXTRACTED_FLAG = False
# Set up the page
st.set_page_config(page_title='Follow Up Clash For Cloud 11', page_icon=":1234:", layout='centered')
css_file = "styles/main.css"
with open(css_file) as f:
    st.markdown("<style>{}</style>".format(f.read()), unsafe_allow_html=True)
st.title('Follow Up Clash Report For Cloud 11')
pdfmetrics.registerFont(TTFont('Sarabun', r'./Font/THSarabunNew.ttf'))
pdfmetrics.registerFont(TTFont('Sarabun-Bold', r'./Font/THSarabunNew Bold.ttf'))
image_dict = {}

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

def extract_file_name(url):
    if isinstance(url, str):
        # Split the string by comma to handle multiple URLs and take the first one
        first_url = url.split(',')[0]
        url_decoded = unquote(first_url)
        # Replace underscores with spaces in the file name
        file_name = url_decoded.split('/')[-1].replace('_', ' ')
        return file_name
    else:
        return url
    
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
            canvas.drawCentredString(doc.width/2 + 0.5*inch, doc.height + 1.25*inch + 0.25*inch, project_name)

            timestamp = time.strftime("%Y/%m/%d")
            canvas.setFont("Sarabun-Bold", 10)
            canvas.drawRightString(doc.width + inch, doc.height + inch + 0.75*inch, f"Generated on: {timestamp}")

    logo_path = r"./Media/1-Aurecon-logo-colour-RGB-Positive.png"

    #desktop_path = os.path.join(os.path.expanduser('~'), 'Desktop')
    #output_file = os.path.join(desktop_path, f"{time.strftime('%Y%m%d')}_ClashReport_{project_name}.pdf")
    #pdf = MyDocTemplate(output_file, pagesize=landscape(A3))
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
        ('BACKGROUND', (0, 0), (-1, 0), colors.limegreen),
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
    column_order = ["ID", "Location", "Name", "Photo", "Check TOC model", "Solution", "Note - Solution", "Status", "Team", "Remark"]
    header_data_reordered = [header_data[df.columns.get_loc(col)] for col in column_order]
    content = []

  
    for _, row in df.iterrows():
        img_name_designer = row['Photo']
        img_name_combine_shop = row['Check TOC model']
        img_name_solution = row['Solution']

        img_designer = None
        img_combine_shop = None
        img_solution = None

        if img_name_designer != "Image not found" and img_name_designer in image_dict:
            img_data_designer = BytesIO(image_dict[img_name_designer])
            img_designer = ReportlabImage(img_data_designer, width=2*inch, height=2*inch)

        if img_name_combine_shop != "Image not found" and img_name_combine_shop in image_dict:
            img_data_combine_shop = BytesIO(image_dict[img_name_combine_shop])
            img_combine_shop = ReportlabImage(img_data_combine_shop, width=2*inch, height=2*inch)

        if img_name_solution != "Image not found" and img_name_solution in image_dict:
            img_data_solution = BytesIO(image_dict[img_name_solution])
            img_solution = ReportlabImage(img_data_solution, width=2*inch, height=2*inch)

        row_data = [
            Paragraph(str(row["ID"]), cell_style),
            Paragraph(str(row["Location"]), cell_style),
            Paragraph(str(row["Name"]), cell_style),
            img_designer,
            img_combine_shop,
            img_solution,
            Paragraph(str(row["Note - Solution"]), cell_style),
            Paragraph(str(row["Status"]), cell_style),
            Paragraph(str(row["Team"]), cell_style),
            Paragraph(str(row["Remark"]), cell_style),
        ]
        content.append(row_data)


    data = [header_data_reordered] + content
    col_widths = [50, 100, 150, 150, 150, 150, 150, 80, 80, 80]
    #1 point = 1/72 of an inch
    table = Table(data, colWidths=col_widths, repeatRows=1, style=table_style)
    #elems = [Spacer(1, 0.5*inch), table]
    elems = [table]
    pdf.build(elems)
    output.seek(0)
    return output
    


project_name = st.text_input("Enter Project Name:", value='Cloud 11')
csv_file = st.file_uploader("Choose a CSV file", type="csv")
uploaded_zip = st.file_uploader("Upload Image ZIP", type=['zip'])
if uploaded_zip:
    zip_images = extract_images_from_zip(uploaded_zip)
    for img_name, img_data in zip_images:
        image_dict[img_name] = img_data



if csv_file and uploaded_zip:
    data = pd.read_csv(csv_file)
    data.fillna("", inplace=True)
    data['Photo'] = data['Photo'].apply(extract_file_name)
    data['Check TOC model'] = data['Check TOC model'].apply(extract_file_name)
    data['Solution'] = data['Solution'].apply(extract_file_name)

    unique_locations = data['Location'].unique().tolist()
    selected_locations = st.multiselect("Select Location(s):", unique_locations, default=unique_locations)
    
    unique_statuses = data['Status'].unique().tolist()
    selected_statuses = st.multiselect("Select Status(es):", unique_statuses, default=unique_statuses)
    
    unique_teams = data['Team'].unique().tolist()
    selected_teams = st.multiselect("Select Team(s):", unique_teams, default=unique_teams)
    
    # Filter the DataFrame based on selected values
    if selected_locations:
        data = data[data['Location'].isin(selected_locations)]
    if selected_statuses:
        data = data[data['Status'].isin(selected_statuses)]
    if selected_teams:
        data = data[data['Team'].isin(selected_teams)]
    
    st.write(data.head(10))


    if st.button("Generate CSV"):
        csv_data = data.to_csv(encoding='utf-8-sig', index=False).encode('utf-8-sig')
        st.download_button(
            label="Download CSV",
            data=BytesIO(csv_data),
            file_name=f"{time.strftime('%Y%m%d')}_Design-Coordination_Tracking-Report_{project_name}.csv",
            mime="text/csv"
        )

    if st.button("Generate Report"):
        df_data = generate_pdf(data, project_name)
        st.download_button(
            label="Download PDF Report",
            data=df_data,
            file_name=f"{time.strftime('%Y%m%d')}_Design-Coordination_Tracking-Report_{project_name}.pdf",
                mime="application/pdf"
            )

