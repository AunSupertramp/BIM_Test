from unicodedata import name
import streamlit as st
import streamlit.components.v1 as stc 


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
		"Clash Detection" 
	
	### App Content
	- Generate Clash Report from CSV
	- View & Edit Report 

	### Contact

	- [Facebook](https://www.facebook.com/siwawut.pattanasri/)
	- [Aurecongroup](https://www.aurecongroup.com/.)
	- Line ID: atomsiwawut
	- 📧: Siwawut.Pattanasri@aurecongroup.com
	- ☎️: 0828952663
	  		
	  			
			""")
	



if __name__ == '__main__':
	main()
	



    
