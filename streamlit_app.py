import plotly.graph_objects as go
import streamlit as st
import requests
import pandas as pd
import numpy as np
import json
from datetime import timedelta, datetime
from pytz import timezone

# Page configuration
st.set_page_config(
    page_title="Meteo Dashboard",
    page_icon="🌤️",
    layout="centered",
    initial_sidebar_state="expanded"
)

######## Sidebar ########


#### Search for location ####

# Input widget:
with st.sidebar:
    st.write('### Weather Forecast Dashboard')
    location_input = st.text_input("Search for a city:", "Budapest")

# Open Meteo Geocoding API call:
url = "https://geocoding-api.open-meteo.com/v1/search"
params = {
    "name": location_input,
    "count": 1
}

response = requests.get(url, params=params)
if response.status_code == 200: # 200 means success
    response_data = response.json()
    try:
        searched_location = pd.json_normalize(response_data['results'])
    except (NameError, KeyError):
        with st.sidebar:
            st.warning('City not found! Please choose another.')
else:
    with st.sidebar:
        st.write('Error getting data: ', response.status_code)

### Set params for choosen location:
city = searched_location.at[0, 'name']
latitude = searched_location.at[0, 'latitude']
longitude = searched_location.at[0, 'longitude']
coordinates = [{'latitude':latitude, 'longitude':longitude}]
elevation = searched_location.at[0, 'elevation']
country = searched_location.at[0, 'country']
local_timezone = searched_location.at[0, 'timezone']

### Show map in sidebar:
with st.sidebar:    
    st.map(coordinates, zoom=10, size=300)



######## Main area ########


#### Title and info block about the location ####

# Title:
"""
# Weather Forecast Dashboard
Data from [Open-Meteo API](https://open-meteo.com/)
"""

# Create info table:
city_info_table = pd.DataFrame({'City info':['city','latitude','longitude','elevation','country','timezone'], ' ':[city,latitude,longitude,elevation,country,local_timezone]})

# Set params for info table:
st.dataframe(city_info_table, 
             column_config={
                 'index':'',
                 '0':''
             },
             hide_index=True,
             use_container_width=True
             )

# Show date and time of data collection:
current_date = str(pd.to_datetime(datetime.today()))[:16]
st.write(f'Data collected: {current_date} UTC')


#### Funcions ####

def get_meteo_data(url):
    response = requests.get(url)
    if response.status_code == 200: # 200 means success
        data = response.json() # Get the response data as a JSON object
    else:
        print('Error getting data: ', response.status_code)
        
    df = pd.read_json(json.dumps(data))
    return df

def process_daily_data(df):
    # extract daily data without NA-s:
    daily_wo_nan = pd.DataFrame(df['daily'].dropna(how='any'))
    # reorder time, sunrise and sunset data to columns:
    daily = pd.DataFrame()
    for line in daily_wo_nan.index:
        daily[line] = daily_wo_nan['daily'][line]
    # transform string to datetime type:
    daily['sunrise'] = pd.to_datetime(daily['sunrise'])
    daily['sunset'] = pd.to_datetime(daily['sunset'])
    
    return daily

def process_hourly_data(df):
    # extract hourly data without NA-s:
    hourly_wo_nan = pd.DataFrame(df['hourly'].dropna(how='any'))
    # reorder lines into data frame columns:
    hourly = pd.DataFrame()
    for line in hourly_wo_nan.index:
        hourly[line] = hourly_wo_nan['hourly'][line]
    # transform string to datetime type:
    hourly['time'] = pd.to_datetime(hourly['time'])
    
    return hourly

def get_local_time(local_timezone):
    format = "%Y-%m-%d %H:%M:%S"
    # Current time in UTC
    now_utc = datetime.now(timezone('UTC'))

    # Convert time zone
    local_time = now_utc.astimezone(timezone(local_timezone))
    
    return local_time.strftime(format)


#### Getting and processing the data ####

# Split timezone variable for url:
timezone1 = local_timezone.split('/')[0]
timezone2 = local_timezone.split('/')[1]

