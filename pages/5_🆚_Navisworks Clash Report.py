import streamlit as st
import pandas as pd
import xml.etree.ElementTree as ET
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
from PIL import Image
from io import BytesIO

st.set_page_config(page_title='Clash Issues Report', page_icon=":vs:", layout='centered')

css_file = "styles/main.css"
with open(css_file) as f:
    st.markdown("<style>{}</style>".format(f.read()), unsafe_allow_html=True)

def process_html(uploaded_file):
    soup = BeautifulSoup(uploaded_file, "html.parser")
    
    data_html = []
    h2_tags = soup.find_all('h2')
    for tag in h2_tags:
        view_name = tag.text.strip()
        img_tag = tag.find_next('img')
        image = img_tag['src'] if img_tag else ''
        data_html.append({"View Name": view_name, "Image": image})

    df_html = pd.DataFrame(data_html)
    return df_html

def split_view_name(view_name):
    parts = view_name.split("_")
    clash_id = parts[0]
    
    date_str = parts[1]
    if len(date_str) == 8 and date_str.isdigit():
        date_found = '-'.join([date_str[:4], date_str[4:6], date_str[6:]])
    elif len(date_str) == 6 and date_str.isdigit():
        date_found = '-'.join(["20" + date_str[:2], date_str[2:4], date_str[4:]])
    else:
        date_found = '2023-07-05'  
    
    main_zone = parts[2] if len(parts) > 2 else ""
    sub_zone = parts[3] if len(parts) > 3 else ""
    level = parts[4] if len(parts) > 4 else ""
    description = parts[5] if len(parts) > 5 else ""
    
    discipline_assign = parts[6] if len(parts) > 6 else ""
    discipline, _, assign_to = discipline_assign.partition(" By ")
    
    due_date = (datetime.strptime(date_found, "%Y-%m-%d") + timedelta(weeks=2)).strftime("%Y-%m-%d")
    
    return clash_id, view_name, date_found, main_zone, sub_zone, level, description, discipline, assign_to, due_date

def process_xml(uploaded_file):
    tree = ET.parse(uploaded_file)
    root = tree.getroot()
    data_xml = []
    
    # Extracting the top-most viewfolder names and their associated views
    top_most_viewfolders = ["Major", "Minor", "NoIssueType"]
    top_most_viewfolder_data = {}
    issues_status_data = {}
    
    for viewfolder_name in top_most_viewfolders:
        for viewfolder in root.findall(f'.//viewfolder[@name="{viewfolder_name}"]'):
            issues_status = viewfolder.attrib.get('name', '')
            for view in viewfolder.findall('.//view'):
                view_name = view.attrib.get('name', '')
                top_most_viewfolder_data[view_name] = viewfolder_name
                issues_status_data[view_name] = issues_status
    
    for view in root.findall('.//view'):
        view_name = view.attrib.get('name', '')
        
        if "*" not in view_name:
            clash_id, view_name, date_found, main_zone, sub_zone, level, description, discipline, assign_to, due_date = split_view_name(view_name)
            
            # Extracting "Assign To" from view name by splitting at the last underscore
            last_underscore_index = view_name.rfind('_')
            if last_underscore_index != -1:
                assign_to = view_name[last_underscore_index + 1:]
            
            data_xml.append({
                "Clash ID": clash_id,
                "View Name": view_name,
                "Date Found": date_found,
                "Main Zone": main_zone,
                "Sub Zone": sub_zone,
                "Level": level,
                "Issues Type": top_most_viewfolder_data.get(view_name, 'Unknown'),
                "Issues Status": issues_status_data.get(view_name, 'Unresolved'),
                "Description": description,
                "Discipline": discipline,
                "Assign To": assign_to,
                "Due Date": due_date
            })
    
    df_xml = pd.DataFrame(data_xml)
    return df_xml







def display_images(uploaded_images):
    for image in uploaded_images:
        st.image(image, caption=image.name)

def merge_and_display(df_xml, df_html):
    merged_df = pd.merge(df_xml, df_html, on="View Name", how="left")
    st.write(merged_df)
    return merged_df

def download_csv_option(merged_df):
    csv_data = merged_df.to_csv(index=False).encode('utf-8-sig')
    filename = "merged_data.csv"
    st.download_button(
        label="Download CSV",
        data=BytesIO(csv_data),
        file_name=filename,
        mime="text/csv"
    )

def main():
    st.title('XML and HTML Processor')
    
    uploaded_html = st.file_uploader("Choose an HTML file", type="html")
    if uploaded_html:
        df_html = process_html(uploaded_html)

    uploaded_xml = st.file_uploader("Choose an XML file", type="xml")
    if uploaded_xml:
        df_xml = process_xml(uploaded_xml)

    uploaded_images = st.file_uploader("Choose JPEG files", type="jpg", accept_multiple_files=True)
    if uploaded_images:
        display_images(uploaded_images)

    if uploaded_html and uploaded_xml:
        merged_df = merge_and_display(df_xml, df_html)
        download_csv_option(merged_df)

if __name__ == "__main__":
    main()
