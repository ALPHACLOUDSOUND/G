import logging
import random
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, CallbackContext

# API credentials
BOT_TOKEN = 'your_bot_token'
GROUP_ID = 'your_group_id'  # Replace with your group ID
OWNER_ID = 'your_telegram_id'  # Telegram ID of the bot owner

# Store user UPI info
user_upi_info = {}

# Configure logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

async def start(update: Update, context: CallbackContext) -> None:
    keyboard = [[InlineKeyboardButton("Join Giveaway", callback_data='join')]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("Welcome to the Giveaway Bot! Click the button below to join the giveaway.", reply_markup=reply_markup)

async def button(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    user_id = query.from_user.id

    if query.data == 'join':
        chat_member = await context.bot.get_chat_member(chat_id=GROUP_ID, user_id=user_id)
        
        if chat_member.status in ['member', 'administrator', 'creator']:
            if user_id not in user_upi_info:
                user_upi_info[user_id] = {'upi': None, 'username': query.from_user.username}
                await query.edit_message_text("You've successfully joined the group! Please send your UPI ID to participate in the giveaway.")
                # Notify the owner about the new user
                await context.bot.send_message(
                    chat_id=OWNER_ID,
                    text=f"New participant:\nUser ID: {user_id}\nUsername: {query.from_user.username}"
                )
            else:
                await query.edit_message_text("You are already entered in the giveaway.")
        else:
            await query.edit_message_text("Please join the group first to participate in the giveaway.")

async def collect_upi(update: Update, context: CallbackContext) -> None:
    user_id = update.message.from_user.id
    if user_id in user_upi_info:
        user_upi_info[user_id]['upi'] = update.message.text.strip()
        await update.message.reply_text("Thank you! Your UPI ID has been recorded.")
    else:
        await update.message.reply_text("You need to join the group first using the inline command.")

async def draw(update: Update, context: CallbackContext) -> None:
    if update.message.from_user.id != int(OWNER_ID):
        await update.message.reply_text("Only the bot owner can draw the giveaway.")
        return

    if not user_upi_info:
        await update.message.reply_text("No participants found.")
        return

    winner_id = random.choice(list(user_upi_info.keys()))
    winner_upi = user_upi_info[winner_id]['upi']
    winner_username = user_upi_info[winner_id]['username']
    
    # Send the winner information to the owner
    await context.bot.send_message(
        chat_id=OWNER_ID,
        text=f"Winner Details:\nUser ID: {winner_id}\nUsername: {winner_username}\nUPI ID: {winner_upi}"
    )

    # Forward all UPI IDs to the bot owner's private chat
    upi_list = "\n".join(f"User ID: {user_id}, Username: {info['username']}, UPI ID: {info['upi']}" for user_id, info in user_upi_info.items())
    await context.bot.send_message
