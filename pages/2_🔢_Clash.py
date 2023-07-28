import streamlit as st
import pandas as pd
import os
from PIL import Image
import datetime

st.set_page_config(page_title='Clash Issues', page_icon=":1234:", layout='centered')

project_name = st.text_input("Please enter the project name", value="Project")
uploaded_file = st.file_uploader("Choose a CSV file", type="csv")


if uploaded_file is not None:
    data = pd.read_csv(uploaded_file, encoding='utf-8-sig')
    data = data.dropna()
    data["Date Found"] = pd.to_datetime(data["Date Found"]).dt.strftime("%m/%d/%Y")

    st.sidebar.header("Filter Options")
    
    clash_id_list = data['Clash ID'].unique().tolist()
    view_name_list = data['ViewName'].unique().tolist()
    main_zone_list = data['Main Zone'].unique().tolist()
    sub_zone_list = data['Sub Zone'].unique().tolist()
    level_list = data['Level'].unique().tolist()
    issues_type_list = data['Issues Type'].unique().tolist()
    issues_status_list = data['Issues Status'].unique().tolist()
    discipline_list = data['Discipline'].unique().tolist()
    assign_to_list = data['Assign to'].unique().tolist()

    selected_clash_id = st.sidebar.selectbox('Select Clash ID', ['All'] + clash_id_list)
    selected_view_name = st.sidebar.selectbox('Select View Name', ['All'] + view_name_list)
    selected_main_zone = st.sidebar.selectbox('Select Main Zone', ['All'] + main_zone_list)
    selected_sub_zone = st.sidebar.selectbox('Select Sub Zone', ['All'] + sub_zone_list)
    selected_level = st.sidebar.selectbox('Select Level', ['All'] + level_list)
    selected_issues_type = st.sidebar.selectbox('Select Issues Type', ['All'] + issues_type_list)
    selected_issues_status = st.sidebar.selectbox('Select Issues Status', ['All'] + issues_status_list)
    selected_discipline = st.sidebar.selectbox('Select Discipline', ['All'] + discipline_list)
    selected_assign_to = st.sidebar.selectbox('Select Assign to', ['All'] + assign_to_list)
    selected_usage = st.sidebar.selectbox('Select Usage', ['All', 'Using', 'Not Used'])

    if selected_clash_id != 'All':
        data = data[data['Clash ID'] == selected_clash_id]
    if selected_view_name != 'All':
        data = data[data['ViewName'] == selected_view_name]
    if selected_main_zone != 'All':
        data = data[data['Main Zone'] == selected_main_zone]
    if selected_sub_zone != 'All':
        data = data[data['Sub Zone'] == selected_sub_zone]
    if selected_level != 'All':
        data = data[data['Level'] == selected_level]
    if selected_issues_type != 'All':
        data = data[data['Issues Type'] == selected_issues_type]
    if selected_issues_status != 'All':
        data = data[data['Issues Status'] == selected_issues_status]
    if selected_discipline != 'All':
        data = data[data['Discipline'] == selected_discipline]
    if selected_assign_to != 'All':
        data = data[data['Assign to'] == selected_assign_to]

    notes = []

    for idx in range(len(data)):
        image_path = data.iloc[idx]['ImagePath']
        view_name = data.iloc[idx]['ViewName']
        clash_id = data.iloc[idx]['Clash ID']
        issue_type = data.iloc[idx]['Issues Type']
        issue_status = data.iloc[idx]['Issues Status']
        try:
            image = Image.open(image_path)

            col1, col2 = st.columns([3, 3])
            with col1:
                st.image(image, use_column_width=True)
            with col2:
                st.write(view_name)
                st.write(f"Issue Type: {issue_type}")
                st.write(f"Issue Status: {issue_status}")
                #note = st.text_input(f"Add a note for {clash_id}", key=str(idx))
                note = st.text_area(f"Add a note for {clash_id}", key=str(idx))

                usage = st.selectbox('Select usage', ['Using', 'Not Used'], key=f"usage_{idx}")
                notes.append((note, usage))
                
            st.markdown("---")  # Draw a horizontal line after each row

        except Exception as e:
            st.write(f"Error loading image: {e}")

    # Split the notes into separate note and usage columns
    data['Text Note'] = [note for note, usage in notes]
    data['Usage'] = [usage for note, usage in notes]

    if 'Usage' in data.columns and selected_usage != 'All':
        data = data[data['Usage'] == selected_usage]

    st.table(data)

    if st.button("Export CSV"):
        # Get the project name from the user
        # Generate the filename using the current date and the project name
        filename = datetime.datetime.now().strftime("%Y_%m_%d") + "_" + project_name + ".csv"
    
        desktop_path = os.path.join(os.path.expanduser('~'), 'Desktop')
        file_path = os.path.join(desktop_path, filename)
        data.to_csv(file_path, encoding='utf-8-sig', index=False)
        st.write("File exported successfully!")
else:
    st.write("Please upload a CSV file.")
