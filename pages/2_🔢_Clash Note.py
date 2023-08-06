import streamlit as st
import pandas as pd
import os
from PIL import Image
import datetime

# Set up the page
st.set_page_config(page_title='Clash Issues', page_icon=":1234:", layout='centered')
css_file = "styles/main.css"
with open(css_file) as f:
    st.markdown("<style>{}</style>".format(f.read()), unsafe_allow_html=True)
st.title('Clash Note')

# User input for project name
project_name = st.text_input("Please enter the project name", value="")

# File uploaders
csv_file = st.file_uploader("Upload CSV", type=['csv'])
uploaded_images = st.file_uploader("Upload JPEGs", type=['jpg', 'jpeg'], accept_multiple_files=True)

# Create a dictionary to map image names to their data
image_dict = {img.name: img.getvalue() for img in uploaded_images}

if csv_file:
    df = pd.read_csv(csv_file, encoding='utf-8-sig')
    df = df.dropna()
    df["Date Found"] = pd.to_datetime(df["Date Found"]).dt.strftime("%m/%d/%Y")

    # Drop the 'ImagePath' column
    if 'ImagePath' in df.columns:
        df.drop(columns=['ImagePath'], inplace=True)

    # Ensure 'Notes' and 'Usage' columns exist in df
    if 'Notes' not in df.columns:
        df['Notes'] = ""
    if 'Usage' not in df.columns:
        df['Usage'] = ""

    # Update the DataFrame with the values from the session state before filtering
    for _, row in df.iterrows():
        clash_id = row['Clash ID']
        note_key = f"note_{clash_id}"
        usage_key = f"usage_{clash_id}"

        # Retrieve values from session state or use default values
        default_note = st.session_state.get(note_key, "")
        default_usage = st.session_state.get(usage_key, "Using")

        df.loc[df['Clash ID'] == clash_id, 'Notes'] = default_note
        df.loc[df['Clash ID'] == clash_id, 'Usage'] = default_usage

    st.sidebar.header("Filter Options")

    # Generate filter options based on unique values in the DataFrame
    filter_cols = ['Clash ID', 'View Name', 'Main Zone', 'Sub Zone', 'Level', 
                   'Issues Type', 'Issues Status', 'Discipline', 'Assign to', 'Usage']
    selected_values = {}
    for col in filter_cols:
        unique_values = df[col].unique().tolist()
        selected_values[col] = st.sidebar.selectbox(f'Select {col}', ['All'] + unique_values)
    
    # Apply filters
    for col, value in selected_values.items():
        if value != 'All':
            df = df[df[col] == value]

    # Display data with images
    for idx, row in df.iterrows():
        img_name = row['Image']

        if img_name in image_dict:
            img = Image.open(BytesIO(image_dict[img_name]))

            # Two-column layout
            col1, col2 = st.columns([3, 3])
            with col1:
                st.image(img, use_column_width=True)
            with col2:
                st.write(row['View Name'])
                st.write(f"Issue Type: {row['Issues Type']}")
                st.write(f"Issue Status: {row['Issues Status']}")
                st.write(f"Description: {row['Description']}")

                # Generate unique keys for storing values in session state
                note_key = f"note_{row['Clash ID']}"
                usage_key = f"usage_{row['Clash ID']}"

                note = st.text_area(f"Add a note for {row['Clash ID']}", value=row['Notes'], key=str(idx))
                usage = st.selectbox('Select usage', ['Using', 'Not Used'], index=(1 if row['Usage'] == 'Not Used' else 0), key=f"usage_{idx}")

                # Store the captured values in session state
                st.session_state[note_key] = note
                st.session_state[usage_key] = usage

            st.markdown("---")  # Draw a horizontal line after each row
        else:
            st.write("Image not found")

    # Export to CSV
    if st.button("Export CSV"):
        filename = datetime.datetime.now().strftime("%Y_%m_%d") + "_" + project_name + ".csv"
        csv_data = df.to_csv(encoding='utf-8-sig', index=False).encode('utf-8-sig')
        
        st.download_button(
            label="Download CSV",
            data=BytesIO(csv_data),
            file_name=filename,
            mime="text/csv"
        )
else:
    st.write("Please upload a CSV file.")
