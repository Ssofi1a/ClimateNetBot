import requests
from django.http import JsonResponse
from django.views import View
import telebot
from telebot import types
import threading
import time
import os
from dotenv import load_dotenv

load_dotenv()

TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
bot = telebot.TeleBot(TELEGRAM_BOT_TOKEN)

locations = {
    'Yerevan': ['V. Sargsyan', 'TUMO'],
    'Shirak': ['Maralik', 'Panik', 'Azatan', 'Artik', 'Ashotsk', 'Amasia', 'Hatsik', 'Akhuryan', 'Yerazgavors'],
    'Gegharkunik': ['Sevan', 'Gavar', 'Chambarak'],
    'Tavush': ['Berd', 'Artsvaberd', 'Ijevan', 'Azatamut', 'Koghb'],
    'Lori': ['Stepanavan', 'Spitak', 'Alaverdi', 'Odzun', 'Dsegh', 'Shnogh'],
    'Vayots Dzor': ['Areni', 'Vayk', 'Jermuk'],
    'USA': ['New York']
}

device_ids = {
    'Maralik': 1, 'Panik': 2, 'Azatan': 3, 'Artik': 4, 'Ashotsk': 5, 'Gavar': 6, 'Akhuryan': 7, 'V. Sargsyan': 8,
    'Sevan': 9, 'Hatsik': 10, 'Amasia': 11, 'Yerazgavors': 12, 'Artsvaberd': 13, 'TUMO': 14, 'Ijevan': 15, 'Berd': 16,
    'Chambarak': 17, 'Azatamut': 18, 'Spitak': 19, 'Stepanavan': 20, 'Vayk': 21, 'Areni': 22, 'Jermuk': 23, 'Alaverdi': 25,
    'New York': 26, 'Odzun': 27, 'Dsegh': 28, 'Shnogh': 29, 'Koghb': 30
}

user_context = {}

def fetch_latest_measurement(device_id):
    url = f"https://climatenet.am/device_inner/{device_id}/latest/"
    response = requests.get(url)

    if response.status_code == 200:
        data = response.json()
        if data:
            latest_measurement = data[0]  
            timestamp = latest_measurement["time"].replace("T", " ")
            return {
                "timestamp": timestamp,
                "uv": latest_measurement["uv"],
                "lux": latest_measurement["lux"],
                "temperature": latest_measurement["temperature"],
                "pressure": latest_measurement["pressure"],
                "humidity": latest_measurement["humidity"],
                "pm1": latest_measurement["pm1"],
                "pm2_5": latest_measurement["pm2_5"],
                "pm10": latest_measurement["pm10"],
                "wind_speed": latest_measurement["speed"],
                "rain": latest_measurement["rain"],
                "wind_direction": latest_measurement["direction"]
            }
        else:
            return None
    else:
        print(f"Failed to fetch data: {response.status_code}")
        return None

def start_bot():
    bot.polling(none_stop=True)

def run_bot():
    while True:
        try:
            start_bot()
        except Exception as e:
            print(f"Error occurred: {e}")
            time.sleep(15)

def start_bot_thread():
    bot_thread = threading.Thread(target=run_bot)
    bot_thread.start()

def send_location_selection(chat_id):
    location_markup = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
    for country in locations.keys():
        location_markup.add(types.KeyboardButton(country))
    
    bot.send_message(chat_id, 'Please choose a location: 📍', reply_markup=location_markup)

@bot.message_handler(commands=['start'])
def start(message):
    bot.send_message(
        message.chat.id,
        '🌤️ Welcome to ClimateNet! 🌧️'
    )
    bot.send_message(
        message.chat.id,
        f'''Hello {message.from_user.first_name}! 👋​ I am your personal climate assistant. 
        
With me, you can: 
    🔹​​​ Access current measurements of temperature, humidity, wind speed, and more, refreshed every 15 minutes for reliable updates.
    🔹​​​​ Receive alerts for significant climate changes.
    🔹​​​​ Get personalized recommendations based on current conditions in your area.
'''
    )
    send_location_selection(message.chat.id)

@bot.message_handler(func=lambda message: message.text in locations.keys())
def handle_country_selection(message):
    selected_country = message.text
    chat_id = message.chat.id
    user_context[chat_id] = {'selected_country': selected_country}
    markup = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
    for device in locations[selected_country]:
        markup.add(types.KeyboardButton(device))

    bot.send_message(chat_id, 'Please choose a device: ✔️', reply_markup=markup)

