import altair as alt
import streamlit as st
import requests
import pandas as pd
import numpy as np
import json
import matplotlib.pyplot as plt
from datetime import timedelta, datetime
from matplotlib.ticker import StrMethodFormatter


"""
# Weather Dashboard
Data from [Open-Meteo Weather API](https://open-meteo.com/)
"""

current_date = str(pd.to_datetime(datetime.today().date()))[:10]
st.write(current_date)

st.divider()

url = 'https://api.open-meteo.com/v1/forecast?latitude=47.60&longitude=19.36&hourly=temperature_2m,relativehumidity_2m,dewpoint_2m,apparent_temperature,precipitation_probability,precipitation,rain,showers,snowfall,snow_depth,weathercode,cloudcover,cloudcover_low,cloudcover_mid,cloudcover_high,visibility,windspeed_10m,winddirection_10m,windgusts_10m,freezinglevel_height&daily=sunrise,sunset&forecast_days=3&timezone=Europe%2FBerlin'

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

#### Getting and processing the data ####
df = get_meteo_data(url)
hourly = process_hourly_data(df)
daily = process_daily_data(df)

#### sidebar ####

# location map:
location = [{'latitude':47.60, 'longitude':19.36}]
with st.sidebar:
    st.map(location)


#### main area ####

def plot_temp_data(hourly, daily):
    # create figure object and set canvas size:
    fig, ax = plt.subplots(1,1,figsize=(15,3))

    ### plot temperature data:
    ax.plot(hourly['time'], hourly['temperature_2m'], color='#F78221', label = 'Temperature', zorder=3)

    # set axis labels:
    ax.set_xlabel('Time')
    ax.set_ylabel('Temperature (°C)')
    # set ylim and add more space above and below the plotted data (10% of the ylim max value):
    y_min = ax.get_ylim()[0]-(ax.get_ylim()[1]*0.10)
    y_max = ax.get_ylim()[1]+(ax.get_ylim()[1]*0.10)
    ax.set_ylim(y_min,y_max)

    ### Second y-axis on the right, copy of left side:
    ax2 = ax.twinx()
    ax2.set_ylim(ax.get_ylim())
    ax2.set_ylabel('Temperature (°C)')

    # Format y-axis to show 0 decimals
    ax.yaxis.set_major_formatter(StrMethodFormatter('{x:.0f}'))
    ax2.yaxis.set_major_formatter(StrMethodFormatter('{x:.0f}'))

    ### calculate daily min and max values and store the time they measured:
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

    # write min and max temps on the plot:
    for i in range(6):
        ax.text(x=min_max_times[i], y=min_max_temps[i], s=min_max_temps[i], color='black', alpha=0.7, ha='center', va='top', fontsize=12)

    ### create and plot small x axis ticks for every hour and bigger x axis ticks for every 6 hours with labels:
    # set start and end time points for generating tick positions (based on 'time' variable):
    start = hourly['time'].iloc[0]
    # here + 1 hour (last time point is 23:00 for every day, but we need 24:00):
    end = hourly['time'].iloc[-1] + timedelta(hours=1)

    # create x tick positions as a datetime object:
    hourly_ticks = pd.date_range(start=start, end=end, freq='h', normalize=True)
    six_hour_ticks = pd.date_range(start=start, end=end, freq='3h', normalize=True)

    # create labels for every 6 hours:
    xtick_labels = [x.strftime('%H') if x in hourly_ticks else '' for x in six_hour_ticks]

    # plot x ticks and labels:
    ax.set_xticks(hourly_ticks, minor=True)
    ax.set_xticks(six_hour_ticks)
    ax.set_xticklabels(xtick_labels, fontsize=10)

    ### vertical lines between days based on the 'time' variable (start and end are set above):
    # generate vertical line positions as a datetime object:
    daybreak_lines = pd.date_range(start=start, end=end, freq='D', normalize=True)

    # plot vertical lines:
    for date in daybreak_lines:
        plt.axvline(x=date, color='grey', linestyle='--', zorder=2)

    ### color filled area indicating the time between sunrise and sunset: 
    for i in range(3):
        ax.axvspan(daily['sunrise'][i],daily['sunset'][i],color='#FFEF50',alpha=0.5, label='Daylight', zorder=1)

    ### horizontal grid lines:
    ax.grid(axis='y',alpha=0.3,linestyle='--')

    ### date and day sign above the plot:
    # create list with signs for the days to show above the plot:
    day_sign = []
    weekday_log = []
    weekdays = ['Monday','Tuesday','Wednesday','Thursday','Friday','Saturday','Sunday']
    for i in [0,24,48]:
        year = hourly['time'].dt.year[i]
        month = hourly['time'].dt.month[i]
        day = hourly['time'].dt.day[i]
        weekday = weekdays[hourly['time'][i].weekday()]
        day_sign.append(str(weekday)+' - '+str(year)+'.'+str(month)+'.'+str(day))
        weekday_log.append(weekday)
        
    # create a list with day sign colors - orange for weekend, black for weekdays:
    weekday_color = []
    for weekday in weekday_log:
        if str(weekday) in ['Saturday','Sunday']:
            weekday_color.append('#F78221')
        else:
            weekday_color.append('black')

    # define x positions for signs based on sunrise-sunset:
    sign_x_pos=[]
    for i in range(3):
        diff = (daily['sunset'][i]-daily['sunrise'][i])/2
        pos = daily['sunrise'][i] + diff
        sign_x_pos.append(pos)

    # define y position for signs based on the actual ymax of the plot:
    sign_y_pos=ax.get_ylim()[1]+(ax.get_ylim()[1])*0.05

    # plot day and date sign with colors above the graph:
    for i in range(3):
        ax.text(x=sign_x_pos[i], y=sign_y_pos, s=day_sign[i], color=weekday_color[i], ha='center', va='center')

    ### legend box position:
    fig.legend(['Temperature', 'Daylight'], bbox_to_anchor =(1.04,0.08), loc='lower right')

    st.pyplot(fig)

# Plot the temp data:
plot_temp_data(hourly, daily)

# Plot with streamlit:


st.divider()
















#### code from streamlit example

num_points = st.slider("Number of points in spiral", 1, 10000, 1100)
num_turns = st.slider("Number of turns in spiral", 1, 300, 31)

indices = np.linspace(0, 1, num_points)
theta = 2 * np.pi * num_turns * indices
radius = indices

x = radius * np.cos(theta)
y = radius * np.sin(theta)

df = pd.DataFrame({
    "x": x,
    "y": y,
    "idx": indices,
    "rand": np.random.randn(num_points),
})

st.altair_chart(alt.Chart(df, height=700, width=700)
    .mark_point(filled=True)
    .encode(
        x=alt.X("x", axis=None),
        y=alt.Y("y", axis=None),
        color=alt.Color("idx", legend=None, scale=alt.Scale()),
        size=alt.Size("rand", legend=None, scale=alt.Scale(range=[1, 150])),
    ))
