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

EXTRACTED_FLAG = False

st.set_page_config(page_title='Clash Issues Report', page_icon=":station:", layout='centered')

css_file = "styles/main.css"
with open(css_file) as f:
    st.markdown("<style>{}</style>".format(f.read()), unsafe_allow_html=True)

pdfmetrics.registerFont(TTFont('Sarabun', r'./Font/THSarabunNew.ttf'))
pdfmetrics.registerFont(TTFont('Sarabun-Bold', r'./Font/THSarabunNew Bold.ttf'))

def adjust_convert_date_format(date_str):
    # Check if the date is already in 'YYYY-MM-DD' format
    if len(date_str) == 10 and date_str[4] == '-' and date_str[7] == '-':
        return date_str
    # Adjusted function to handle the date format 'YYMMDD'
    try:
        formatted_date = "20" + date_str[:2] + "-" + date_str[2:4] + "-" + date_str[4:6]
        return formatted_date  # We already have it in 'YYYY-MM-DD' format, so no need for extra conversion
    except:
        return None

def process_html_content(html_content):
    soup = BeautifulSoup(html_content, 'html.parser')
    h2_tags = soup.find_all('h2')
    data = []

    for h2 in h2_tags:
        img = h2.find_next('img')
        img_src = img['src'].split('/')[-1] if img else None  # Extract just the filename from the src
        data.append((h2.text.strip(), img_src))

    df = pd.DataFrame(data, columns=['View Name', 'Image'])

    multiple_underscores_df = df[df['View Name'].str.count('_') > 2]
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

    if 'Date Found' in expanded_df.columns:
        expanded_df['Formatted Date'] = expanded_df['Date Found'].apply(adjust_convert_date_format)
    else:
        expanded_df['Formatted Date'] = None

    filtered_date_df = expanded_df.dropna(subset=['Formatted Date'])
    filtered_date_df['Issues Status'] = ""

    desired_order = ["Clash ID", "View Name", "Date Found", "Main Zone", "Sub Zone", "Level", 
                     "Issues Type", "Issues Status", "Description", "Discipline", "Assign To", "Image"]
    
    # Only reorder columns that are present in the DataFrame
    available_columns = [col for col in desired_order if col in filtered_date_df.columns]
    reordered_df = filtered_date_df[available_columns]

    return reordered_df


def process_xml_content(xml_content):
    root = ET.fromstring(xml_content)
    def extract_view_details(element):
        results = []
        current_folder_name = element.attrib.get('name', None)
        for child in element:
            if child.tag == 'viewfolder':
                results.extend(extract_view_details(child))
            elif child.tag == 'view':
                view_name = child.attrib.get('name', None)
                results.append((view_name, current_folder_name))
        return results

    view_details = extract_view_details(root.find('viewpoints'))
    df_views = pd.DataFrame(view_details, columns=["View Name", "Issues Status"])
    desired_folders = ["01_Resolved", "02_Unresolved", "03_For Tracking", "04_New Issues"]
    filtered_df = df_views[df_views["Issues Status"].isin(desired_folders)]
    status_mapping = {
        "01_Resolved": "Resolved",
        "02_Unresolved": "Unresolved",
        "03_For Tracking": "For Tracking",
        "04_New Issues": "New"
    }
    filtered_df["Issues Status"] = filtered_df["Issues Status"].replace(status_mapping)
    filtered_df = filtered_df[["View Name", "Issues Status"]]
    return filtered_df
    

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
    st.title('Clash Report Generator')
    project_name = st.text_input("Enter Project Name:")
    merged_df = pd.DataFrame()
    html_file = st.file_uploader("Upload HTML File", type=['html'])
    xml_file = st.file_uploader("Upload XML File", type=['xml'])
    
    if html_file and xml_file:  # Check that both files are uploaded
        try:
            html_content = html_file.read().decode('utf-8')
            df_html = process_html_content(html_content)
        
            xml_content = xml_file.read().decode('utf-8')
            df_xml = process_xml_content(xml_content)
        
            # Merge on "View Name"
            merged_df = pd.merge(df_html.drop(columns="Issues Status"), df_xml, on="View Name", how="left")

            # Apply the date formatting function to the entire "Date Found" column of merged_df
            if "Date Found" in merged_df.columns:
                merged_df["Date Found"] = merged_df["Date Found"].apply(adjust_convert_date_format)

            desired_order = ["Clash ID", "View Name", "Date Found", "Main Zone", "Sub Zone", "Level", 
                 "Issues Type", "Issues Status", "Description", "Discipline", "Assign To", "Image"]

            merged_df = merged_df[desired_order]

            if not merged_df.empty:
                #st.table(merged_df.head(3))
                st.write("Merged Complete")
            
        except Exception as e:
            st.write("Error processing files:", str(e))

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

    # Replace the "Image" column with the filenames for display in Streamlit table
    merged_df_display = merged_df.copy()
    # Replace the "Image" column with the actual image objects for processing
    if "Image" in merged_df.columns:
        merged_df["Image"] = merged_df["Image"].apply(lambda x: image_dict.get(x, "Image not found"))
    
    if not merged_df.empty and "Issues Status" in merged_df.columns:
        available_statuses = merged_df["Issues Status"].unique().tolist()
    else:
        available_statuses = []
    selected_statuses = st.multiselect("Select Issues Status for Export:", available_statuses, default=available_statuses)

    if "Issues Status" in merged_df.columns:
        filtered_df = merged_df[merged_df["Issues Status"].isin(selected_statuses)]
    else:
        filtered_df = merged_df
    if "Issues Status" in merged_df_display.columns:
        filtered_df_display = merged_df_display[merged_df_display["Issues Status"].isin(selected_statuses)]
    else:
        filtered_df_display = merged_df_display
    st.table(filtered_df_display.head(10))

    if st.button("Generate CSV"):
        #csv_data = merged_df.to_csv(index=False)
        csv_data = filtered_df_display.to_csv(index=False, encoding='utf-8-sig')
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
        ('BACKGROUND', (0, 0), (-1, 0), colors.purple),
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
                image_stream = BytesIO(img_data.getvalue())
            img_data.seek(0)  # Reset the file pointer
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

if __name__ == "__main__":
    main()
