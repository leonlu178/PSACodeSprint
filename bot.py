import os
import telebot
import openai
from telebot import types
from dotenv import load_dotenv
from datetime import datetime

load_dotenv()

BOT_TOKEN = os.getenv('BOT_TOKEN')
bot = telebot.TeleBot(BOT_TOKEN)
API_KEY = os.getenv('API_KEY')
PROMPT = os.getenv('PROMPT')

openai.api_key = API_KEY  #public key changes from time to time DakuWorks #api-and-update
openai.api_base = "https://api.daku.tech/v1"

HR_INFO, APPLY_LEAVE, CHECK_PAYROLL, CONTACT_HR, TRACK_STATUS, CHAT_AI= range(6)

user_data = {}

hr_documents = {
    "passes_permits": 'https://www.singaporepsa.com/resources/port-users/passes-and-permits/',
    "guidelines": 'https://www.singaporepsa.com/resources/port-users/guidelines/',
    "bus_guides": 'https://www.singaporepsa.com/resources/port-users/terminal-bus-guide/',
    "tender_notices": 'https://www.singaporepsa.com/resources/tender-notices/',
    "students": 'https://www.singaporepsa.com/careers/for-students-graduates/',
    "graduates": 'https://www.singaporepsa.com/careers/for-students-graduates/',
    "why_us": 'https://www.singaporepsa.com/careers/great-place-to-work/',
    "apply_now": 'https://psacareers.singaporepsa.com/cw/en/listing/',
    "contact_us": 'https://www.singaporepsa.com/about-us/contact-us/',
}

leave_applications = {}

def create_menu_keyboard():
    markup = types.InlineKeyboardMarkup(row_width=1)
    item_hr_info = types.InlineKeyboardButton("HR Information", callback_data='hr_info')
    item_apply_leave = types.InlineKeyboardButton("Apply for Leave", callback_data='apply_leave')
    item_contact_hr = types.InlineKeyboardButton("Contact HR", callback_data='contact_hr')
    item_start_ai = types.InlineKeyboardButton("Start chatting with our AI", callback_data='startAI')
    markup.add(item_hr_info, item_apply_leave, item_contact_hr, item_start_ai)
    return markup

@bot.callback_query_handler(func=lambda call: True)
def handle_menu_callback(call):
    user_id = call.from_user.id
    if call.data == 'hr_info':
        bot.send_message(user_id, "You selected HR Information. Use /hr_info command to explore HR documents.")
    elif call.data == 'apply_leave':
        bot.send_message(user_id, "You selected Apply for Leave. Use /apply_leave command to apply for leave.")
    elif call.data == 'contact_hr':
        send_contact_pdf(user_id)
    elif call.data == 'startAI':
        start_ai(user_id)

@bot.message_handler(commands=['menu'])
def display_menu(message):
    user_id = message.chat.id
    menu_markup = create_menu_keyboard()
    bot.send_message(user_id, "Select an option from the menu below:", reply_markup=menu_markup)

# Function to start convo
@bot.message_handler(commands=['start', 'hello'])
def send_welcome(message):
    user_id = message.chat.id
    bot.reply_to(message, "Welcome to the HR Virtual Assistant! How can I assist you today? Type /menu to find out more!")
    user_data[user_id] = {'state': HR_INFO}

@bot.message_handler(commands=['hr_info'])
def handle_hr_info_command(message):
    user_id = message.chat.id
    user_data[user_id]['state'] = HR_INFO
    bot.reply_to(message, "You are now in the HR Information menu. Type one of the following:\n\n"
                          "/passes_permits\n/guidelines\n/bus_guides\n/tender_notices\n/students\n/graduates\n/why_us\n/apply_now\n/contact_us")

# Function to handle user input
@bot.message_handler(commands=['passes_permits', 'guidelines', 'bus_guides', 'tender_notices', 'students', 'graduates', 'why_us', 'apply_now', 'contact_us'])
def handle_hr_info_request(message):
    user_id = message.chat.id
    command = message.text.strip('/')

    if command in hr_documents:
        bot.reply_to(message, f"Here is the HR information you requested: {hr_documents[command]}")
        user_data[user_id]['state'] = HR_INFO
    else:
        bot.reply_to(message, "I couldn't find the HR information you requested.")
        user_data[user_id]['state'] = HR_INFO