# Set url based on the selected location (coordinates and timezone):
url = f'https://api.open-meteo.com/v1/forecast?latitude={latitude}&longitude={longitude}&hourly=temperature_2m,relativehumidity_2m,dewpoint_2m,apparent_temperature,precipitation_probability,precipitation,rain,showers,snowfall,snow_depth,weathercode,cloudcover,cloudcover_low,cloudcover_mid,cloudcover_high,visibility,windspeed_10m,winddirection_10m,windgusts_10m,freezinglevel_height&daily=sunrise,sunset&forecast_days=3&timezone={timezone1}%2F{timezone2}'

# Run functions:
df = get_meteo_data(url)
hourly = process_hourly_data(df)
daily = process_daily_data(df)
local_time = get_local_time(local_timezone)





#### METEOGRAMS ####


### TEMPERATURE DATA

# Create fig and plot data
fig = go.Figure()

fig.add_trace(go.Scatter(x=hourly['time'], y=hourly['temperature_2m'], mode='lines', name='Temperature', line=dict(color='#ffa929')))
fig.add_trace(go.Scatter(x=hourly['time'], y=hourly['apparent_temperature'], mode='lines', name='Apparent Temperature', line=dict(color='#ed601f')))

fig.update_layout(
    xaxis_title='Time',
    yaxis_title='Temperature (°C)',
    showlegend=True,
    legend=dict(
        orientation="h",
        yanchor="top",
        y=1.15,
        xanchor="left",
        x=0
    ),
    hovermode="x unified",
    hoverlabel=dict(bgcolor="white", font_size=12),
    hoverdistance=100,
    margin=dict(
        b=0  # Set the bottom margin
    
    )
)

# Calculate daily min and max values and store the time they were measured
min_max_temps = []
min_max_times = []
for day in [[0,25],[25,49],[49,72]]:
    min=hourly['temperature_2m'][day[0]:day[1]].min()
    min_time = hourly['time'][hourly['temperature_2m'][day[0]:day[1]].idxmin()]
    max=hourly['temperature_2m'][day[0]:day[1]].max()
    max_time = hourly['time'][hourly['temperature_2m'][day[0]:day[1]].idxmax()]
    min_max_temps.append(min)
    min_max_temps.append(max)
    min_max_times.append(min_time)
    min_max_times.append(max_time)

# Define the annotation positions and texts
annotations = []
for temp, time in zip(min_max_temps, min_max_times):
    annotations.append(dict(x=time, y=temp, xref='x', yref='y', text=f"{temp}°C", showarrow=True, arrowhead=2, ax=0, ay=-30))

# Add annotations to the plot
for annotation in annotations:
    fig.add_annotation(annotation)
    
# Set y min and y max values based on the data
if hourly['temperature_2m'].min() < hourly['apparent_temperature'].min():
    y0=hourly['temperature_2m'].min()-3
else:
    y0=hourly['apparent_temperature'].min()-3

if hourly['temperature_2m'].max() > hourly['apparent_temperature'].max():
    y1=hourly['temperature_2m'].max()+4
else:
    y1=hourly['apparent_temperature'].max()+4

# Current local time for the selected location with a vertical line
fig.add_shape(type="line", x0=local_time, y0=y0, x1=local_time, y1=y1, line=dict(color="black", width=1, dash="dot"))

# Draw dashed vertical lines at midnight for each day as day separators
for date in hourly['time'].dt.date.unique():
    midnight = datetime.combine(date, datetime.min.time())
    fig.add_shape(type="line", x0=midnight, y0=y0, x1=midnight, y1=y1, line=dict(color="light grey", width=1, dash="dash"))
    
# Find the end time of the last day (previous loop not working for the third day...)
last_day_end = hourly[hourly['time'].dt.date == hourly['time'].dt.date.max()].iloc[-1]['time']+timedelta(hours=1)

# Add a vertical line to extend to the end of the last day
fig.add_shape(type="line", x0=last_day_end, y0=y0, x1=last_day_end, y1=y1, line=dict(color="light grey", width=1, dash="dash"))

