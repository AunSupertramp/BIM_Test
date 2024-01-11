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

st.set_page_config(page_title='Naviswork Clash Issues Report & Note (Shark Fin)', page_icon=":shark:", layout='centered')

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
        clash_id = view_name.split('_')[0]  # Extract the Clash ID by splitting the view name on underscore
        data.append((clash_id, view_name, img_src))

    full_df = pd.DataFrame(data, columns=['Clash ID', 'View Name', 'Image'])
    
    # Filter the rows based on the view name patterns

    df1 = full_df[full_df['View Name'].str.contains("_View \(Plan\)")]
    df2 = full_df[full_df['View Name'].str.contains("_View \(Section\)")]

    df1 = df1[df1['View Name'].str.count('_') > 1]

    view_name_components1 = df1['View Name'].str.split('_', expand=True)
    #view_name_components2 = df2['View Name'].str.split('_', expand=True)
    df1['Clash ID'] = view_name_components1[0]
    df1['Level'] = view_name_components1[1]
    #df2['Clash ID'] = view_name_components2[0]
    #df2['Level'] = view_name_components2[1]
    df1['Merge ID'] = df1['Clash ID'] + '_' + df1['Level']
    #df2['Merge ID'] = df2['Clash ID'] + '_' + df2['Level']


    # Extract grid value for df2

    return df1





# Function to process HTML content
def process_html_content(html_content):
    #df1 = process_html_to_dfs(html_content)

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
    view_name_components = df['View Name'].str.split('_', expand=True)
    df['Clash ID'] = view_name_components[0]
    df['Date Found'] = view_name_components[1]
    df['Main Zone'] = view_name_components[2]
    df['Location'] = view_name_components[3]
    df['Level'] = view_name_components[4]
    df['Discipline'] = view_name_components[5]
    df['Description'] = view_name_components[6]
    df['Assign To'] = view_name_components[7]
    df['Date Found'] = df['Date Found'].apply(adjust_convert_date_format)
    df['Issues Status'] = ""
    


    # Merge reordered_df with df1 and df2 based on "Clash ID"
    #merged_df = pd.merge(df, df1, on="Merge ID", how="outer", suffixes=("", "_df1"))
    #merged_df = pd.merge(merged_with_df1, df2, on="Merge ID", how="outer", suffixes=("", "_df2"))
    # Rename the columns as per your request
    #column_rename_mapping = {"View Name_df1": "View Name_Plan","Image_df1": "Image_Plan"}
    #merged_df = merged_df.rename(columns=column_rename_mapping)
    #return merged_df
    return df
    

# Function to extract view details with levels from XML content
def extract_view_details_with_levels(root):
    stack = [(root, [], None)]
    results = []

    while stack:
        element, folder_names, parent_name = stack.pop()
        
        if element.tag == 'view':
            view_name = element.attrib.get('name', None)
            issues_type = folder_names[-3] if len(folder_names) >= 3 else None
            issues_status = folder_names[-2] if len(folder_names) >= 2 else None
            sub_zone = folder_names[-1] if folder_names else None
            results.append((view_name, sub_zone, issues_status, issues_type))
        else:
            current_folder_name = element.attrib.get('name', parent_name)
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
    elems = [table]
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

DATE_FORMATS = ["%Y-%m-%d", "%m/%d/%Y", "%d/%m/%Y"]
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


