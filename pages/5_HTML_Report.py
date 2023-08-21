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
from bs4 import BeautifulSoup

st.set_page_config(page_title='Generate PDF Report', page_icon=":cityscape:", layout='centered')

pdfmetrics.registerFont(TTFont('Sarabun', r'./Font/THSarabunNew.ttf'))
pdfmetrics.registerFont(TTFont('Sarabun-Bold', r'./Font/THSarabunNew Bold.ttf'))

def process_zip(zip_file):
    with zipfile.ZipFile(zip_file, 'r') as z:
        file_names = z.namelist()
        image_dict = {}
        for file_name in file_names:
            if file_name.endswith(('.jpg', '.jpeg', '.png')):
                with z.open(file_name) as img_file:
                    image_data = BytesIO(img_file.read())
                    image_dict[file_name] = image_data
        return image_dict

def process_html_content(html_content):
    soup = BeautifulSoup(html_content, 'html.parser')
    h2_tags = soup.find_all('h2')
    data = []

    for h2 in h2_tags:
        img = h2.find_next('img')
        img_src = img['src'] if img else None
        data.append((h2.text.strip(), img_src))

    df = pd.DataFrame(data, columns=['View Name', 'Image'])

    multiple_underscores_df = df[df['View Name'].str.count('_') > 1]
    filtered_no_asterisk_df = multiple_underscores_df[~multiple_underscores_df['View Name'].str.contains('\*')]
    
    split_columns = filtered_no_asterisk_df['View Name'].str.split('_', expand=True)
    renamed_columns = {
        0: "Clash ID",
        1: "Date Found",
        2: "Main Zone",
        3: "Sub Zone",
        4: "Level",
        5: "Discipline",
        6: "Description",
        7: "Issues Type",
        8: "Assign To"
    }
    split_columns = split_columns.rename(columns=renamed_columns)
    expanded_df = pd.concat([filtered_no_asterisk_df, split_columns], axis=1)

    expanded_df['Formatted Date'] = expanded_df['Date Found'].apply(convert_date_format)
    filtered_date_df = expanded_df.dropna(subset=['Formatted Date'])

    filtered_date_df['Issues Status'] = ""

    desired_order = ["Clash ID", "View Name", "Date Found", "Main Zone", "Sub Zone", "Level", 
                     "Issues Type", "Issues Status", "Description", "Discipline", "Assign To", "Image"]
    reordered_df = filtered_date_df[desired_order]

    return reordered_df

def convert_date_format(date_str):
    try:
        formatted_date = "20" + date_str[:2] + date_str[2:4] + date_str[4:6]
        dt_object = pd.to_datetime(formatted_date, format='%Y%m%d')
        return dt_object.strftime('%d/%m/%Y')
    except:
        return None

def main():
    st.title('Clash Report Generator')
    project_name = st.text_input("Enter Project Name:")

    html_file = st.file_uploader("Upload HTML", type=['html'])

    if html_file:
        html_content = html_file.read().decode('utf-8')
        df = process_html_content(html_content)
        
        zip_file = st.file_uploader("Upload Image Zip", type=['zip'])
        if zip_file:
            image_dict = process_zip(zip_file)

            def get_image_placeholder(x):
                return "Image" if x.split("/")[-1] in image_dict else "Image not found"

            df["Image"] = df["Image"].apply(get_image_placeholder)

            st.table(df.head(3))

            if st.button("Generate Report"):
                pdf_data = generate_pdf(df, project_name, image_dict)
                st.download_button(
                    label="Download PDF Report",
                    data=pdf_data,
                    file_name=f"{time.strftime('%Y%m%d')}_ClashReport_{project_name}.pdf",
                    mime="application/pdf"
                )

def generate_pdf(df, project_name, image_dict):
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

    for _, row in df.iterrows():
        img_data = image_dict.get(row['Image'], "Image not found")
        if img_data != "Image not found":
            img_data.seek(0)  # Reset the file pointer to the beginning
            img = Image(img_data, width=150, height=150)
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
    column_order = ["Clash ID", "Image", "View Name", "Date Found", "Main Zone", "Sub Zone", "Level",
                    "Issues Type", "Issues Status", "Description", "Discipline", "Assign To"]
    header_data_reordered = [header_data[df.columns.get_loc(col)] for col in column_order]

    data = [header_data_reordered] + content
    col_widths = [100, 170, 80, 80, 80, 80, 80, 80, 80, 90, 80, 80]
    table = Table(data, colWidths=col_widths, repeatRows=1, style=table_style)
    elems = [Spacer(1, 0.5*inch), table]
    pdf.build(elems)
    output.seek(0)
    return output

if __name__ == "__main__":
    main()
