from django.http import JsonResponse
import telebot
from telebot import types
import threading
import time
import os
from dotenv import load_dotenv # type: ignore

# Load environment variables from the .env file
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

def start_bot():
    bot.polling(none_stop=True)

# This function runs the bot in a separate thread
def run_bot():
    while True:
        try:
            start_bot()
        except Exception as e:
            print(f"Error occurred: {e}")
            time.sleep(15)  # wait before retrying

# Function to start the bot in a thread
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
    flag = '🇺🇲' if selected_country == 'USA' else '🇦🇲'
    bot.send_message(call.message.chat.id, f'You selected: {selected_country} {flag}')
    
    markup = types.InlineKeyboardMarkup()
    for device in locations[selected_country]:
        markup.add(types.InlineKeyboardButton(device, callback_data=device))

    bot.send_message(call.message.chat.id, 'Choose a device:', reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data in [device for devices in locations.values() for device in devices])
def handle_device_selection(call):
    selected_device = call.data
    bot.send_message(call.message.chat.id, f'You selected: {selected_device}📍​')
    bot.send_message(call.message.chat.id, 'ⓘ Type /help - I’ll tell you all about my available commands and how to use them.')

@bot.message_handler(commands=['help'])
def help(message):
    bot.send_message(message.chat.id, '''<b>/start:</b> Welcome message explaining the bot’s purpose.\n
<b>/help:</b> Describe how to use the bot.\n
<b>/current:</b> Get the latest data readings like temperature, humidity, wind speed, etc.\n
<b>/history [parameter] [period]:</b> Show historical data for a given parameter (e.g., /history temperature 24h).\n
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

@bot.message_handler(content_types=['audio', 'document', 'photo', 'sticker', 'video', 'video_note', 'voice', 'contact', 'location', 'venue', 'animation'])
def handle_media(message):
    bot.send_message(
        message.chat.id,
        '''⚠️ I can only process text commands.
Please use <u>valid</u> commands.
ⓘ Type <b>/help</b> to see available commands.''', parse_mode='HTML')

# This is a view to trigger the bot
def run_bot_view(request):
    start_bot_thread()
    return JsonResponse({'status': 'Bot is running in the background!'})