def generate_pdf2(df, project_name):
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
    header_data = ["No.", "Image", "Details", "Note"]
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
            f"<b>Clash ID:</b> <l>{row['Clash ID']}</l>",
            f"<b>Date Found:</b> <l>{row['Date Found']}</l>",
            f"<b>Main Zone:</b> <l>{row['Main Zone']}</l>",
            f"<b>Sub Zone:</b> <l>{row['Sub Zone']}</l>",
            f"<b>Level:</b> <l>{row['Level']}</l>",
            f"<b>Description:</b> <l>{row['Description']}</l>",
            f"<b>Discipline:</b> <l>{row['Discipline']}</l>",
            f"<b>Issue Type:</b> <l>{row['Issues Type']}</l>",
            f"<b>Issue Status:</b> <l>{row['Issues Status']}</l>",
            f"<b>Due Date:</b> <l>{row['Due Date']}</l>"
        ]
        for text in texts:
            bold_part, light_part = formatted_paragraph(text, styles)
            details_list.append(bold_part)
            details_list.append(light_part)
        details_list.append(Spacer(1, 0.1*inch))

       # new code for note column
        if row['Notes']:
            note_lines = row['Notes'].splitlines()
            light_style = ParagraphStyle("LightStyle", parent=styles["Normal"], fontName="Sarabun")
            note_paragraphs = [Paragraph(f"{note_lines[0]}", style=light_style)]
            for line in note_lines[1:]:
                note_paragraphs.append(Paragraph(f"{line}", style=light_style))
        else:
            note_paragraphs = [Spacer(1, 0.1*inch)]  # Use a Spacer instead of plain string

        data.append([str(idx), image_path, details_list, note_paragraphs])


    page_width, page_height = A4 
    col_widths = [(0.05 * page_width), (0.3 * page_width), (0.3* page_width), (0.3* page_width)]
    table_style = TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), '#8EA5AE'),
        ('TEXTCOLOR', (0, 0), (-1, 0), '#333333'),
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

def generate_pdf3(df, project_name):
    class MyDocTemplate(BaseDocTemplate):
        def __init__(self, filename, **kwargs):
            BaseDocTemplate.__init__(self, filename, **kwargs)
            page_width, page_height = landscape(A3)
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
            canvas.setFont("Sarabun-Bold", 30)
            canvas.drawCentredString(doc.width/2 + 0.5*inch, doc.height + 1.0*inch + 0.25*inch, project_name)
            timestamp = time.strftime("%Y/%m/%d")
            canvas.setFont("Sarabun-Bold", 10)
            canvas.drawRightString(page_width - 0.2*inch, page_height - 0.2*inch, f"Generated on: {timestamp}")

    logo_path = r"./Media/1-Aurecon-logo-colour-RGB-Positive.png"
    output = BytesIO()
    pdf = MyDocTemplate(output, pagesize=landscape(A3))
    story = []
    header_data = ["No.", "Image", "Plan","Details", "Note"]
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

        #if isinstance(row['Image_Plan'], BytesIO):
            #plan_image_stream = row['Image_Plan']
            #plan_image_path = ReportlabImage(plan_image_stream, width=2.4*inch, height=2.4*inch)
        #else:
            #plan_image_path = "Plan Image Not Found"

        # Handling the Section image
        #if isinstance(row['Image_Section'], BytesIO):
            #section_image_stream = row['Image_Section']
            #section_image_path = ReportlabImage(section_image_stream, width=2.4*inch, height=2.4*inch)
        #else:
            #section_image_path = "Section Image Not Found"


        details_list = []
        texts = [
            f"<b>Clash ID:</b> <l>{row['Clash ID']}</l>",
            f"<b>Date Found:</b> <l>{row['Date Found']}</l>",
            f"<b>Main Zone:</b> <l>{row['Main Zone']}</l>",
            f"<b>Sub Zone:</b> <l>{row['Sub Zone']}</l>",
            f"<b>Level:</b> <l>{row['Level']}</l>",
            f"<b>Description:</b> <l>{row['Description']}</l>",
            f"<b>Discipline:</b> <l>{row['Discipline']}</l>",
            f"<b>Issue Type:</b> <l>{row['Issues Type']}</l>",
            f"<b>Issue Status:</b> <l>{row['Issues Status']}</l>",
            f"<b>Due Date:</b> <l>{row['Due Date']}</l>"
        ]
        for text in texts:
            bold_part, light_part = formatted_paragraph(text, styles)
            details_list.append(bold_part)
            details_list.append(light_part)
        details_list.append(Spacer(1, 0.1*inch))

       # new code for note column
        if row['Notes']:
            note_lines = row['Notes'].splitlines()
            light_style = ParagraphStyle("LightStyle", parent=styles["Normal"], fontName="Sarabun")
            note_paragraphs = [Paragraph(f"{note_lines[0]}", style=light_style)]
            for line in note_lines[1:]:
                note_paragraphs.append(Paragraph(f"{line}", style=light_style))
        else:
            note_paragraphs = [Spacer(1, 0.1*inch)]  # Use a Spacer instead of plain string

        #data.append([str(idx), image_path, plan_image_path, details_list, note_paragraphs])
        data.append([str(idx), image_path, image_path, details_list, note_paragraphs])


    page_width, page_height = A3 
    col_widths = [(0.05 * page_width), (0.255 * page_width), (0.255* page_width),  (0.2* page_width), (0.35* page_width)]
    table_style = TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), '#8EA5AE'),
        ('TEXTCOLOR', (0, 0), (-1, 0), '#333333'),
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




