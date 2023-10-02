import streamlit as st
import xml.etree.ElementTree as ET
import pandas as pd
import io

def extract_view_details_with_levels(root):
    stack = [(root, [], None)]
    results = []

    while stack:
        element, folder_names, parent_name = stack.pop()
        current_folder_name = element.attrib.get('name', parent_name)
        
        if element.tag == 'view':
            view_name = element.attrib.get('name', None)
            issues_type = folder_names[-4] if len(folder_names) >= 4 else None
            issues_status = folder_names[-3] if len(folder_names) >= 3 else None
            assign_to = folder_names[-2] if len(folder_names) >= 2 else None
            sub_zone = folder_names[-1] if folder_names else None
            results.append((view_name, sub_zone, assign_to, issues_status, issues_type))
        else:
            stack.extend([(child, folder_names + [current_folder_name], current_folder_name) for child in element])
    
    return results


# Updated rename_views_in_xml function with new MergeID logic
def rename_views_in_xml_updated_mergeid(tree):
    # Extract view details and convert to dataframe
    xml_view_details = extract_view_details_with_levels(tree.getroot())
    xml_df = pd.DataFrame(xml_view_details, columns=['View Name', 'Sub Zone', 'Assigned To', 'Issue Status', 'Issue Type'])
    
    # Process the dataframe to get Clash ID and Updated MergeID
    view_name_components_xml = xml_df['View Name'].str.split('_', expand=True)
    xml_df['Clash ID'] = view_name_components_xml[0]
    xml_df['MergeID'] = xml_df['Clash ID'] + '_' + xml_df['Sub Zone'] + '_' + xml_df['Assigned To']
    
    # Group by MergeID and rename views accordingly
    grouped = xml_df.groupby('MergeID')
    for name, group in grouped:
        view_plan_row = group[group['View Name'].str.contains('View \(Plan\)')]
        if not view_plan_row.empty and group.shape[0] > 1:
            corresponding_row = group[(group['View Name'].str.split('_').str.len() >= 3) & (~group['View Name'].str.contains('View \(Plan\)'))]
            if not corresponding_row.empty:
                level_component = corresponding_row['View Name'].str.split('_', expand=True).iloc[0, 1]
                new_view_name = f"{view_plan_row['Clash ID'].values[0]}_{level_component}_View (Plan)"
                
                # Update XML structure
                root = tree.getroot()
                for element in root.iter('view'):
                    if element.attrib.get('name') == view_plan_row['View Name'].values[0]:
                        element.attrib['name'] = new_view_name
                        break
    
    return tree

# Streamlit App UI
st.title("XML Renaming Tool")
uploaded_file = st.file_uploader("Upload XML", type="xml")

if uploaded_file:
    tree = ET.parse(uploaded_file)
    modified_tree = rename_views_in_xml_updated_mergeid(tree)
    
    # Convert modified XML tree to bytes and allow user to download it
    xml_data = io.BytesIO()
    modified_tree.write(xml_data)
    st.download_button(label="Download Modified XML", data=xml_data, file_name="modified.xml", mime="text/xml")