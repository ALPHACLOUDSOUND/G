import logging
import random
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Updater, CommandHandler, CallbackQueryHandler, MessageHandler, Filters, CallbackContext
from pymongo import MongoClient
from telegram import Bot

# Configure logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# MongoDB connection
client = MongoClient('your_mongodb_connection_string')
db = client['cricket_bot']
users = db['users']
matches = db['matches']

# Bot token
BOT_TOKEN = 'your_telegram_bot_token'

# Helper functions for MongoDB
def get_user(user_id):
    return users.find_one({"user_id": user_id})

def update_user(user):
    users.update_one({"user_id": user['user_id']}, {"$set": user}, upsert=True)

def get_match(match_id):
    return matches.find_one({"match_id": match_id})

def update_match(match):
    matches.update_one({"match_id": match['match_id']}, {"$set": match}, upsert=True)

# Command Handlers
def start(update: Update, context: CallbackContext):
    user = update.effective_user
    context.bot.send_message(chat_id=user.id, text=f"Hello {user.first_name}, welcome to the Cricket Bot!")

    # Register user in the database
    user_data = get_user(user.id)
    if not user_data:
        users.insert_one({
            "user_id": user.id,
            "username": user.username,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "matches": [],
            "team": None
        })

    # Send command options
    send_main_menu(update, context)

def send_main_menu(update: Update, context: CallbackContext):
    keyboard = [
        [InlineKeyboardButton("Join Team", callback_data='join_team')],
        [InlineKeyboardButton("Start Match", callback_data='start_match')],
        [InlineKeyboardButton("View Teams", callback_data='view_teams')],
        [InlineKeyboardButton("Help", callback_data='help')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    update.message.reply_text('Choose an option:', reply_markup=reply_markup)

def join_team(update: Update, context: CallbackContext):
    user = update.effective_user
    user_data = get_user(user.id)

    if user_data['team']:
        context.bot.send_message(chat_id=user.id, text="You are already in a team!")
        return

    keyboard = [
        [InlineKeyboardButton("Team A", callback_data='join_team_A')],
        [InlineKeyboardButton("Team B", callback_data='join_team_B')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    context.bot.send_message(chat_id=user.id, text="Select a team to join:", reply_markup=reply_markup)

def start_match(update: Update, context: CallbackContext):
    user = update.effective_user
    # Only the bot owner can start a match
    if user.id != int(BOT_OWNER_ID):
        context.bot.send_message(chat_id=user.id, text="Only the bot owner can start a match.")
        return

    match_id = f"match_{int(time.time())}"
    match_data = {
        "match_id": match_id,
        "team_A": [],
        "team_B": [],
        "batting_team": None,
        "bowling_team": None,
        "score": {"A": 0, "B": 0},
        "wickets": {"A": 0, "B": 0},
        "overs": {"A": 0, "B": 0},
        "status": "toss"
    }
    matches.insert_one(match_data)
    context.bot.send_message(chat_id=update.effective_chat.id, text="Match started! Time for the toss.")
    send_toss_menu(update, context, match_id)

def send_toss_menu(update: Update, context: CallbackContext, match_id):
    keyboard = [
        [InlineKeyboardButton("Heads", callback_data=f'toss_heads_{match_id}')],
        [InlineKeyboardButton("Tails", callback_data=f'toss_tails_{match_id}')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    context.bot.send_message(chat_id=update.effective_chat.id, text="Team A, choose heads or tails:", reply_markup=reply_markup)

def button(update: Update, context: CallbackContext):
    query = update.callback_query
    query.answer()

    data = query.data
    user = query.from_user
    user_data = get_user(user.id)

    if data.startswith('join_team'):
        team = data.split('_')[2]
        user_data['team'] = team
        update_user(user_data)
        query.edit_message_text(text=f"You have joined Team {team}")

    elif data.startswith('toss'):
        match_id = data.split('_')[2]
        match_data = get_match(match_id)
        result = random.choice(['heads', 'tails'])
        if data.split('_')[1] == result:
            match_data['batting_team'] = 'A'
            match_data['bowling_team'] = 'B'
        else:
            match_data['batting_team'] = 'B'
            match_data['bowling_team'] = 'A'
        match_data['status'] = 'playing'
        update_match(match_data)
        query.edit_message_text(text=f"Toss result: {result.capitalize()}. Team {match_data['batting_team']} will bat first.")
        send_batting_order_menu(update, context, match_id)

def send_batting_order_menu(update: Update, context: CallbackContext, match_id):
    match_data = get_match(match_id)
    team = match_data['batting_team']
    players = users.find({"team": team})

    keyboard = [[InlineKeyboardButton(player['first_name'], callback_data=f'bat_{player["user_id"]}_{match_id}') for player in players]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    context.bot.send_message(chat_id=update.effective_chat.id, text="Select batting order:", reply_markup=reply_markup)

def help_command(update: Update, context: CallbackContext):
    context.bot.send_message(chat_id=update.effective_chat.id, text="Help text here")

def main():
    updater = Updater(token=BOT_TOKEN, use_context=True)
    dispatcher = updater.dispatcher

    dispatcher.add_handler(CommandHandler('start', start))
    dispatcher.add_handler(CallbackQueryHandler(button))
    dispatcher.add_handler(CommandHandler('help', help_command))

    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()
