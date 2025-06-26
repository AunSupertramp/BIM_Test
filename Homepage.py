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
# Check if the CSS file exists before trying to open it
try:
    with open(css_file) as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
except FileNotFoundError:
    st.warning(f"CSS file not found: {css_file}. Please ensure it's in the correct path.")


def main():
    # Render the main HTML header
    stc.html(html_temp)

    # --- Start of Sidebar Content ---
    # Any Streamlit command prefixed with 'st.sidebar.' will appear in the sidebar
    st.sidebar.title("Navigation")
    st.sidebar.write("---") # A simple separator

    # Example sidebar elements:
    st.sidebar.header("Reports")
    if st.sidebar.button("Generate Clash Report"):
        st.success("Generating Clash Report...")
        # You would put logic here to navigate or display the report content
    if st.sidebar.button("View & Edit Report"):
        st.info("Showing Report Editor...")
        # Logic for viewing/editing report

    st.sidebar.write("---")
    st.sidebar.header("Settings")
    option = st.sidebar.selectbox(
        "Choose a setting:",
        ("Option A", "Option B", "Option C")
    )
    st.sidebar.slider("Adjust Value", 0, 100, 50)
    # --- End of Sidebar Content ---

    # Main content of the application
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