# Function to apply leave
@bot.message_handler(commands=['apply_leave'])
def apply_leave_command(message):
    user_id = message.chat.id
    user_data[user_id]['state'] = APPLY_LEAVE
    bot.reply_to(message, "You are now in the Leave Application menu. Please enter the start date of your leave (YYYY-MM-DD):")

@bot.message_handler(func=lambda message: user_data.get(message.chat.id, {}).get('state') == APPLY_LEAVE)
def apply_leave_start_date(message):
    user_id = message.chat.id

    try:
        start_date = datetime.strptime(message.text, '%Y-%m-%d')
        current_date = datetime.now()

        if start_date <= current_date:
            bot.reply_to(message, "Start date should be after the current date. Please enter a valid start date.")
            return

        user_data[user_id]['leave_start'] = start_date.strftime('%Y-%m-%d')
        user_data[user_id]['state'] = APPLY_LEAVE + 1
        bot.send_message(user_id, "Please enter the end date of your leave (YYYY-MM-DD):")
    except ValueError:
        bot.reply_to(message, "Invalid date format. Please enter the date in YYYY-MM-DD format.")

@bot.message_handler(func=lambda message: user_data.get(message.chat.id, {}).get('state') == APPLY_LEAVE + 1)
def apply_leave_end_date(message):
    user_id = message.chat.id

    try:
        end_date = datetime.strptime(message.text, '%Y-%m-%d')
        start_date = datetime.strptime(user_data[user_id]['leave_start'], '%Y-%m-%d')

        if end_date <= start_date:
            bot.reply_to(message, "End date should be later than the start date. Please enter a valid end date.")
            return

        leave_request = {
            'start_date': start_date.strftime('%Y-%m-%d'),
            'end_date': end_date.strftime('%Y-%m-%d'),
            'user_id': user_id,
        }
        leave_applications[user_id] = leave_request
        bot.reply_to(message, "Leave application submitted. HR will review your request.")
        user_data[user_id]['state'] = HR_INFO
    except ValueError:
        bot.reply_to(message, "Invalid date format. Please enter the date in YYYY-MM-DD format.")

# Function to get contact information
@bot.message_handler(commands=['contact_hr'])
def send_contact_pdf(user_id):
    try:
        with open("PSAContacts.pdf", "rb") as pdf_file:
            bot.send_document(user_id, pdf_file)
    except Exception as e:
        print(f"Error sending PDF: {e}")
        bot.send_message(user_id, "Unable to send the PDF at the moment.")


@bot.message_handler(commands=['startAI'])
def start_ai(user_id):
    #user_id = message.chat.id
    user_data[user_id]["status"] = CHAT_AI
    bot.send_message(user_id, "You have started a chat with our AI bot. Type something. Use /stopai to end the chat.")

@bot.message_handler(commands=['stopai'])
def stop_ai(message):
    user_id = message.chat.id
    user_data[user_id]["status"] = HR_INFO
    bot.reply_to(message, "You have ended the chat with our AI bot.")

@bot.message_handler()
def chat_ai(message):
    user_id = message.chat.id
    if user_data.get(user_id) == None:
        bot.reply_to(message, "You have entered an unknown command. Try using /start.")


    elif user_data[user_id]["status"] == CHAT_AI:
        try:
                if user_data[user_id]["status"] == CHAT_AI:
                    completion = openai.ChatCompletion.create(model="gpt-3.5-turbo",
                                                            messages=[{"role": "user", "content": PROMPT + message.text}])
                    bot.reply_to(message, completion.choices[0].message.content)
        except:
                bot.send_message(user_id, "Our AI chat bot is not available at the moment. Please try again later.")
    else:
        bot.reply_to(message, "You have entered an unknown command. Try using /start.")

bot.infinity_polling()