# Draw color-filled areas for daytime intervals
for index, row in daily.iterrows():
    fig.add_vrect(
        x0=row['sunrise'],
        x1=row['sunset'],
        fillcolor="rgba(255, 239, 80, 0.4)",
        layer="below",
        line_width=0,
        annotation_text=datetime.strptime(row['time'], '%Y-%m-%d').strftime('%Y-%m-%d'),  # Convert string to datetime
        annotation_position="top left",  # Updated annotation position to top left
    )
    # Add annotations for sunrise and sunset labels on the x-axis
    fig.add_annotation(
        x=row['sunrise'],
        y=y0+1,
        text=f"Sunrise<br>{row['sunrise'].strftime('%H:%M')}",
        showarrow=False,
        font=dict(color="grey")
    )
    fig.add_annotation(
        x=row['sunset'],
        y=y0+1,
        text=f"Sunset<br>{row['sunset'].strftime('%H:%M')}",
        showarrow=False,
        font=dict(color="grey")
    )
    
# Define tick positions and labels for every three hours
tick_positions = hourly['time'][::3]
tick_labels = [time.strftime('%H') for time in tick_positions]

# Update x-axis tickvals and ticktext
fig.update_xaxes(
    tickvals=tick_positions,
    ticktext=tick_labels
)

# Show plot
st.plotly_chart(fig, theme="streamlit", use_container_width=True)





### WIND DATA

# Create fig and plot data
fig = go.Figure()

fig.add_trace(go.Scatter(x=hourly['time'], y=hourly['windgusts_10m'], mode='lines', name='Wind gust', line=dict(color='#0972B2')))
fig.add_trace(go.Scatter(x=hourly['time'], y=hourly['windspeed_10m'], mode='lines', name='Wind speed', line=dict(color='#4FD2FD')))

fig.update_layout(
    xaxis_title='Time',
    yaxis_title='Speed (km/h)',
    showlegend=True,
    legend=dict(
        orientation="h",
        yanchor="top",
        y=1.15,
        xanchor="left",
        x=0
    ),
    hovermode="x unified",
    hoverlabel=dict(bgcolor="white", font_size=12),
    hoverdistance=100,
    margin=dict(
        b=0,  # Set the bottom margin
        t=0   # Set the top margin
    )
)

# Current local time for the selected location with a vertical line
fig.add_shape(type="line", x0=local_time, y0=-6, x1=local_time, y1=hourly['windgusts_10m'].max()+5, line=dict(color="black", width=1, dash="dot"))

# Draw dashed vertical lines at midnight for each day
for date in hourly['time'].dt.date.unique():
    midnight = datetime.combine(date, datetime.min.time())
    fig.add_shape(type="line", x0=midnight, y0=-6, x1=midnight, y1=hourly['windgusts_10m'].max()+5, line=dict(color="grey", width=1, dash="dash"))
    
# Find the end time of the last day
last_day_end = hourly[hourly['time'].dt.date == hourly['time'].dt.date.max()].iloc[-1]['time']+timedelta(hours=1)

# Add a vertical line to extend to the end of the last day
fig.add_shape(type="line", x0=last_day_end, y0=-6, x1=last_day_end, y1=hourly['windgusts_10m'].max()+5, line=dict(color="grey", width=1, dash="dash"))

# Draw color-filled areas for daytime intervals
for index, row in daily.iterrows():
    fig.add_vrect(
        x0=row['sunrise'],
        x1=row['sunset'],
        fillcolor="rgba(255, 239, 80, 0.4)", 
        layer="below",
        line_width=0,
        annotation_text=datetime.strptime(row['time'], '%Y-%m-%d').strftime('%Y-%m-%d'),  # Convert string to datetime
        annotation_position="top left",  # Updated annotation position to top left
    )
    # Add annotations for sunrise and sunset labels on the x-axis
    fig.add_annotation(
        x=row['sunrise'],
        y=-3,
        text=f"Sunrise<br>{row['sunrise'].strftime('%H:%M')}",
        showarrow=False,
        font=dict(color="grey") 
    )
    fig.add_annotation(
        x=row['sunset'],
        y=-3,
        text=f"Sunset<br>{row['sunset'].strftime('%H:%M')}",
        showarrow=False,
        font=dict(color="grey") 
    )
    
