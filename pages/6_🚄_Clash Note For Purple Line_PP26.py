import streamlit as st
import pandas as pd
from PIL import Image, Image as pil_image
import datetime
from io import BytesIO
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import inch
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import (SimpleDocTemplate, Table, TableStyle, Frame, 
                                PageTemplate, BaseDocTemplate, Image as ReportlabImage, 
                                Paragraph, Spacer)
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
import time
from reportlab.lib.styles import ParagraphStyle
import os
import shutil
import tempfile
from bs4 import BeautifulSoup




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
            return pd.to_datetime(text, format=fmt).strftime("%m/%d/%Y")
        except ValueError:
            pass
    # If all formats fail, return the original string
    return text

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



pdfmetrics.registerFont(TTFont('Sarabun', r'./Font/THSarabunNew.ttf'))
pdfmetrics.registerFont(TTFont('Sarabun-Bold', r'./Font/THSarabunNew Bold.ttf'))




if 'notes' not in st.session_state:
    st.session_state.notes = {}
if 'usage' not in st.session_state:
    st.session_state.usage = {}
if 'due_dates' not in st.session_state:  # Initialize session state for due dates
    st.session_state.due_dates = {}

st.set_page_config(page_title='Clash Issues Note Report For Purple Line Project', page_icon=":bullettrain_side:", layout='centered')
css_file = "styles/main.css"
with open(css_file) as f:
    st.markdown("<style>{}</style>".format(f.read()), unsafe_allow_html=True)
image_dict = {}
st.title('Clash Issues Note Report For Purple Line P Pui')
project_name = st.text_input("Please enter the project name", value="")
csv_file = st.file_uploader("Upload CSV", type=['csv'])
uploaded_zip = st.file_uploader("Upload Image ZIP", type=['zip'])
if uploaded_zip:
    zip_images = extract_images_from_zip(uploaded_zip)
    for img_name, img_data in zip_images:
        image_dict[img_name] = img_data
        
ROWS_PER_PAGE = 10

if csv_file:
    if 'df' not in st.session_state:
        st.session_state.df = pd.read_csv(csv_file, encoding='utf-8-sig')
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
        img_name = row['Image']
        if img_name in image_dict:
            img = Image.open(BytesIO(image_dict[img_name]))
            col1, col2 = st.columns([3, 3])
            with col1:
                st.write(f"<b>{row['View Name']}</b>", unsafe_allow_html=True)
                st.image(img, use_column_width=True)
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
        else:
            st.write("Image not found")

    if st.button("Export CSV"):
        filename = datetime.datetime.now().strftime("%Y_%m_%d") + "_" + project_name + ".csv"
        csv_data = df_view.to_csv(encoding='utf-8-sig', index=False).encode('utf-8-sig')
        st.download_button(
            label="Download CSV",
            data=BytesIO(csv_data),
            file_name=filename,
            mime="text/csv"
        )

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
    header_data = ["No.", "Image", "Details", "Note"]
    styles = getSampleStyleSheet()
 
    data = [header_data]
    for idx, (index, row) in enumerate(df.iterrows(), 1):
        img_name = row['Image']
        if img_name in image_dict:
            image_path = ReportlabImage(BytesIO(image_dict[img_name]), width=2.4*inch, height=2.4*inch)
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
        ('BACKGROUND', (0, 0), (-1, 0), '#f0ceff'),
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

if st.button("Generate Report"):
    pdf_data = generate_pdf(df_view, project_name)
    st.download_button(
        label="Download PDF Report",
        data=pdf_data,
        file_name=f"{datetime.datetime.now().strftime('%Y%m%d')}_ClashReport_{project_name}.pdf",
        mime="application/pdf"
    )