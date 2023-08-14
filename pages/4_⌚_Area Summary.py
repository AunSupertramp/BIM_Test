import streamlit as st
import pandas as pd
from io import BytesIO

st.set_page_config(page_title='File Combiner and Transformer', page_icon=":watch:", layout='centered')
css_file = "styles/main.css"
with open(css_file) as f:
    st.markdown("<style>{}</style>".format(f.read()), unsafe_allow_html=True)
st.title('File Combiner and Transformer for area')

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
        return level_str  # Return the original value for unexpected values or non-"Level" values

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
        combined_pivot['SUM GFA'] = combined_pivot[['Common', 'Amenity', 'BOH', 'Parking']].sum(axis=1)
        combined_pivot['NSA'] = combined_pivot['Unit type']
        combined_pivot['NSA/GFA'] = combined_pivot['NSA'] / combined_pivot['SUM GFA']
        combined_pivot['EFF%'] = combined_pivot['NSA/GFA'] * 100

        for unit_type in all_data[all_data['Department'] == "Unit type"]['Name'].unique():
            unit_pivot = all_data[all_data['Name'] == unit_type].groupby('Level')['GFA_sum'].sum()
            combined_pivot[unit_type] = unit_pivot

        combined_pivot.fillna(0, inplace=True)
        combined_pivot.replace([float('inf'), -float('inf')], 0, inplace=True)
        
        # Alphanumeric reordering of unit type columns
        unit_type_columns = [col for col in combined_pivot.columns if col not in ["Common", "Amenity", "BOH", "Parking", "SUM GFA", "NSA", "NSA/GFA", "EFF%", "Unit type"]]
        sorted_unit_type_columns = sorted(unit_type_columns)
        ordered_columns_alphanumeric = ["Common", "Amenity", "BOH", "Parking", "SUM GFA", "NSA", "NSA/GFA", "EFF%"] + sorted_unit_type_columns
        reordered_df_alphanumeric = combined_pivot[ordered_columns_alphanumeric]

        # Format level names with zero-padded two-digit format
        reordered_df_alphanumeric.index = reordered_df_alphanumeric.index.map(format_level)
        reordered_df_alphanumeric_sorted = reordered_df_alphanumeric.sort_index()

        # Compute totals for each column and append it to the dataframe
        totals = reordered_df_alphanumeric_sorted.sum(numeric_only=True)
        totals_df = pd.DataFrame(totals).T
        totals_df.index = ['Total']
        final_df_with_totals = pd.concat([reordered_df_alphanumeric_sorted, totals_df])

        st.dataframe(final_df_with_totals)
        csv_data = final_df_with_totals.to_csv(encoding='utf-8-sig', index=True).encode('utf-8-sig')
        st.download_button(
            label="Download Transformed CSV",
            data=BytesIO(csv_data),
            file_name="transformed_data.csv",
            mime="text/csv"
        )

main()