# Define tick positions and labels for every three hours
tick_positions = hourly['time'][::3]
tick_labels = [time.strftime('%H') for time in tick_positions]

# Update x-axis tickvals and ticktext
fig.update_xaxes(
    tickvals=tick_positions,
    ticktext=tick_labels
)

# Show plot
st.plotly_chart(fig, theme="streamlit", use_container_width=True)





### PRECIPITATION DATA

# Create fig and plot data
fig = go.Figure(
    layout=dict(
        barcornerradius=15,
    )
)

fig.add_trace(go.Bar(x=hourly['time'], y=hourly['rain'], name='Rain', width=[10], marker=dict(color='#0C6CDF')))
fig.add_trace(go.Bar(x=hourly['time'], y=hourly['showers'], name='Showers', width=[10], marker=dict(color='#12ECF0')))
fig.add_trace(go.Bar(x=hourly['time'], y=hourly['snowfall'], name='Snowfall', width=[10], marker=dict(color='pink')))

fig.add_trace(go.Scatter(x=hourly['time'], y=hourly['precipitation_probability'], mode='lines', name='Precipitation probability', line=dict(color='darkblue'), yaxis='y2'))

# Update layout for secondary y-axis
fig.update_layout(
    yaxis2=dict(
        title='Precipitation probability (%)',
        overlaying='y',
        side='right',
        range=[0, 110],
        showgrid=False
    )
)

fig.update_layout(
    xaxis_title='Time',
    yaxis_title='Precipitation (mm)',
    showlegend=True,
    legend=dict(
        orientation="h",
        yanchor="top",
        y=1.15,
        xanchor="left",
        x=0
    ),
    hovermode="x unified",
    hoverlabel=dict(bgcolor="white", font_size=12),
    hoverdistance=100,
    margin=dict(
        b=20, 
        t=0
    )
)

# Set y max value based on the data
if hourly['rain'].max() > hourly['showers'].max():
    if hourly['rain'].max() > hourly['snowfall'].max():
        y1=hourly['rain'].max()+(hourly['rain'].max()*0.3)
    else:
        y1=hourly['snowfall'].max()+(hourly['snowfall'].max()*0.3)
elif hourly['showers'].max() > hourly['snowfall'].max():
    y1=hourly['showers'].max()+(hourly['showers'].max()*0.3)
else:
    y1=hourly['snowfall'].max()+(hourly['snowfall'].max()*0.3)

# Current local time for the selected location with a vertical line
fig.add_shape(type="line", x0=local_time, y0=0, x1=local_time, y1=y1, line=dict(color="black", width=1, dash="dot"))

# Draw dashed vertical lines at midnight for each day
for date in hourly['time'].dt.date.unique():
    midnight = datetime.combine(date, datetime.min.time())
    fig.add_shape(type="line", x0=midnight, y0=0, x1=midnight, y1=y1, line=dict(color="grey", width=1, dash="dash"))
    
# Find the end time of the last day
last_day_end = hourly[hourly['time'].dt.date == hourly['time'].dt.date.max()].iloc[-1]['time']+timedelta(hours=1)

# Add a vertical line to extend to the end of the last day
fig.add_shape(type="line", x0=last_day_end, y0=0, x1=last_day_end, y1=y1, line=dict(color="grey", width=1, dash="dash"))

# Draw color-filled areas for daytime intervals
for index, row in daily.iterrows():
    fig.add_vrect(
        x0=row['sunrise'],
        x1=row['sunset'],
        fillcolor="rgba(255, 239, 80, 0.4)",  # Light green color with transparency
        layer="below",
        line_width=0,
        annotation_text=datetime.strptime(row['time'], '%Y-%m-%d').strftime('%Y-%m-%d'),  # Convert string to datetime
        annotation_position="top left",  # Updated annotation position to top left
    )
    
# Define tick positions and labels for every three hours
tick_positions = hourly['time'][::3]
tick_labels = [time.strftime('%H') for time in tick_positions]

# Update x-axis tickvals and ticktext
fig.update_xaxes(
    tickvals=tick_positions,
    ticktext=tick_labels
)

# Show plot
st.plotly_chart(fig, theme="streamlit", use_container_width=True)
