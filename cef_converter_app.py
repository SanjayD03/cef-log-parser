#Import Libraries
import streamlit as st
import pandas as pd
import os
import re

#App Title and File Upload
# Title
st.title("CEF to CSV Converter - Anaplan Log Parser")

# File uploader
file = st.file_uploader("Upload .cef File", type=["cef"])

# Processing function
def process_cef(file):
    try:
        # Load data
        df = pd.read_csv(file, sep='|', header=None)

        # Rename columns
        df = df.rename(columns={0: 'Time stamp', 5: 'actions', 6: 6})

        # Extract user ID
        user_id = []
        for i in range(df.shape[0]):
            check_list = str(df[6][i]).split(' ')
            for j in check_list:
                if "userId" in j:
                    user_id.append(j[7:])
                    break
            else:
                user_id.append("NO USER ID")
        df['User ID'] = user_id

        # Extract workspace ID
        workspace_id = []
        for i in range(df.shape[0]):
            check_list = str(df[6][i]).split(' ')
            found = False
            for j in check_list:
                if "workspaceId" in j:
                    parts = j.split(',')
                    for k in parts:
                        x = k.find("workspaceId")
                        if x >= 0:
                            workspace_id.append(k[x+14:].replace('}', '').strip('"'))
                            found = True
                            break
                    if found:
                        break
            if not found:
                workspace_id.append(f"NO WORKSPACE ID FOUND at {i}")
        df['Workspace ID'] = workspace_id

        # Drop unnecessary columns
        df.drop(columns=[1, 2, 3, 4, 6], inplace=True, errors='ignore')

        # Clean timestamp
        df['Time stamp'] = df['Time stamp'].astype(str).apply(lambda x: x[:-9] if 'T' in x and len(x) > 8 else x)
        df['Date'] = df['Time stamp'].apply(lambda x: x.split('T')[0] if 'T' in x else '')
        df['Time'] = df['Time stamp'].apply(lambda x: x.split('T')[1] if 'T' in x else '')

        # Filter for Butterfly workspace
        butterfly_id = '8a81b09b664b166b016654daf2185553'
        filtered_df = df[df['Workspace ID'] == butterfly_id].reset_index(drop=True)
        filtered_df['flag'] = True

        # Extract timestamp from file name
        base_filename = os.path.basename(file.name)
        match = re.search(r"user_activity.*", base_filename)
        suffix = match.group(0).replace(".cef", "") if match else "output"

        # Output file name
        output_filename = f"Butterfly_CM_RM_PM - {suffix}.csv"
        filtered_df.to_csv(output_filename, index=False)

        return df, filtered_df, output_filename, butterfly_id

    except Exception as e:
        st.error(f"Error processing file: {e}")
        return None, None, None, None
		
#UI Logic and Output
if file is not None:
    st.info("Processing file...")
    df_all, df_filtered, out_file, workspace_id_used = process_cef(file)

    if df_filtered is not None:
        st.success("✅ File successfully processed and saved.")
        st.subheader("🔍 Preview of Filtered Data")
        st.dataframe(df_filtered.head(10))

        with open(out_file, "rb") as f:
            st.download_button("📥 Download CSV", f, file_name=out_file, mime='text/csv')

        # Summary stats
        st.subheader("📊 Summary")
        st.write(f"**Filtered Workspace ID**: `{workspace_id_used}`")
        st.write(f"**Total Records in Uploaded File**: `{df_all.shape[0]}`")
        st.write(f"**Records after Filtering**: `{df_filtered.shape[0]}`")