@bot.message_handler(func=lambda message: message.text in [device for devices in locations.values() for device in devices])
def handle_device_selection(message):
    selected_device = message.text
    chat_id = message.chat.id
    device_id = device_ids.get(selected_device)
    
    if chat_id in user_context:
        user_context[chat_id]['selected_device'] = selected_device
        user_context[chat_id]['device_id'] = device_id

    if device_id:
        command_markup = get_command_menu()
        measurement = fetch_latest_measurement(device_id)
        if measurement:
            formatted_data = (
                f"Latest Measurement ({measurement['timestamp']}):\n"
                f"☀️ UV Index: {measurement['uv']}\n"
                f"🔆​ Light Intensity: {measurement['lux']} lux\n"
                f"🌡️ Temperature: {measurement['temperature']}°C\n"
                f"⏲️ Pressure: {measurement['pressure']} hPa\n"
                f"💧 Humidity: {measurement['humidity']}%\n"
                f"💨​​ PM1: {measurement['pm1']} µg/m³\n"
                f"🫁​​ PM2.5: {measurement['pm2_5']} µg/m³\n"
                f"🌫️​ PM10: {measurement['pm10']} µg/m³\n"
                f"🌪️ Wind Speed: {measurement['wind_speed']} m/s\n"
                f"🌧️ Rainfall: {measurement['rain']} mm\n"
                f"🧭​ Wind Direction: {measurement['wind_direction']}"
            )
            
            bot.send_message(chat_id, formatted_data, reply_markup=command_markup)
        else:
            bot.send_message(chat_id, "⚠️ Error retrieving data. Please try again later.", reply_markup=command_markup)
    else:
        bot.send_message(chat_id, 'Device not found. ❌​')


def get_command_menu():
    command_markup = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
    command_markup.add(
        types.KeyboardButton('/Current 📍'),
        types.KeyboardButton('/Change_device 🔄'),
        types.KeyboardButton('/Help ❓'),
        types.KeyboardButton('/Website 🌐'),
    )
    return command_markup

@bot.message_handler(commands=['Current'])
def get_current_data(message):
    chat_id = message.chat.id
    command_markup = get_command_menu()
    
    if chat_id in user_context and 'device_id' in user_context[chat_id]:
        device_id = user_context[chat_id]['device_id']
        
        measurement = fetch_latest_measurement(device_id)
        
        if measurement:
            formatted_data = (
                f"Latest Measurement ({measurement['timestamp']}):\n"
                f"☀️ UV Index: {measurement['uv']}\n"
                f"🔆​ Light Intensity: {measurement['lux']} lux\n"
                f"🌡️ Temperature: {measurement['temperature']}°C\n"
                f"⏲️ Pressure: {measurement['pressure']} hPa\n"
                f"💧 Humidity: {measurement['humidity']}%\n"
                f"💨​​ PM1: {measurement['pm1']} µg/m³\n"
                f"🫁​​ PM2.5: {measurement['pm2_5']} µg/m³\n"
                f"🌫️​ PM10: {measurement['pm10']} µg/m³\n"
                f"🌪️ Wind Speed: {measurement['wind_speed']} m/s\n"
                f"🌧️ Rainfall: {measurement['rain']} mm\n"
                f"🧭​ Wind Direction: {measurement['wind_direction']}"
            )
            bot.send_message(chat_id, formatted_data, reply_markup=command_markup)
        else:
            bot.send_message(chat_id, "⚠️ Error retrieving data. Please try again later.", reply_markup=command_markup)
    else:
        bot.send_message(chat_id, "⚠️ Please select a device first using /Change_device.", reply_markup=command_markup)

@bot.message_handler(commands=['Help'])
def help(message):
    bot.send_message(message.chat.id, '''
<b>/Help:</b> Show available commands.\n
<b>/Current:</b> Get the latest climate data.\n
<b>/Change_device:</b> Change to a different climate monitoring device.\n
<b>/Website:</b> Visit our website for more info.
''', parse_mode='HTML')

@bot.message_handler(commands=['Change_device'])
def change_device(message):
    chat_id = message.chat.id

    if chat_id in user_context:
        user_context[chat_id].pop('selected_device', None)
        user_context[chat_id].pop('device_id', None)
    send_location_selection(chat_id)

@bot.message_handler(commands=['Website'])
def website(message):
    markup = types.InlineKeyboardMarkup()
    button = types.InlineKeyboardButton('Visit Website', url='https://climatenet.am/en/')
    markup.add(button)

    bot.send_message(
        message.chat.id,
        'For more information, click the button below to visit our official website: 모​',
        reply_markup=markup
    )

@bot.message_handler(content_types=['audio', 'document', 'photo', 'sticker', 'video', 'video_note', 'voice', 'contact', 'location', 'venue', 'animation'])
def handle_media(message):
    bot.send_message(
        message.chat.id,
        '''⚠️ I can only process text commands.
Please use valid commands.
''', parse_mode='HTML')

def run_bot_view(request):
    start_bot_thread()
    return JsonResponse({'status': 'Bot is running in the background!'})