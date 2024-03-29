import streamlit as st
import pandas as pd
import time
import plotly.graph_objects as go
import numpy as np
import plotly.express as px
import matplotlib.pyplot as plt
import altair as alt

st.set_page_config(layout="wide")

@st.cache_data(ttl=120, show_spinner=True)
def load_data(url):
    df = pd.read_csv(url)
    df['Date Created'] = pd.to_datetime(df['Date Created'], errors='coerce')  # set 'Date Created' as datetime
    df.rename(columns={'In process (On It SME)': 'SME (On It)'}, inplace=True)  # Renaming column
    return df

def calculate_metrics(df):
    unique_case_count = df['Service'].count()
    survey_avg = df['Survey'].mean()
    survey_count = df['Survey'].count()
    return unique_case_count, survey_avg, survey_count

def convert_to_seconds(time_str):
    if pd.isnull(time_str):
        return 0
    try:
        h, m, s = map(int, time_str.split(':'))
        return h * 3600 + m * 60 + s
    except ValueError:
        return 0

def seconds_to_hms(seconds):
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    seconds = seconds % 60
    return f"{int(hours):02d}:{int(minutes):02d}:{int(seconds):02d}"

url = 'https://docs.google.com/spreadsheets/d/e/2PACX-1vTyaNjkYwSc-mA_Bf3CcvP0kc7zSTkMIizPBIZB859tmhIH5C8iwwNhhqSKapN8bnN_NC56V3rOV_zg/pub?gid=0&single=true&output=csv'
df = load_data(url).copy()

st.write(':wave: Welcome:exclamation:')
st.title(':new: SRR Management View')

# Button to refresh the data
if st.button('Refresh Data'):
    st.experimental_memo.clear()
    st.experimental_rerun()

# Sidebar with a dropdown for 'Service' column filtering
with st.sidebar:
    selected_service = st.selectbox('Select a Service', ['All'] + list(df['Service'].unique()))

# Apply filtering
if selected_service != 'All':
    df_filtered = df[df['Service'] == selected_service]
else:
    df_filtered = df

# Sidebar with a dropdown for 'Month' column filtering
with st.sidebar:
    selected_month = st.selectbox('Select a Month', ['All'] + list(df_filtered['Month'].unique()))

# Apply filtering
if selected_month != 'All':
    df_filtered = df_filtered[df_filtered['Month'] == selected_month]
else:
    df_filtered = df_filtered

# Sidebar with a dropdown for 'Weekend?' column filtering
with st.sidebar:
    selected_weekend = st.selectbox('Select a Weekend?', ['All', 'Yes', 'No'])

# Apply filtering
if selected_weekend != 'All':
    df_filtered = df_filtered[df_filtered['Weekend?'] == selected_weekend]
else:
    df_filtered = df_filtered

# Sidebar with a dropdown for 'Working Hours?' column filtering
with st.sidebar:
    selected_working_hours = st.selectbox('Select a Working Hours?', ['All', 'Yes', 'No'])

# Apply filtering
if selected_working_hours != 'All':
    df_filtered = df_filtered[df_filtered['Working Hours?'] == selected_working_hours]
else:
    df_filtered = df_filtered

# DataFrames for "In Queue" and "In Progress"
df_inqueue = df[df['Status'] == 'In Queue']
df_inqueue = df_inqueue[['Case #', 'Requestor','Service','Creation Timestamp', 'Message Link 0']]
df_inprogress = df[df['Status'] == 'In Progress']
df_inprogress = df_inprogress[['Case #', 'Requestor','Service','Creation Timestamp', 'SME (On It)', 'TimeTo: On It', 'Message Link 1']]

# Display the filtered dataframe
st.title('Data')
with st.expander('Show Data', expanded=False):
    st.dataframe(df_filtered)

# Metrics
df_filtered['TimeTo: On It Sec'] = df_filtered['TimeTo: On It'].apply(convert_to_seconds)
df_filtered['TimeTo: Attended Sec'] = df_filtered['TimeTo: Attended'].apply(convert_to_seconds)
overall_avg_on_it = df_filtered['TimeTo: On It Sec'].mean()
overall_avg_attended = df_filtered['TimeTo: Attended Sec'].mean()
unique_case_count, survey_avg, survey_count = calculate_metrics(df_filtered)

# Display metrics
col1, col2, col3, col4, col5 = st.columns(5)
with col1:
    st.metric(label="Interactions", value=unique_case_count)
with col2:
    st.metric(label="Survey Avg.", value=f"{survey_avg:.2f}")
with col3:
    st.metric(label="Answered Surveys", value=survey_count)
with col4:
    st.metric("Overall Avg. TimeTo: On It", seconds_to_hms(overall_avg_on_it))
with col5:
    st.metric("Overall Avg. TimeTo: Attended", seconds_to_hms(overall_avg_attended))

# Display "In Queue" DataFrame with count
st.title(f'In Queue:exclamation: ({len(df_inqueue)})')
with st.expander("Show Data", expanded=False):
    st.dataframe(df_inqueue)

