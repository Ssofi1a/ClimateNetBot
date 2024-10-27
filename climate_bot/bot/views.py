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
    'Tavush': ['Berd', 'Artsvaberd', 'Ijevan', 'Azatamut'],
    'Lori': ['Stepanavan', 'Spitak'],
    'Vayots Dzor': ['Areni', 'Vayk', 'Jermuk'],
    'USA': ['New York']
}

device_ids = {
    'Maralik': 1, 'Panik': 2, 'Azatan': 3, 'Artik': 4, 'Ashotsk': 5, 'Gavar': 6, 'Akhuryan': 7, 'V. Sargsyan': 8,
    'Sevan': 9, 'Hatsik': 10, 'Amasia': 11, 'Yerazgavors': 12, 'Artsvaberd': 13, 'TUMO': 14, 'Ijevan': 15, 'Berd': 16,
    'Chambarak': 17, 'Azatamut': 18, 'Spitak': 19, 'Stepanavan': 20, 'Vayk': 21, 'Areni': 22, 'Jermuk': 23, 'New York': 26,
    'Odzun': 27, 'Dsegh': 28, 'Shnogh': 29
}

user_context = {}

def fetch_latest_measurement(device_id):
    url = f"https://emvnh9buoh.execute-api.us-east-1.amazonaws.com/getData?device_id={device_id}"
    response = requests.get(url)

    if response.status_code == 200:
        data = response.json()
        latest_measurement = data['data'][-1]
        return {
            "timestamp": latest_measurement[1],
            "uv": latest_measurement[2],
            "lux": latest_measurement[3],
            "temperature": latest_measurement[4],
            "pressure": latest_measurement[5],
            "humidity": latest_measurement[6],
            "pm1": latest_measurement[7],
            "pm2_5": latest_measurement[8],
            "pm10": latest_measurement[9],
            "wind_speed": latest_measurement[10],
            "rain": latest_measurement[11],
            "wind_direction": latest_measurement[12]
        }
    else:
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

@bot.message_handler(commands=['start'])
def start(message):
    bot.send_message(message.chat.id, '🌤️ Welcome to ClimateNet! 🌧️')
    bot.send_message(message.chat.id, f'''Hello {message.from_user.first_name}! 👋​ I am your personal climate assistant, designed to keep you informed about real-time climate and environmental conditions. 
    
With me, you can: 
    ◽​​​ Get live updates on temperature, humidity, wind speed, and more.
    ◽​​​ Receive alerts for significant climate changes and potential hazards.
    ◽​​​ Enjoy personalized recommendations based on current conditions in your area. 
    
Feel free to ask me anything about the climate or how I can assist you today!''')
    
    markup = types.InlineKeyboardMarkup()
    for country in locations.keys():
        markup.add(types.InlineKeyboardButton(country, callback_data=country))
    
    bot.send_message(message.chat.id, 'Please choose a location:', reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data in locations.keys())
def handle_country_selection(call):
    selected_country = call.data
    chat_id = call.message.chat.id
    
    user_context[chat_id] = {'selected_country': selected_country}
    
    flag = '🇺🇲' if selected_country == 'USA' else '🇦🇲'
    bot.send_message(chat_id, f'You selected: {selected_country} {flag}')
    
    markup = types.InlineKeyboardMarkup()
    for device in locations[selected_country]:
        markup.add(types.InlineKeyboardButton(device, callback_data=device))

    bot.send_message(chat_id, 'Choose a device:', reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data in [device for devices in locations.values() for device in devices])
def handle_device_selection(call):
    selected_device = call.data
    chat_id = call.message.chat.id
    device_id = device_ids.get(selected_device)
    
    if chat_id in user_context:
        user_context[chat_id]['selected_device'] = selected_device
        user_context[chat_id]['device_id'] = device_id

    if device_id:
        bot.send_message(chat_id, f'You selected: {selected_device}📍​ (Device ID: {device_id})')
        bot.send_message(chat_id, 'ⓘ Type /current to get the latest data or /help for more commands.')
    else:
        bot.send_message(chat_id, 'Device not found.')

@bot.message_handler(commands=['current'])
def get_current_data(message):
    chat_id = message.chat.id
    
    if chat_id in user_context and 'device_id' in user_context[chat_id]:
        device_id = user_context[chat_id]['device_id']
        
        measurement = fetch_latest_measurement(device_id)
        
        if measurement:
            formatted_data = (
                f"Latest Measurement ({measurement['timestamp']}):\n"
                f"☀️ UV Index: {measurement['uv']}\n"
                f"🌟​ Light Intensity: {measurement['lux']} lux\n"
                f"🌡️ Temperature: {measurement['temperature']}°C\n"
                f"⏲️ Pressure: {measurement['pressure']} hPa\n"
                f"💧 Humidity: {measurement['humidity']}%\n"
                f"🌫️​ PM1: {measurement['pm1']} µg/m³\n"
                f"🌫️​ PM2.5: {measurement['pm2_5']} µg/m³\n"
                f"🌫️​ PM10: {measurement['pm10']} µg/m³\n"
                f"💨 Wind Speed: {measurement['wind_speed']} m/s\n"
                f"🌧️ Rainfall: {measurement['rain']} mm\n"
                f"🌪️ Wind Direction: {measurement['wind_direction']}"
            )
            bot.send_message(chat_id, formatted_data)
        else:
            bot.send_message(chat_id, "Error retrieving data. Please try again later.")
    else:
        bot.send_message(chat_id, "⚠️ Please select a device first using /start.")

@bot.message_handler(content_types=['audio', 'document', 'photo', 'sticker', 'video', 'video_note', 'voice', 'contact', 'location', 'venue', 'animation'])
def handle_media(message):
    bot.send_message(
        message.chat.id,
        '''⚠️ I can only process text commands.
Please use <u>valid</u> commands.
ⓘ Type <b>/help</b> to see available commands.''', parse_mode='HTML')

@bot.message_handler(commands=['help'])
def help(message):
    bot.send_message(message.chat.id, '''<b>/start:</b> Welcome message explaining the bot’s purpose.\n
<b>/help:</b> Describe how to use the bot.\n
<b>/current:</b> Get the latest data readings like temperature, humidity, wind speed, etc.\n
<b>/setalert:</b> Allow users to set thresholds for alerts (e.g., “alert me when temperature > 35°C”).\n
<b>/removealert:</b> Remove previously set alerts.\n
<b>/website:</b> Provides a link to the project's official website or a source for more detailed information.
''', parse_mode='HTML')

@bot.message_handler(commands=['website'])
def website(message):
    markup = types.InlineKeyboardMarkup()
    button = types.InlineKeyboardButton('Visit Website', url='https://climatenet.am/en/')
    markup.add(button)

    bot.send_message(
        message.chat.id,
        'For more information, click the button below to visit our official website: 🌐​',
        reply_markup=markup
    )

def run_bot_view(request):
    start_bot_thread()
    return JsonResponse({'status': 'Bot is running in the background!'})
