from flask import Flask, render_template, request, redirect, url_for, flash
import requests
from datetime import datetime, timedelta
from statsmodels.tsa.arima.model import ARIMA
import numpy as np

app = Flask(__name__)
app.secret_key = 'c85c6d9cbea24f13a1143839242905'

API_KEY = 'c85c6d9cbea24f13a1143839242905'
CURRENT_URL = 'http://api.weatherapi.com/v1/current.json'
HISTORY_URL = 'http://api.weatherapi.com/v1/history.json'

favorites = []

def get_weather_data(city):
    try:
        params = {
            'key': API_KEY,
            'q': city
        }
        response = requests.get(CURRENT_URL, params=params)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(e)
        return None

def get_historical_data(city):
    try:
        historical_data = []
        for i in range(7):
            date = (datetime.now() - timedelta(days=i)).strftime('%Y-%m-%d')
            params = {
                'key': API_KEY,
                'q': city,
                'dt': date
            }
            response = requests.get(HISTORY_URL, params=params)
            response.raise_for_status()
            historical_data.append(response.json())
        return historical_data
    except requests.exceptions.RequestException as e:
        print(e)
        return None

def train_arima_model(data):
    model = ARIMA(data, order=(5, 1, 0))
    model_fit = model.fit()
    return model_fit

def predict_next_days(model_fit, steps=3):
    forecast = model_fit.forecast(steps=steps)
    return forecast.tolist()

def prepare_data(historical_data):
    temperature_data = []
    for day in historical_data:
        temperature_data.append(day['forecast']['forecastday'][0]['day']['avgtemp_c'])
    return temperature_data

@app.route('/')
def index():
    weather_data = None
    historical_data = None
    forecast_data = None
    city = request.args.get('city')
    if city:
        weather_data = get_weather_data(city)
        if not weather_data:
            flash('Could not retrieve current weather data. Please try again.')
        historical_data = get_historical_data(city)
        if not historical_data:
            flash('Could not retrieve historical weather data. Please try again.')
        
        data = prepare_data(historical_data)
        model_fit = train_arima_model(data)
        forecast_data = predict_next_days(model_fit, steps=3)
    
    return render_template('index.html', weather_data=weather_data, historical_data=historical_data, forecast_data=forecast_data, favorites=favorites)


@app.route('/add_favorite', methods=['POST'])
def add_favorite():
    city = request.form.get('city')
    if city and city not in favorites:
        favorites.append(city)
    return redirect(url_for('index'))

@app.route('/remove_favorite/<city>')
def remove_favorite(city):
    if city in favorites:
        favorites.remove(city)
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)
