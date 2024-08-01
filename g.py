import json
from random import choice
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import (
    Updater,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    Filters,
    CallbackContext,
)

API_ID = '26661233'
API_HASH = '2714c0f32cbede4c64f4e9fd628dbe29'
BOT_TOKEN = '7257335666:AAFAcI84Jxv-Be5N8mfyjB-gf3wYpJBjAIE'
GROUP_ID = -1002070732383  # Example group ID
BOT_OWNER_ID = 7049798779  # Example bot owner ID
CHANNEL_ID =  -1002150575443 # Example channel ID to save participant details
GROUP_LINK = 'https://t.me/tamilchattingu'

# Helper Functions
def is_user_in_group(context: CallbackContext, user_id: int) -> bool:
    try:
        member = context.bot.get_chat_member(GROUP_ID, user_id)
        return member.status in ['member', 'administrator', 'creator']
    except:
        return False

def save_participant_to_channel(user_id: int, username: str, upi_id: str):
    message = json.dumps({
        'user_id': user_id,
        'username': username,
        'upi_id': upi_id
    }, indent=4)
    # Send participant details to the channel
    context.bot.send_message(
        chat_id=CHANNEL_ID,
        text=f"New Participant:\n{message}"
    )

def get_participants_from_channel(context: CallbackContext):
    messages = context.bot.get_chat_history(CHANNEL_ID, limit=100)  # Adjust limit as needed
    participants = []
    for message in messages:
        try:
            participant = json.loads(message.text)
            participants.append(participant)
        except json.JSONDecodeError:
            continue
    return participants

def start(update: Update, context: CallbackContext):
    update.message.reply_text(
        "Welcome to the Giveaway Bot! Send your UPI ID to participate in the giveaway."
    )

def participate(update: Update, context: CallbackContext):
    user = update.message.from_user
    user_id = user.id
    username = user.username
    upi_id = update.message.text

    if not is_user_in_group(context, user_id):
        update.message.reply_text("You must join the specified group to participate.")
        return

    save_participant_to_channel(user_id, username, upi_id)
    update.message.reply_text("You have successfully entered the giveaway.")

def select_winner(update: Update, context: CallbackContext):
    if update.message.from_user.id != BOT_OWNER_ID:
        update.message.reply_text("Only the bot owner can select a winner.")
        return

    participants = get_participants_from_channel(context)
    if not participants:
        update.message.reply_text("No participants found.")
        return

    winner = choice(participants)
    context.bot.send_message(
        chat_id=update.message.chat_id,
        text=f"The winner is @{winner['username']} with UPI ID {winner['upi_id']}."
    )

def show_commands(update: Update, context: CallbackContext):
    keyboard = [
        [
            InlineKeyboardButton("Start", callback_data='start'),
            InlineKeyboardButton("Participate", callback_data='participate'),
            InlineKeyboardButton("Select Winner", callback_data='select_winner'),
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    update.message.reply_text('Choose a command:', reply_markup=reply_markup)

def button(update: Update, context: CallbackContext):
    query = update.callback_query
    query.answer()

    if query.data == 'start':
        start(query, context)
    elif query.data == 'participate':
        query.edit_message_text(text="Send your UPI ID to participate.")
    elif query.data == 'select_winner':
        select_winner(query, context)

def check_group_membership(update: Update, context: CallbackContext):
    user_id = update.message.from_user.id
    if not is_user_in_group(context, user_id):
        update.message.reply_text(f"You need to join the group to participate. Please join: {GROUP_LINK}")
    else:
        update.message.reply_text("You are already a member of the group.")

def main():
    updater = Updater(token=BOT_TOKEN, use_context=True)
    dp = updater.dispatcher

    dp.add_handler(CommandHandler('start', start))
    dp.add_handler(MessageHandler(Filters.text & ~Filters.command, participate))
    dp.add_handler(CommandHandler('select_winner', select_winner))
    dp.add_handler(CommandHandler('show_commands', show_commands))
    dp.add_handler(CallbackQueryHandler(button))
    dp.add_handler(MessageHandler(Filters.status_update.new_chat_members, check_group_membership))

    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()
