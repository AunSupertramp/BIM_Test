import streamlit as st
import pandas as pd
from io import BytesIO

st.set_page_config(page_title='Home Page', page_icon=":derelict_house_building:", layout='wide')

css_file = "styles/main.css"
with open(css_file) as f:
    st.markdown("<style>{}</style>".format(f.read()), unsafe_allow_html=True)
st.title("Land Area, Green Space, and Assembly Area Calculator")

empty1, content1, empty2, content2, empty3, content3, empty4 = st.columns([0.1, 1, 0.1, 1, 0.1, 1.5, 0.1])

with content1:
    st.markdown("<h4>User Input</h4>", unsafe_allow_html=True)
    Land_Area = st.number_input("Land Area", 0, 10000)
    FAR = st.number_input("FAR (Floor to Area Ratio)", 0, 10)
    total_GFA = Land_Area * FAR
    Req_Open_Space = Land_Area * 0.3
    Cover_Area = st.number_input("Cover_Area", 0, 10000)
    Open_Space = Land_Area - Cover_Area
    Req_Deep_green_by_land_area = Land_Area * 0.15
    number_of_units = st.number_input("Number of Units", 0, 10000)
    Req_Green_area_by_population = number_of_units
    Green_area_proposed_by_LA = st.number_input("Green area proposed by LA", 0, 10000)

with content2:
    st.markdown("<h4>Data Table</h4>", unsafe_allow_html=True)
    df = pd.DataFrame({
        'Parameter': [
            'Land Area',
            'FAR',
            'Total GFA',
            'Open Space',
            'Required Open Space (30%)',
            'Open Space',
            'Cover Area',
            'Required Deep Green by Land Area',
            'Required Green Area by Population',
            'Green Area Proposed by LA'
        ],
        'Value': [
            Land_Area,
            FAR,
            total_GFA,
            Open_Space,
            Land_Area * 0.3,
            Req_Open_Space,
            Cover_Area,
            Req_Deep_green_by_land_area,
            Req_Green_area_by_population,
            Green_area_proposed_by_LA
        ]
    })
    st.dataframe(df)

with content3:
    def sum_gfa_values(row):
        """Converts the "GFA " column to float and sums the values."""
        values = [float(val.replace(" m²", "")) for val in row.split('m²') if val.strip()]
        return sum(values)

    def format_level(level_str):
        """Formats the 'Level' string to ensure the numeric portion is zero-padded to two digits."""
        if "Level" in level_str:
            number = int(level_str.split(' ')[1])
            return f"Level {number:02}"
        else:
            return level_str

    def main():
        uploaded_files = st.file_uploader("Choose CSV or Excel files", type=["csv", "xlsx"], accept_multiple_files=True)

        if uploaded_files:
            dataframes = []
            for uploaded_file in uploaded_files:
                if ".csv" in uploaded_file.name:
                    dataframes.append(pd.read_csv(uploaded_file))
                elif ".xlsx" in uploaded_file.name:
                    dataframes.append(pd.read_excel(uploaded_file))

            all_data = pd.concat(dataframes, ignore_index=True)
            all_data['GFA_sum'] = all_data['GFA '].apply(sum_gfa_values)
            combined_pivot = all_data.pivot_table(index='Level', columns='Department', values='GFA_sum', aggfunc='sum')

            combined_pivot['SUM GFA'] = combined_pivot[['Common', 'Amenity', 'BOH', 'Parking']].sum(axis=1).replace([float('inf'), -float('inf'), None], 0)
            combined_pivot['NSA'] = combined_pivot['Unit type'].fillna(0)
            combined_pivot['CFA'] = combined_pivot['NSA'] + combined_pivot['SUM GFA']
            combined_pivot['Difference (CFA-GFA)'] = combined_pivot['CFA'] - combined_pivot['SUM GFA']
            combined_pivot['GFA / CFA(%)'] = (combined_pivot['SUM GFA'] / combined_pivot['CFA']) * 100
            combined_pivot['NSA / CFA(%)'] = (combined_pivot['NSA'] / combined_pivot['CFA']) * 100
            combined_pivot['NSA/GFA'] = (combined_pivot['NSA'] / combined_pivot['SUM GFA'])
            combined_pivot['EFF%'] = combined_pivot['NSA/GFA'] * 100

            # Ordering columns
            ordered_columns = ["Common", "Amenity", "BOH", "Parking", "SUM GFA", "NSA", "NSA/GFA", "EFF%", "CFA", "Difference (CFA-GFA)", "GFA / CFA(%)", "NSA / CFA(%)"]
            reordered_df = combined_pivot[ordered_columns]
            reordered_df.index = reordered_df.index.map(format_level)
            reordered_df_sorted = reordered_df.sort_index()

            # Replace NaN values with 0
            reordered_df_sorted.fillna(0, inplace=True)

            # Compute totals for each column and append it to the dataframe
            totals = reordered_df_sorted.sum(numeric_only=True)
            totals_df = pd.DataFrame(totals).T
            totals_df.index = ['Total']
            final_df_with_totals = pd.concat([reordered_df_sorted, totals_df])

            st.dataframe(final_df_with_totals)
            csv_data = final_df_with_totals.to_csv(encoding='utf-8-sig', index=True).encode('utf-8-sig')
            st.download_button(
                label="Download Transformed CSV",
                data=BytesIO(csv_data),
                file_name="transformed_data.csv",
                mime="text/csv"
            )

    main()
