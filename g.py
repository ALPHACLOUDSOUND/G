import logging
import random
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Updater, CommandHandler, CallbackQueryHandler, MessageHandler, filters, CallbackContext

# API credentials
BOT_TOKEN = '7257335666:AAFAcI84Jxv-Be5N8mfyjB-gf3wYpJBjAIE'
GROUP_ID = '-1002070732383'  # Replace with your group ID
OWNER_ID = '7049798779'  # Telegram ID of the bot owner

# Store user UPI info
user_upi_info = {}

# Configure logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

def start(update: Update, context: CallbackContext) -> None:
    keyboard = [[InlineKeyboardButton("Join Giveaway", callback_data='join')]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    update.message.reply_text("Welcome to the Giveaway Bot! Click the button below to join the giveaway.", reply_markup=reply_markup)

def button(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    user_id = query.from_user.id

    if query.data == 'join':
        chat_member = context.bot.get_chat_member(chat_id=GROUP_ID, user_id=user_id)
        
        if chat_member.status in ['member', 'administrator', 'creator']:
            if user_id not in user_upi_info:
                user_upi_info[user_id] = {'upi': None, 'username': query.from_user.username}
                query.edit_message_text("You've successfully joined the group! Please send your UPI ID to participate in the giveaway.")
                # Notify the owner about the new user
                context.bot.send_message(
                    chat_id=OWNER_ID,
                    text=f"New participant:\nUser ID: {user_id}\nUsername: {query.from_user.username}"
                )
            else:
                query.edit_message_text("You are already entered in the giveaway.")
        else:
            query.edit_message_text("Please join the group first to participate in the giveaway.")

def collect_upi(update: Update, context: CallbackContext) -> None:
    user_id = update.message.from_user.id
    if user_id in user_upi_info:
        user_upi_info[user_id]['upi'] = update.message.text.strip()
        update.message.reply_text("Thank you! Your UPI ID has been recorded.")
    else:
        update.message.reply_text("You need to join the group first using the inline command.")

def draw(update: Update, context: CallbackContext) -> None:
    if update.message.from_user.id != int(OWNER_ID):
        update.message.reply_text("Only the bot owner can draw the giveaway.")
        return

    if not user_upi_info:
        update.message.reply_text("No participants found.")
        return

    winner_id = random.choice(list(user_upi_info.keys()))
    winner_upi = user_upi_info[winner_id]['upi']
    winner_username = user_upi_info[winner_id]['username']
    
    # Send the winner information to the owner
    context.bot.send_message(
        chat_id=OWNER_ID,
        text=f"Winner Details:\nUser ID: {winner_id}\nUsername: {winner_username}\nUPI ID: {winner_upi}"
    )

    # Forward all UPI IDs to the bot owner's private chat
    upi_list = "\n".join(f"User ID: {user_id}, Username: {info['username']}, UPI ID: {info['upi']}" for user_id, info in user_upi_info.items())
    context.bot.send_message(
        chat_id=OWNER_ID,
        text=f"All UPI IDs:\n{upi_list}"
    )

    update.message.reply_text(f"The winner is User ID: {winner_id}, Username: {winner_username} with UPI ID: {winner_upi}")
    update.message.reply_text("Thanks for using our services!")

def main():
    # Initialize the bot
    updater = Updater(BOT_TOKEN)
    dp = updater.dispatcher
    
    # Define command handlers
    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(MessageHandler(Filters.text & ~Filters.command, collect_upi))
    
    # Define callback query handler for inline buttons
    dp.add_handler(CallbackQueryHandler(button))
    
    # Define admin command handler for drawing the giveaway
    dp.add_handler(CommandHandler("draw", draw))

    # Start the bot
    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()
