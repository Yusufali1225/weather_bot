import requests
from config import WEATHER_API_KEY

def get_current_weather(city, lang='en'):
    url = "http://api.openweathermap.org/data/2.5/weather"
    params = {
        'q': city,
        'appid': WEATHER_API_KEY,
        'units': 'metric',
        'lang': lang
    }
    r = requests.get(url, params=params, timeout=8)
    data = r.json()
    return data
