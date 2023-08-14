import streamlit as st 
import pandas as pd 
import sys
import os
st.set_page_config(page_title='About me',page_icon=":atom_symbol:",layout='wide')
about_variable = "from Main About.py Page"


#st.header('My CV', anchor=None)
#st.subheader("Siwawut Pattanasri")

css_file="styles/main.css"
with open(css_file) as f:
    st.markdown("<style>{}</style>".format(f.read()), unsafe_allow_html=True)

st.markdown("""


# My CV :notebook_with_decorative_cover: 

### Siwawut Pattanasri

##### Digital Solution Development

--- 

""")


empty1,content1,empty2,content2,empty3=st.columns([0.3,1.5,0.3,2,0.3])
with empty1:
        st.empty()
with content1:
        #st.write("here is the first column of content.")
        imageurl="https://raw.githubusercontent.com/atomsiwawut1/FloodPrediction/main/Media/Atom.png"
        #content1.image(".\Media\Atom.png",caption="Siwawut pattanasri",width=300)
        #content1.image(imageurl,caption="Siwawut pattanasri",width=300)
        content1.image(imageurl,caption="Siwawut pattanasri",use_column_width=True)


        st.markdown("""
### Qualifications and Professional Memberships
- ◉ Master of Urban Environmental Planning and Development, Faculty of Architecture and Planning, Thammasat University, Rangsit Campus, Pathumthani, Thailand
                    
- ◉ Bachelor of Civil Engineering, Faculty of Engineering, Thammasat University, Rangsit Campus, Pathumthani, Thailand

- ◉ License for Professional Practice Civil Engineer, Engineering Council of Thailand, Associate Engineer ID.272693

- ◉ Drone license (Thailand)

- ◉ Training certificate
    - ◎ ArchiStar Academy
        - ▹Dynamo Advanced
        - ▹Dynamo Designer
        - ▹Dynamo Essentials
        - ▹SketchUp Essentials
        - ▹Advanced VR in Unreal Engine 4

    - ◎ Linkedin learning
        - ▹Dynamo for Revit Python Scripting
        - ▹BIM 360 Design Essential Training
        - ▹Rhino 7 Essential Training

    - ◎ Google Analytics Academy
        - ▹Data Studio

    - ◎ Maven Analytics
        - ▹Microsoft Power BI - Up & Running With Power BI Desktop   


        """)

with empty2:
        st.empty()
with content2:
        ##st.write("here is the second column of content.")
        st.markdown("""
        
➞      Siwawut has experiences in analysis and design structure of building with CSI software; 3D modelling with BIM software (SketchUp Revit Tekla Structures) management and planning of construction projects with Primavera P6 & Microsoft Project Data Visualization with Power BI and Data analysis with R & Python programming.

--- 
### EXPERTISE AND SKILLS
- ◉ Consulting about using BIM in project (i.e. BIM Model Development, Quantity Takeoff, Scheduling, Clash detection and Facility Management)
- ◉ Technical support for teams (Automation Process, BIM Technical Issues, ETC)
- ◉ Research and stay informed on BIM related software and technologies.

---

### Management skills
- ◉ Information & Data Management : Monitor, manage and reviews project information and data.
- ◉ Scope & Change Control : Defines requirements and scope as key element of any project.
- ◉ Project Leadership : Focuses on strategy, manage details to align team and client towards project success.

---

### Technical skills
- ◉ Digital Modeling - Autodesk Revit, SketchUp, Tekla structure, Rhino 
- ◉ 3D Visualization- D5 Render, Enscape, Unreal Engine 
- ◉ BIM Model Coordination & Management – Autodesk Navisworks, BIM Track and BIM360
- ◉ Computational Design - Dynamo, Grasshopper (Parametric modeling in structural design & Urban Design)
- ◉ Data analyst skills – Python, Power BI (Dashboard, Decision Making Tools for Business)
- ◉ Geospatial Analyst Skills - QGIS, Python Leafmap (Urban Analytics)
- ◉ Machine learning Skills- PythonPackage TensorFlow and scikit-learn (Flood Prediction, Urban Energy Consumption)
- ◉ Drone flying skills : Drone Deploy ,Pix4d (2D Mapping, 3D Mapping)

---

### Relevant Experience
- ◉ Whizdom101 Bangkok, Mixed-use Building; Project Commercial Phase II  (Feb 2019 – 2022), Magnolia Quality Development Corporation Limited | BIM Consultant

- ◉ Terra, Data Center; Project Terra (Feb 2019 – 2021), ST Telemedia Limited | BIM Consultant

- ◉ Sansiri BIM Corporate Service | Bangkok | Sansiri Development High rise & Low Rise | 2019 – 2020 | BIM Corporate Consult

- ◉ Dusit Central Park | Bangkok | Joint Venture of Dusit Thani with Central Pattana | 2019 - 2023 | BIM Management

- ◉ DTGO BIM Corporate Service | Bangkok | 2020 – 2021 | BIM Corporate Consult

- ◉ Bangkok Cybertech District | Bangkok | Magnolia Quality Development Corporation Limited (MQDC) | 2020 - 2023 |BIM consultant

- ◉ PATTAYA WORLDMARK | Chonburi | Magnolia Quality Development Corporation Limited (MQDC) | 2020 - 2025 | BIM Management

- ◉ Pattaya Smart City Platform,Chonburi| EEC Phase 1  | 2021 - 2025 |Urban Development

- ◉ New South Wales, Australian | 2021 - 2022 | BIM Asset Code management

- ◉ AP BIM Corporate Service | Bangkok | 2021 – 2022 | BIM Corporate Consult

- ◉ Next01, Data Center; Project Terra (Feb 2022 – 2023), ST Telemedia Limited | BIM Consultant





        """)

with empty3:
        st.empty()




st.markdown("""

---

""")




empty1,content1,empty2,content2,empty3=st.columns([0.3,1.5,0.3,2,0.3])
with empty1:
        st.empty()
with content1:
        imageurl2 = "https://raw.githubusercontent.com/atomsiwawut1/FloodPrediction/main/Media/City.png"
        #st.image(".\Media\City.png",caption="https://www.facebook.com/siwawut.pattanasri/",width=600)
        #st.image(imageurl2,caption="https://www.facebook.com/siwawut.pattanasri/",width=600)
        st.image(imageurl2,caption="https://www.facebook.com/siwawut.pattanasri/",use_column_width=True)
        #st.image('hackershrine.jpg',use_column_width=True)
with empty2:
        st.empty()
with content2:
        st.markdown("""

## contact

[Facebook](https://www.facebook.com/siwawut.pattanasri/)


lineID : atomsiwawut

:e-mail: atomsiwawut@gmail.com

:telephone_receiver: 0828952663

""")
with empty3:
        st.empty()







