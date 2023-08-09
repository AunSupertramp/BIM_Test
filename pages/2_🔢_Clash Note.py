import streamlit as st
import pandas as pd
from PIL import Image
import datetime
from io import BytesIO

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
uploaded_images = st.file_uploader("Upload Images", type=['jpg', 'jpeg', 'png'], accept_multiple_files=True)

# Create a dictionary to map image names to their data
image_dict = {img.name: img.getvalue() for img in uploaded_images}

# Initialize session state attributes for notes and usage if they don't exist
if 'notes' not in st.session_state:
    st.session_state.notes = {}
if 'usage' not in st.session_state:
    st.session_state.usage = {}

if csv_file:
    df = pd.read_csv(csv_file, encoding='utf-8-sig')
    df = df.dropna()
    df["Date Found"] = pd.to_datetime(df["Date Found"]).dt.strftime("%m/%d/%Y")

    # Ensure 'Notes' and 'Usage' columns exist in df
    if 'Notes' not in df.columns:
        df['Notes'] = ""
    if 'Usage' not in df.columns:
        df['Usage'] = "Tracking"

    # Update the dataframe with session state values
    for idx, row in df.iterrows():
        note_key = f"note_{idx}_{row['Clash ID']}"
        usage_key = f"usage_{idx}_{row['Clash ID']}"
        if note_key in st.session_state:
            df.at[idx, 'Notes'] = st.session_state[note_key]
        if usage_key in st.session_state:
            df.at[idx, 'Usage'] = st.session_state[usage_key]

    st.sidebar.header("Filter Options")

    # Generate filter options based on unique values in the DataFrame
    filter_cols = ['Clash ID', 'View Name', 'Main Zone', 'Sub Zone', 'Level', 
                   'Issues Type', 'Issues Status', 'Discipline', 'Assign To', 'Usage']
    selected_values = {}
    for col in filter_cols:
        unique_values = df[col].unique().tolist()
        selected_values[col] = st.sidebar.selectbox(f'Select {col}', ['All'] + unique_values)

    # Apply filters to the dataframe
    filtered_df = df.copy()
    for col, value in selected_values.items():
        if value != 'All':
            filtered_df = filtered_df[filtered_df[col] == value]

    # Display data with images for the filtered dataframe
    for idx, row in filtered_df.iterrows():
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

                note_key = f"note_{idx}_{row['Clash ID']}"
                initial_note = st.session_state.notes.get(note_key, row['Notes'])
                note = st.text_area(f"Add a note for {row['Clash ID']}", value=initial_note, key=note_key, height=150)
                st.session_state.notes[note_key] = note

                usage_key = f"usage_{idx}_{row['Clash ID']}"
                usage_options = ['Tracking', 'Not Used', 'High Priority']
                initial_usage_value = st.session_state.usage.get(usage_key, row['Usage'])
                usage = st.selectbox('Select usage', usage_options, index=usage_options.index(initial_usage_value), key=usage_key)
                st.session_state.usage[usage_key] = usage

                if usage == 'Not Used':
                    df.at[idx, 'Issues Status'] = 'Resolved'

            st.markdown("---")
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
