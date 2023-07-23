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
import time
from PIL import Image as pil_image
import os
import requests
from io import BytesIO
import tempfile

pdfmetrics.registerFont(TTFont('Sarabun', r'./Font/THSarabunNew.ttf'))
pdfmetrics.registerFont(TTFont('Sarabun-Bold', r'./Font/THSarabunNew Bold.ttf'))

def main():
    st.title('Clash Report Generator')
    project_name = st.text_input("Enter Project Name:")
    csv_file = st.file_uploader("Upload CSV", type=['csv'])
    
    if csv_file is not None:
        df = pd.read_csv(csv_file, encoding='utf-8-sig')
        df = df.dropna()

        df = df.rename(columns={
            "Clash ID": "Clash ID",
            "ViewName": "View Name",
            "Date Found": "Date Found",
            "Main Zone": "Main Zone",
            "Sub Zone": "Sub Zone",
            "Level": "Level",
            "Issues Type": "Issues Type",
            "Issues Status": "Issues Status",
            "Description": "Description",
            "Discipline": "Discipline",
            "Assign to": "Assign to",
            "ImagePath": "Image"
        })

        df["Date Found"] = pd.to_datetime(df["Date Found"]).dt.strftime("%m/%d/%Y")
        st.table(df.head(10))

        if st.button("Generate Report"):
            output_file = tempfile.NamedTemporaryFile(delete=False).name
            logo_path = r"./Media/1-Aurecon-logo-colour-RGB-Positive.png"
            generate_pdf(df, logo_path, project_name, output_file)

def generate_pdf(df, logo_path, project_name, output_file):
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

    pdf = MyDocTemplate(output_file, pagesize=landscape(A3))

    styles = getSampleStyleSheet()
    cell_style = styles["Normal"]
    cell_style.fontName = "Sarabun"
    cell_style.alignment = TA_LEFT

    header_style = ParagraphStyle(
        "HeaderStyle",
        parent=styles["Normal"],
        fontName="Sarabun-Bold",
        fontSize=14,
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
        ('FONTSIZE', (0, 0), (-1, 0), 14),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('STYLE', (0, 0), (-1, -1), cell_style),
    ]

    header_data = [Paragraph(cell, header_style) for cell in df.columns.tolist()]
    content = []

    for _, row in df.iterrows():
        img_data = get_image_from_file(row["Image"])
        img = Image(BytesIO(img_data), width=60, height=60)
        row_data = [
            Paragraph(str(row["Clash ID"]), cell_style),
            Paragraph(str(row["View Name"]), cell_style),
            Paragraph(str(row["Date Found"]), cell_style),
            Paragraph(str(row["Main Zone"]), cell_style),
            Paragraph(str(row["Sub Zone"]), cell_style),
            Paragraph(str(row["Level"]), cell_style),
            Paragraph(str(row["Issues Type"]), cell_style),
            Paragraph(str(row["Issues Status"]), cell_style),
            Paragraph(str(row["Description"]), cell_style),
            Paragraph(str(row["Discipline"]), cell_style),
            Paragraph(str(row["Assign to"]), cell_style),
            img
        ]
        content.append(row_data)

    data = [header_data] + content

    table = Table(data, repeatRows=1, style=table_style)
    elems = [Spacer(1, 0.5*inch), table]
    pdf.build(elems)

def get_image_from_file(img_path):
    try:
        # If it's a URL, download the image and return the content
        response = requests.get(img_path)
        response.raise_for_status()
        return response.content
    except requests.exceptions.RequestException:
        # If it's a local file, open and read the image, then return the content
        with open(img_path, 'rb') as f:
            return f.read()

if __name__ == "__main__":
    main()