# Display "In Progress" DataFrame with count
st.title(f'In Progress:hourglass: ({len(df_inprogress)})')
with st.expander("Show Data", expanded=False):
    st.dataframe(df_inprogress)

agg_month = df_filtered.groupby('Month').agg({
    'TimeTo: On It Sec': 'mean',
    'TimeTo: Attended Sec': 'mean'
}).reset_index()

agg_month['TimeTo: On It'] = agg_month['TimeTo: On It Sec'].apply(seconds_to_hms)
agg_month['TimeTo: Attended'] = agg_month['TimeTo: Attended Sec'].apply(seconds_to_hms)

agg_service = df_filtered.groupby('Service').agg({
    'TimeTo: On It Sec': 'mean',
    'TimeTo: Attended Sec': 'mean'
}).reset_index()

agg_service['TimeTo: On It'] = agg_service['TimeTo: On It Sec'].apply(seconds_to_hms)
agg_service['TimeTo: Attended'] = agg_service['TimeTo: Attended Sec'].apply(seconds_to_hms)

st.set_option('deprecation.showPyplotGlobalUse', False)

# Instead of converting these columns to datetime, consider converting seconds to minutes or hours for a more interpretable visualization
agg_month['TimeTo: On It Minutes'] = agg_month['TimeTo: On It Sec'] / 60
agg_month['TimeTo: Attended Minutes'] = agg_month['TimeTo: Attended Sec'] / 60

# # Now plot these columns
# st.set_option('deprecation.showPyplotGlobalUse', False)
# fig, ax = plt.subplots()
# agg_month.plot(x='Month', y=['TimeTo: On It Minutes', 'TimeTo: Attended Minutes'], kind='bar', stacked=True, ax=ax)

# # Customizing the plot
# plt.xlabel('Month')
# plt.ylabel('Average Time (Minutes)')
# plt.title('Average Resolution Time by Month')
# plt.legend(['Time to: On It', 'Time to: Attended'], loc='upper right')

# # Display the plot using Streamlit
# st.pyplot(fig)

col1,col5 = st.columns(2)

# Create an interactive bar chart using Altair

# Adjust the column names to remove spaces and special characters
agg_month.rename(columns={
    'TimeTo: On It Minutes': 'TimeTo_On_It_Minutes',
    'TimeTo: Attended Minutes': 'TimeTo_Attended_Minutes'
}, inplace=True)

agg_month_long = agg_month.melt(id_vars=['Month'],
                                value_vars=['TimeTo_On_It_Minutes', 'TimeTo_Attended_Minutes'],
                                var_name='Category',
                                value_name='Minutes')

# Create a stacked bar chart
chart = alt.Chart(agg_month_long).mark_bar().encode(
    x='Month',
    y=alt.Y('Minutes', stack='zero'),  # Use stack='zero' for stacking
    color='Category',  # Color distinguishes the categories
    tooltip=['Month', 'Category', 'Minutes']  # Optional: add tooltip for interactivity
).properties(
    title='Monthly Response Times',
    width=600,
    height=400
)

# To display the chart in your Streamlit app
with col1:
    st.write(chart)

# Convert seconds to minutes directly for 'agg_service'
agg_service['TimeTo_On_It_Minutes'] = agg_service['TimeTo: On It Sec'] / 60
agg_service['TimeTo_Attended_Minutes'] = agg_service['TimeTo: Attended Sec'] / 60

# Now, the DataFrame 'agg_service' contains correctly named columns for melting
agg_service_long = agg_service.melt(id_vars=['Service'],
                                    value_vars=['TimeTo_On_It_Minutes', 'TimeTo_Attended_Minutes'],
                                    var_name='Category',
                                    value_name='Minutes')

# Create a stacked bar chart
chart2 = alt.Chart(agg_service_long).mark_bar().encode(
    x='Service',
    y=alt.Y('Minutes', stack='zero'),  # Use stack='zero' for stacking
    color='Category',  # Color distinguishes the categories
    tooltip=['Service', 'Category', 'Minutes']  # Optional: add tooltip for interactivity
).properties(
    title='Group Response Times',
    width=600,
    height=400
)

# To display the chart in your Streamlit app
with col5:
    st.write(chart2)

# Create an interactive bar chart using Altair to show the 'unique case count' for each service
chart3 = alt.Chart(df_filtered).mark_bar().encode(
    x='Service',
    y='count()',
    tooltip=['Service', 'count()']
).properties(
    title='Interaction Count',
    width=600,
    height=400
)

# To display the chart in your Streamlit app
with col1:
    st.write(chart3)

# Create an interactive bar chart using Altair to show the 'unique case count' for each 'SME (On It)'
chart4 = alt.Chart(df_filtered).mark_bar().encode(
    x=alt.X('SME (On It)', sort='-y'),  # Sorting based on the count in descending order
    y=alt.Y('count()', title='Unique Case Count'),
    tooltip=['SME (On It)', 'count()']
).properties(
    title='Interactions Handled',
    width=600,
    height=400
)

# To display the chart in your Streamlit app
with col5:
    st.write(chart4)

# Auto-update every 5 minutes
refresh_rate = 120  # 300 seconds = 5 minutes
time.sleep(refresh_rate)
st.rerun()