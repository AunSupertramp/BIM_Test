import streamlit as st
from xml.etree import ElementTree as ET
import pandas as pd
from io import BytesIO

st.title('Get Comment on Viewpoint')

uploaded_file = st.file_uploader("Choose an XML file", type="xml")

if uploaded_file is not None:
    # Parse the uploaded XML file
    tree = ET.parse(uploaded_file)
    root = tree.getroot()

    
    # Extract view names and comments
    data = []
    for view in root.findall('.//view'):
        view_name = view.get('name')
        comments = view.findall('.//rltext/text')
        comment_texts = [comment.text for comment in comments if comment.text is not None]
        combined_comments = "\n".join(comment_texts)
        data.append({'View Name': view_name, 'Comment': combined_comments})

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
