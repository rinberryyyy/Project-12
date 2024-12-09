import os
import requests
from flask import Flask, render_template, request
from dotenv import load_dotenv

load_dotenv()

ACCUWEATHER_API_KEY = os.getenv("ACCUWEATHER_API_KEY")

app = Flask(__name__)

def coords_key_of_location(latitude, longitude):
    location_url = f"http://dataservice.accuweather.com/locations/v1/cities/geoposition/search?apikey={ACCUWEATHER_API_KEY}&q={latitude}%2C{longitude}&details=true"
    response = requests.get(location_url)
    data = response.json()
    if data:
        return data["Key"]
    else:
        return None

def city_key_of_location(name_of_city):
    location_url = f"http://dataservice.accuweather.com/locations/v1/cities/search?apikey={ACCUWEATHER_API_KEY}&q={name_of_city}&language=ru"
    response = requests.get(location_url)
    data = response.json()
    if data:
        return data[0]["Key"]
    else:
        return None

def get_weather(key_of_location):
    weather_url = f"http://dataservice.accuweather.com/currentconditions/v1/{key_of_location}?apikey={ACCUWEATHER_API_KEY}&language=ru&details=true"
    response = requests.get(weather_url)
    data = response.json()
    if data:
        return data[0]
    else:
        return None

def get_forecast(key_of_location):
    forecast_url = f"http://dataservice.accuweather.com/forecasts/v1/daily/1day/{key_of_location}?apikey={ACCUWEATHER_API_KEY}&language=ru&details=true"
    response = requests.get(forecast_url)
    data = response.json()
    if data:
        return data
    else:
        return None

def control_of_bad_weather(temperature, speed_of_wind, probability_of_precipitation):
    warnings = []
    if temperature < 0:
        warnings.append("Низкая температура")
    if temperature > 35:
        warnings.append("Слишком высокая температура")
    if speed_of_wind > 50:
        warnings.append("Сильный ветер")
    if probability_of_precipitation > 70:
        warnings.append("Высокая вероятность осадков")
    if warnings:
        return "Неблагоприятные погодные условия: " + " ".join(warnings)
    else:
        return "Благоприятные погодные условия"

@app.route("/", methods=["GET", "POST"])
def main():
    result = None
    department = ""
    arrival = ""
    department_weather_info = None
    arrival_weather_info = None

    if request.method == "POST":
        department = request.form.get("start_city")
        arrival = request.form.get("end_city")
        if not department or not arrival:
            result = "Введите названия города отправдения и прибытия."
        else:
            try:
                start_key_of_location = city_key_of_location(department)
                end_key_of_location = city_key_of_location(arrival)
                if not start_key_of_location:
                    result = f"Город не найден: {department}"
                    return render_template("index.html", result=result)
                if not end_key_of_location:
                    result = f"Город не найден: {arrival}"
                    return render_template("index.html", result=result)
                start_current_weather = get_weather(start_key_of_location)
                end_current_weather = get_weather(end_key_of_location)
                if not start_current_weather:
                    result = f"Не удалось получить данные о погоде города {department}."
                    return render_template("index.html", result=result)
                if not end_current_weather:
                    result = f"Не удалось получить данные о погоде города {arrival}."
                    return render_template("index.html", result=result)
                start_forecast = get_forecast(start_key_of_location)
                end_forecast = get_forecast(end_key_of_location)
                if not start_forecast:
                    result = f"Не удалось получить прогноз погоды города {department}."
                    return render_template("index.html", result=result)
                if not end_forecast:
                    result = f"Не удалось получить прогноз погоды города {arrival}."
                    return render_template("index.html", result=result)

                department_weather_info = {
                    "city": department,
                    "current_temperature": start_current_weather["Temperature"]["Metric"]["Value"],
                    "weather_text": start_current_weather["WeatherText"],
                    "wind_speed": start_current_weather["Wind"]["Speed"]["Metric"]["Value"],
                    "humidity": start_current_weather["RelativeHumidity"],
                    "pressure": start_current_weather["Pressure"]["Metric"]["Value"],
                    "min_temp": start_forecast["DailyForecasts"][0]["Temperature"]["Minimum"]["Value"],
                    "max_temp": start_forecast["DailyForecasts"][0]["Temperature"]["Maximum"]["Value"],
                    "precipitation_probability": start_forecast["DailyForecasts"][0]["Day"]["PrecipitationProbability"],
                }

                arrival_weather_info = {
                    "city": arrival,
                    "current_temperature": end_current_weather["Temperature"]["Metric"]["Value"],
                    "weather_text": end_current_weather["WeatherText"],
                    "wind_speed": end_current_weather["Wind"]["Speed"]["Metric"]["Value"],
                    "humidity": end_current_weather["RelativeHumidity"],
                    "pressure": end_current_weather["Pressure"]["Metric"]["Value"],
                    "min_temp": end_forecast["DailyForecasts"][0]["Temperature"]["Minimum"]["Value"],
                    "max_temp": end_forecast["DailyForecasts"][0]["Temperature"]["Maximum"]["Value"],
                    "precipitation_probability": end_forecast["DailyForecasts"][0]["Day"]["PrecipitationProbability"],
                }

                start_bad_weather = control_of_bad_weather(
                    department_weather_info["current_temperature"],
                    department_weather_info["wind_speed"],
                    department_weather_info["precipitation_probability"],
                )

                end_bad_weather = control_of_bad_weather(
                    arrival_weather_info["current_temperature"],
                    arrival_weather_info["wind_speed"],
                    arrival_weather_info["precipitation_probability"],
                )

                result = {
                    "start_weather_info": department_weather_info,
                    "end_weather_info": arrival_weather_info,
                    "start_bad_weather": start_bad_weather,
                    "end_bad_weather": end_bad_weather,
                }

            except requests.exceptions.RequestException:
                result = "Ошибка подключения к сервису погоды"
            except Exception as e:
                result = f"Произошла ошибка: {str(e)}"

    return render_template(
        "index.html", result=result, start_city=department, end_city=arrival
    )

if __name__ == "__main__":
    app.run(debug=True)
