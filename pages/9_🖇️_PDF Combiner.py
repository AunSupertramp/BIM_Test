import streamlit as st
import pandas as pd
from io import BytesIO
from PyPDF2 import PdfReader, PdfWriter
import io

st.set_page_config(page_title='PDF Combiner', page_icon=":linked_paperclips:", layout='wide')

css_file = "styles/main.css"
with open(css_file) as f:
    st.markdown("<style>{}</style>".format(f.read()), unsafe_allow_html=True)


def combine_pdfs(uploaded_files):
    merger = PdfWriter()

    for file in uploaded_files:
        pdf = PdfReader(file)
        for page in pdf.pages:
            merger.add_page(page)

    combined_pdf_stream = io.BytesIO()
    merger.write(combined_pdf_stream)
    combined_pdf_stream.seek(0)
    
    return combined_pdf_stream

st.title("PDF Combiner")

filename = st.text_input("Enter the filename for the merged PDF:", "")
if not filename.endswith('.pdf'):
    filename += '.pdf'

uploaded_files = st.file_uploader("Choose PDF files", type="pdf", accept_multiple_files=True)

if uploaded_files:
    # Display uploaded files and allow users to reorder
    st.write("Choose the order for merging:")

    file_order_indices = []
    for i in range(len(uploaded_files)):
        file_order = st.selectbox(f"Position {i+1}", 
                                  options=list(range(len(uploaded_files))),
                                  format_func=lambda x: uploaded_files[x].name)
        file_order_indices.append(file_order)

    reordered_files = [uploaded_files[i] for i in file_order_indices]

    if st.button("Merge PDFs") and uploaded_files:
        combined_pdf_stream = combine_pdfs(reordered_files)
        st.download_button("Download Merged PDF", combined_pdf_stream, filename, mime="application/pdf")
