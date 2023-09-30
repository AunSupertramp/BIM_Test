import streamlit as st
from xml.etree import ElementTree as ET
import pandas as pd
from io import BytesIO

st.set_page_config(page_title='File Combiner and Transformer', page_icon=":watch:", layout='centered')
css_file = "styles/main.css"
with open(css_file) as f:
    st.markdown("<style>{}</style>".format(f.read()), unsafe_allow_html=True)

st.title('XML View Name and Comment Extractor')

uploaded_file = st.file_uploader("Choose an XML file", type="xml")

if uploaded_file is not None:
    # Parse the uploaded XML file
    tree = ET.parse(uploaded_file)
    root = tree.getroot()

    # Extract view names and comments
    data = []
    for view in root.findall('.//view'):
        view_name = view.get('name')
        rltext = view.find('.//rltext/text')
        comment = rltext.text if rltext is not None else None
        data.append({'View Name': view_name, 'Comment': comment})

    # Create a DataFrame
    df = pd.DataFrame(data)

    # Display the first few rows of the DataFrame
    st.write(df.head())

    # Offer to save the data to a CSV file
    if st.button("Generate CSV"):
        filename = "transformed_data.csv"
        csv_data = df.to_csv(encoding='utf-8-sig', index=False).encode('utf-8-sig')
        st.download_button(
            label="Download CSV",
            data=BytesIO(csv_data),
            file_name=filename,
            mime="text/csv"
        )
