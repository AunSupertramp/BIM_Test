import streamlit as st
import xml.etree.ElementTree as ET
from io import BytesIO


st.set_page_config(page_title='XML Viewpoint', page_icon=":1234:", layout='centered')
css_file = "styles/main.css"
with open(css_file) as f:
    st.markdown("<style>{}</style>".format(f.read()), unsafe_allow_html=True)


def parse_xml(file):
    tree = ET.parse(file)
    root = tree.getroot()
    return root, tree

def find_viewpoints_coordinates(root, old_viewpoint_name, new_viewpoint_name):
    coordinates = {}
    for view in root.iter('view'):
        name = view.get('name')
        if old_viewpoint_name in name or new_viewpoint_name in name:
            camera = view.find('viewpoint').find('camera')
            position = camera.find('position').find('pos3f')
            coordinates[name] = (
                float(position.get('x')),
                float(position.get('y')),
                float(position.get('z'))
            )
    return coordinates

def adjust_view_coordinates(root, dx, dy, dz):
    for view in root.iter('view'):
        camera = view.find('viewpoint').find('camera')
        position = camera.find('position').find('pos3f')
        new_x = float(position.get('x')) + dx
        new_y = float(position.get('y')) + dy
        new_z = float(position.get('z')) + dz
        position.set('x', str(new_x))
        position.set('y', str(new_y))
        position.set('z', str(new_z))
    return root

def xml_to_string(root):
    return ET.tostring(root, encoding='utf-8')

# Streamlit UI
st.title("XML Viewpoint Coordinate Adjuster")

uploaded_file = st.file_uploader("Upload XML file", type="xml")

if uploaded_file is not None:
    old_viewpoint_name = st.text_input("Enter old viewpoint name")
    new_viewpoint_name = st.text_input("Enter new viewpoint name")
    
    if old_viewpoint_name and new_viewpoint_name:
        root, tree = parse_xml(uploaded_file)
        coordinates = find_viewpoints_coordinates(root, old_viewpoint_name, new_viewpoint_name)
        
        if len(coordinates) == 2:
            old_coords = coordinates.get(old_viewpoint_name)
            new_coords = coordinates.get(new_viewpoint_name)
            dx = new_coords[0] - old_coords[0]
            dy = new_coords[1] - old_coords[1]
            dz = new_coords[2] - old_coords[2]
            
            st.write(f"Distance X: {dx}")
            st.write(f"Distance Y: {dy}")
            st.write(f"Distance Z: {dz}")
            
            # Adjust other views' coordinates
            adjusted_root = adjust_view_coordinates(root, dx, dy, dz)
            adjusted_xml = xml_to_string(adjusted_root)
            
            st.download_button(
                label="Download Adjusted XML",
                data=adjusted_xml,
                file_name="adjusted_viewpoints.xml",
                mime="text/xml"
            )
        else:
            st.error("Unable to find the specified old and new viewpoints.")