st.title('Naviswork Clash Issues Report & Note ((NC) Shark Fin BIMM)')
project_name = st.text_input("Enter Project Name:", value="(NC) Shark Fin BIMM")
selected_option = st.radio("Select a process:", ["Option 1: Display without merging", "Option 2: Display with merging"])
merged_df = pd.DataFrame()
df_view = pd.DataFrame() 
html_file = st.file_uploader("Upload HTML File", type=['html'])
xml_file = st.file_uploader("Upload XML File", type=['xml'])
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
    html_content = html_file.read().decode('utf-8-sig')
    html_df = process_html_content(html_content)

    tree = ET.parse(xml_file)
    root = tree.getroot()
    view_details_with_levels = extract_view_details_with_levels(root)
    xml_df = pd.DataFrame(view_details_with_levels, columns=['View Name', 'Sub Zone', 'Issues Status', 'Issues Type'])

    xml_df['Clash ID'] = xml_df['View Name'].str.split('_').str[0]

    merged_df = pd.merge(html_df, xml_df, on='Clash ID', how='inner', suffixes=('_html', '_xml'))
    #merged_df = merged_df.drop(columns=['Clash ID_xml'])
    merged_df = merged_df.rename(columns={'Issues Status_xml': 'Issues Status', 'View Name_html': 'View Name','Clash ID_html':'Clash ID'})
    merged_df = merged_df[~merged_df['View Name'].str.contains('__', na=False)]
    
    #merged_df['Merge ID'] = merged_df['Clash ID'] + '_' + merged_df['Sub Zone']
    column_order = ["Clash ID", "View Name", "Date Found", "Main Zone", "Sub Zone", "Location", "Level", 
                "Issues Type", "Issues Status", "Description", "Discipline", "Assign To", "Image"]
    #"View Name_Plan", "Image_Plan"
    merged_df = merged_df[column_order]

    merged_df = merged_df.drop_duplicates(subset='Clash ID', keep='first')

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
    
    st.table(filtered_df_display.head(3))


    if st.button("Generate CSV"):
        csv_data = filtered_df_display.to_csv(encoding='utf-8-sig', index=False).encode('utf-8-sig')
        st.download_button(
            label="Download CSV",
            data=BytesIO(csv_data),
            file_name=f"{datetime.datetime.now().strftime('%Y%m%d')}_CSV-Naviswork_{project_name}.csv",
            mime="text/csv"
        )
    if st.button("Generate Report"):
        pdf_data = generate_pdf(filtered_df, project_name)
        st.download_button(
            label="Download PDF Report",
            data=pdf_data,
            file_name=f"{time.strftime('%Y%m%d')}_PDF-Wide-ClashReport_{project_name}.pdf",
            mime="application/pdf"
        )
else:
    st.write("Please upload both HTML and XML files to proceed.")
       


# Replace the "Image" column with the filenames for display in Streamlit table
merged_df_display = merged_df.copy()
# Replace the "Image" column with the actual image objects for processing
if "Image" in merged_df.columns:
    merged_df["ImageName"]=merged_df["Image"]
    merged_df["Image"] = merged_df["Image"].apply(lambda x: image_dict.get(x, "Image not found"))
    #merged_df["Image_Plan_Name"]=merged_df["Image_Plan"]
    #merged_df["Image_Plan"] = merged_df["Image_Plan"].apply(lambda x: image_dict.get(x, "Image not found"))





