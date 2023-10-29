from unicodedata import name
import streamlit as st
import streamlit.components.v1 as stc 

st.set_page_config(page_title='Home Page', page_icon=":derelict_house_building:", layout='centered')
html_temp = """
		<div style="background-color:#ACE1AF;padding:10px;border-radius:10px">
		<h1 style="color:white;text-align:center;">BIM Management App</h1>
		</div>
		"""

css_file="styles/main.css"
with open(css_file) as f:
    st.markdown("<style>{}</style>".format(f.read()), unsafe_allow_html=True)

def main():
    	# st.title("ML Web App with Streamlit")
	stc.html(html_temp)
	st.write("""
	### BIM Clash Report
	Clash detection is a technique used in BIM (Building Information Modeling) that speeds up projects by detecting conflicts between various models during the design process. It allows architects and contractors to avoid the impact of multi-level design revisions, which can result in budget overruns and project delays.
	
	### App Content
	- Generate Clash Report from Naviswork Report (HTML XML JPEG ZIP)
	- View & Edit Report (Add Note)

	### Contact

	- [Facebook](https://www.facebook.com/siwawut.pattanasri/)
	- :green_book: lineID : atomsiwawut
	- 📧: Siwawut.Pattanasri@aurecongroup.com
	- ☎️: 0828952663
	  		
	  			
			""")
	



if __name__ == '__main__':
	main()
	



    
