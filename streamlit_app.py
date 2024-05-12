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

# Getting and processing the data:
df = get_meteo_data(url)
hourly = process_hourly_data(df)
daily = process_daily_data(df)

# 

st.divider()

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
