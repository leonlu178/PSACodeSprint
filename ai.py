import os
import telebot
import openai
from dotenv import load_dotenv

load_dotenv()
BOT_TOKEN = os.getenv('BOT_TOKEN')
bot = telebot.TeleBot(BOT_TOKEN)
API_KEY = os.getenv('API_KEY')

openai.api_key = API_KEY  #public key changes from time to time DakuWorks #api-and-update
openai.api_base = "https://api.daku.tech/v1"

@bot.message_handler()
def send_welcome(message):
    completion = openai.ChatCompletion.create(model="gpt-3.5-turbo", messages=[{"role": "user", "content": message.text}])
    bot.reply_to(message, completion.choices[0].message.content)

    
bot.infinity_polling()