if 'notes' not in st.session_state:
    st.session_state.notes = {}
if 'usage' not in st.session_state:
    st.session_state.usage = {}
if 'due_dates' not in st.session_state:  # Initialize session state for due dates
    st.session_state.due_dates = {}



if selected_option == "Option 1: Display without merging":
    if not merged_df.empty and uploaded_files:
        if 'df' not in st.session_state:
            st.session_state.df = merged_df.copy()
        df = st.session_state.df
        if 'Notes' not in df.columns:
            df['Notes'] = ""
        if 'Usage' not in df.columns:
            df['Usage'] = "Tracking"
        if 'Assign To' not in df.columns:
            df['Assign To'] = "None"

        df["Notes"].fillna("", inplace=True)
        df["Usage"].fillna("Tracking", inplace=True)
        #df["Date Found"] = pd.to_datetime(df["Date Found"]).dt.strftime("%m/%d/%Y")
        df["Date Found"] = df["Date Found"].apply(try_parsing_date)
        

        st.sidebar.header("Filter Options")
        filter_cols = ['Clash ID', 'View Name', 'Main Zone', 'Sub Zone', 'Level', 
                    'Issues Type', 'Issues Status', 'Discipline', 'Assign To', 'Usage']
        selected_values = {}
        for col in filter_cols:
            unique_values = df[col].unique().tolist()
            selected_values[col] = st.sidebar.selectbox(f'Select {col}', ['All'] + unique_values)

        df_view = df.copy()
        for col, value in selected_values.items():
            if value != 'All':
                df_view = df_view[df_view[col] == value]

        usage_options = ['Tracking', 'High Priority', 'Not Used','For Reporting']
        # Calculate the number of pages after filtering

        ROWS_PER_PAGE = 10

        total_rows = len(df_view)
        total_pages = -(-total_rows // ROWS_PER_PAGE)
        # Only display the slider if there's more than one page
        if total_pages > 1:
            selected_page = st.slider('Select a page:', 1, total_pages)
        else:
            selected_page = 1  # This is a ceiling division

        
        # Filter the dataframe based on the selected page
        start_idx = (selected_page - 1) * ROWS_PER_PAGE
        end_idx = start_idx + ROWS_PER_PAGE

        current_rows = df_view.iloc[start_idx:end_idx]
        for idx, row in current_rows.iterrows():
        
            col1, col2 = st.columns([3, 3])
            with col1:
                st.write(f"<b>{row['View Name']}</b>", unsafe_allow_html=True)
                st.image(row['Image'], use_column_width=True)
                #if row['Image_Plan'] == "Image not found":
                    #st.write("Plan Image not found.")
                #else:
                    #st.image(row['Image_Plan'], use_column_width=True)
            with col2:
                st.write(f"<b>Issue Type:</b> {row['Issues Type']}", unsafe_allow_html=True)
                st.write(f"<b>Issue Status:</b> {row['Issues Status']}", unsafe_allow_html=True)
                st.write(f"<b>Description:</b> {row['Description']}", unsafe_allow_html=True)

                    
                note_key = f"note_{row['Clash ID']}_{idx}"
                initial_note = st.session_state.notes.get(note_key, row['Notes'])
                note = st.text_area(f"Add a note for {row['Clash ID']}", value=initial_note, key=note_key, height=150)

                df_view.at[idx, 'Notes'] = note
                df.at[idx, 'Notes'] = note


                usage_key = f"usage_{row['Clash ID']}_{idx}"
                initial_usage_index = usage_options.index(st.session_state.usage.get(usage_key, row['Usage'])) if st.session_state.usage.get(usage_key, row['Usage']) in usage_options else 0
                usage = st.selectbox('Select usage', usage_options, index=initial_usage_index, key=usage_key)
                df.at[idx, 'Usage'] = usage
                if usage == 'Not Used':
                    df_view.at[idx, 'Issues Status'] = 'Resolved'
                    df.at[idx, 'Issues Status'] = 'Resolved'

                #if df.at[idx, 'Issues Status'] == 'Resolved':
                    #df.at[idx, 'Usage'] = 'Resolved'


                due_date_key = f"due_date_{row['Clash ID']}_{idx}"
                initial_due_date = st.session_state.due_dates.get(due_date_key, datetime.date.today() if pd.isnull(row.get('Due Date')) else pd.to_datetime(row['Due Date']).date())
                due_date = st.date_input(f"Select due date for {row['Clash ID']}", value=initial_due_date, key=due_date_key)

                if 'Due Date' not in df.columns:
                    df['Due Date'] = None
                df_view.at[idx, 'Due Date'] = due_date
                df.at[idx, 'Due Date'] = due_date
            st.markdown("---")


    if st.button("Export CSV"):
        csv_data = df_view.to_csv(encoding='utf-8-sig', index=False).encode('utf-8-sig')
        st.download_button(
            label="Download CSV",
            data=BytesIO(csv_data),
            file_name=f"{datetime.datetime.now().strftime('%Y%m%d')}_CSV-Note_{project_name}.csv",
            mime="text/csv"
        )
    if st.button("Generate ReportA4"):
        pdf_data = generate_pdf2(df_view, project_name)
        st.download_button(
            label="Download PDF Report",
            data=pdf_data,
            file_name=f"{datetime.datetime.now().strftime('%Y%m%d')}_PDF-ClashNoteReport_{project_name}.pdf",
            mime="application/pdf"
        )

    if st.button("Generate Report With Plan"):
        pdf_data = generate_pdf3(df_view, project_name)
        st.download_button(
            label="Download PDF Report",
            data=pdf_data,
            file_name=f"{datetime.datetime.now().strftime('%Y%m%d')}_PDF-ClashNoteReportWithPlan_{project_name}.pdf",
            mime="application/pdf"
        )






elif selected_option == "Option 2: Display with merging":


    
    report_file = st.file_uploader("Upload the Clash Tracking Report CSV file", type=['csv'])
    merge_option = st.checkbox("Do you want to merge the uploaded CSV with the existing data?")

    if not merged_df.empty and uploaded_files and merge_option:
        df_report = pd.read_csv(report_file, encoding='utf-8-sig')
        
        for col in ['Notes', 'Usage', 'Due Date']:
            if col not in df_report.columns:
                df_report[col] = None
            if col not in merged_df.columns:
                merged_df[col] = None

        # Loop-based approach for merging
        for idx, row in merged_df.iterrows():
            match_row = df_report[df_report["Clash ID"] == row["Clash ID"]]
            if not match_row.empty:
                for col in ['Notes', 'Usage', 'Due Date']:
                    if pd.notna(match_row[col].values[0]):
                        merged_df.at[idx, col] = match_row[col].values[0]



        if 'df' not in st.session_state:
            st.session_state.df = merged_df.copy()
        df = st.session_state.df
        if 'Notes' not in df.columns:
            df['Notes'] = ""
        if 'Usage' not in df.columns:
            df['Usage'] = "Tracking"
        if 'Assign To' not in df.columns:
            df['Assign To'] = "None"

        df["Notes"].fillna("", inplace=True)
        df["Usage"].fillna("Tracking", inplace=True)
        #df["Date Found"] = pd.to_datetime(df["Date Found"]).dt.strftime("%m/%d/%Y")
        df["Date Found"] = df["Date Found"].apply(try_parsing_date)
        

        st.sidebar.header("Filter Options")
        filter_cols = ['Clash ID', 'View Name', 'Main Zone', 'Sub Zone', 'Level', 
                    'Issues Type', 'Issues Status', 'Discipline', 'Assign To', 'Usage']
        selected_values = {}
        for col in filter_cols:
            unique_values = df[col].unique().tolist()
            selected_values[col] = st.sidebar.selectbox(f'Select {col}', ['All'] + unique_values)

        df_view = df.copy()
        for col, value in selected_values.items():
            if value != 'All':
                df_view = df_view[df_view[col] == value]

        usage_options = ['Tracking', 'High Priority', 'Not Used','For Reporting']
        # Calculate the number of pages after filtering

        ROWS_PER_PAGE = 10

        total_rows = len(df_view)
        total_pages = -(-total_rows // ROWS_PER_PAGE)
        # Only display the slider if there's more than one page
        if total_pages > 1:
            selected_page = st.slider('Select a page:', 1, total_pages)
        else:
            selected_page = 1  # This is a ceiling division

        
        # Filter the dataframe based on the selected page
        start_idx = (selected_page - 1) * ROWS_PER_PAGE
        end_idx = start_idx + ROWS_PER_PAGE

        current_rows = df_view.iloc[start_idx:end_idx]
        for idx, row in current_rows.iterrows():
        
            col1, col2 = st.columns([3, 3])
            with col1:
                st.write(f"<b>{row['View Name']}</b>", unsafe_allow_html=True)
                st.image(row['Image'], use_column_width=True)

                #if row['Image_Plan'] == "Image not found":
                    #st.write("Plan Image not found.")
                #else:
                    #st.image(row['Image_Plan'], use_column_width=True)
            with col2:
                st.write(f"<b>Issue Type:</b> {row['Issues Type']}", unsafe_allow_html=True)
                st.write(f"<b>Issue Status:</b> {row['Issues Status']}", unsafe_allow_html=True)
                st.write(f"<b>Description:</b> {row['Description']}", unsafe_allow_html=True)

                    
                note_key = f"note_{row['Clash ID']}_{idx}"
                initial_note = st.session_state.notes.get(note_key, row['Notes'])
                note = st.text_area(f"Add a note for {row['Clash ID']}", value=initial_note, key=note_key, height=150)

                df_view.at[idx, 'Notes'] = note
                df.at[idx, 'Notes'] = note


                usage_key = f"usage_{row['Clash ID']}_{idx}"
                initial_usage_index = usage_options.index(st.session_state.usage.get(usage_key, row['Usage'])) if st.session_state.usage.get(usage_key, row['Usage']) in usage_options else 0
                usage = st.selectbox('Select usage', usage_options, index=initial_usage_index, key=usage_key)
                df.at[idx, 'Usage'] = usage
                if usage == 'Not Used':
                    df_view.at[idx, 'Issues Status'] = 'Resolved'
                    df.at[idx, 'Issues Status'] = 'Resolved'

                #if df.at[idx, 'Issues Status'] == 'Resolved':
                    #df.at[idx, 'Usage'] = 'Resolved'


                due_date_key = f"due_date_{row['Clash ID']}_{idx}"
                initial_due_date = st.session_state.due_dates.get(due_date_key, datetime.date.today() if pd.isnull(row.get('Due Date')) else pd.to_datetime(row['Due Date']).date())
                due_date = st.date_input(f"Select due date for {row['Clash ID']}", value=initial_due_date, key=due_date_key)

                if 'Due Date' not in df.columns:
                    df['Due Date'] = None
                df_view.at[idx, 'Due Date'] = due_date
                df.at[idx, 'Due Date'] = due_date
            st.markdown("---")


    if st.button("Export CSV"):
        csv_data = df_view.to_csv(encoding='utf-8-sig', index=False).encode('utf-8-sig')
        st.download_button(
            label="Download CSV",
            data=BytesIO(csv_data),
            file_name=f"{datetime.datetime.now().strftime('%Y%m%d')}_CSV-Note_{project_name}.csv",
            mime="text/csv"
        )
    if st.button("Generate ReportA4"):
        pdf_data = generate_pdf2(df_view, project_name)
        st.download_button(
            label="Download PDF Report",
            data=pdf_data,
            file_name=f"{datetime.datetime.now().strftime('%Y%m%d')}_PDF-ClashNoteReport_{project_name}.pdf",
            mime="application/pdf"
        )
        
    if st.button("Generate Report With Plan"):
        pdf_data = generate_pdf3(df_view, project_name)
        st.download_button(
            label="Download PDF Report",
            data=pdf_data,
            file_name=f"{datetime.datetime.now().strftime('%Y%m%d')}_PDF-ClashNoteReportWithPlan_{project_name}.pdf",
            mime="application/pdf"
        )