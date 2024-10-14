import os
import requests_cache
import openmeteo_requests
import asyncio

from dotenv import load_dotenv
from retry_requests import retry
from geopy.geocoders import Nominatim
from functools import partial
from aiogram import Bot, Dispatcher, types
from aiogram.filters.command import Command


load_dotenv()
bot = Bot(token=os.getenv('BOT_TOKEN_ID'))
dp = Dispatcher()

url = 'https://api.open-meteo.com/v1/forecast'
geolocator = Nominatim(user_agent=os.getenv('GEOLOCATOR'))
geocode = partial(
    geolocator.geocode,
    language=os.getenv('GEOLOCATOR_LANGUAGE'),
)
cache_session = requests_cache.CachedSession(
    os.getenv('NAME_CACHE_FILENAME'),
    expire_after=os.getenv('CACHE_EXPIRED_TIME'),
)
retry_session = retry(
    cache_session,
    retries=os.getenv('RETRY_SESSIONS_RETRIES'),
    backoff_factor=os.getenv('RETRY_SESSIONS_BACKOFF'),
)
openmeteo = openmeteo_requests.Client(session=retry_session)


def check_location(city: str):
    return geolocator.geocode(city)


def get_weather(location) -> str:
    params: dict[str, str] = {
        'latitude': location.latitude,
        'longitude': location.longitude,
        'current': [
            'temperature_2m',
            'relative_humidity_2m',
            'apparent_temperature',
            'precipitation',
            'rain',
            'showers',
            'snowfall',
            'cloud_cover',
            'surface_pressure',
            'wind_speed_10m',
        ],
        'hourly': 'temperature_2m',
    }
    responses = openmeteo.weather_api(url, params=params)
    response = responses[0]
    current = response.Current()
    current_temperature_2m = current.Variables(0).Value()
    current_relative_humidity_2m = current.Variables(1).Value()
    current_apparent_temperature = current.Variables(2).Value()
    current_precipitation = current.Variables(3).Value()
    current_rain = current.Variables(4).Value()
    current_showers = current.Variables(5).Value()
    current_snowfall = current.Variables(6).Value()
    current_cloud_cover = current.Variables(7).Value()
    current_surface_pressure = (current.Variables(8).Value()*float(
        os.getenv('PRESSURE_TRANSFER_COEFFICIENT')))
    current_wind_speed_10m = current.Variables(9).Value()
    return (
        f'Температора: {current_temperature_2m} C \n'
        f'Ощущается как: {current_apparent_temperature} C \n'
        f'Влажность воздуха: {current_relative_humidity_2m}%\n'
        f'Осадки: {current_precipitation} мм\n'
        f'Дождь: {current_rain} мм\n'
        f'Ливень: {current_showers} мм\n'
        f'Снег: {current_snowfall} мм\n'
        f'Облачность: {current_cloud_cover}%\n'
        f'Давление: {current_surface_pressure} мм.рт.ст.\n'
        f'Скорость ветра: {current_wind_speed_10m} км/ч'
    )


@dp.message(Command('start'))
async def cmd_start(message: types.Message):
    await message.answer(os.getenv('START_MESSAGE'))


@dp.message()
async def answer(message: types.Message):
    location = check_location(message.text)
    if location:
        await message.answer(
            f'Город: {message.text} \n'
            f'{location}\n'
            f'{get_weather(location)}'
        )
    else:
        await message.answer(os.getenv('Не смог найти город'))


async def main():
    await dp.start_polling(bot)


if __name__ == '__main__':
    asyncio.run(main())
