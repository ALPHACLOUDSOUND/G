from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ParseMode
from telegram.ext import Updater, CommandHandler, CallbackQueryHandler, CallbackContext, Filters, MessageHandler
import random

# Configuration (replace with your actual values)
BOT_TOKEN = '7257335666:AAFAcI84Jxv-Be5N8mfyjB-gf3wYpJBjAIE'
ADMIN_ID = '7049798779'
GROUP_ID = '-1002070732383'
PRIVATE_CHANNEL_ID = '@giveawaytea'  # Private channel where UPI details will be stored

# Global variables
users_upi = {}
giveaway_active = False

def start(update: Update, context: CallbackContext) -> None:
    keyboard = [
        [InlineKeyboardButton("Start Giveaway", callback_data='start_giveaway')],
        [InlineKeyboardButton("End Giveaway", callback_data='end_giveaway')],
        [InlineKeyboardButton("Check Group Membership", callback_data='check_group')],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    update.message.reply_text('Welcome! Choose an option:', reply_markup=reply_markup)

def button(update: Update, context: CallbackContext) -> None:
    global giveaway_active
    query = update.callback_query
    query.answer()

    if query.data == 'start_giveaway':
        giveaway_active = True
        query.edit_message_text(text="Giveaway started! Reply with your UPI to enter.")

    elif query.data == 'end_giveaway':
        if update.callback_query.from_user.id == int(ADMIN_ID):
            giveaway_active = False
            if users_upi:
                winner_id = random.choice(list(users_upi.keys()))
                winner_upi = users_upi[winner_id]
                message = (
                    f"Congratulations @{winner_id}! You have won the giveaway.\n\n"
                    f"UPI: {winner_upi}\n\n"
                    "Details of all participants:\n"
                    f"{'\n'.join([f'@{uid} - UPI: {upi}' for uid, upi in users_upi.items()])}"
                )
                context.bot.send_message(
                    chat_id=PRIVATE_CHANNEL_ID,
                    text=message,
                    parse_mode=ParseMode.MARKDOWN
                )
                # Send a copy of the details to the bot owner
                context.bot.send_message(
                    chat_id=ADMIN_ID,
                    text=message,
                    parse_mode=ParseMode.MARKDOWN
                )
            else:
                context.bot.send_message(chat_id=ADMIN_ID, text="No participants in the giveaway.")
        else:
            query.message.reply_text('You are not authorized to end the giveaway.')

    elif query.data == 'check_group':
        if update.callback_query.from_user.id == int(ADMIN_ID):
            check_group_members(context)
        else:
            query.message.reply_text('You are not authorized to check group membership.')

def handle_message(update: Update, context: CallbackContext) -> None:
    global giveaway_active
    user_id = str(update.message.from_user.id)
    username = update.message.from_user.username

    if giveaway_active and update.message.text:
        if user_id in users_upi:
            update.message.reply_text('You have already participated in the giveaway.')
        else:
            users_upi[user_id] = update.message.text
            update.message.reply_text('Your UPI has been recorded. Good luck!')

def check_group_members(context: CallbackContext) -> None:
    global users_upi
    for user_id in list(users_upi.keys()):
        try:
            member = context.bot.get_chat_member(chat_id=GROUP_ID, user_id=user_id)
            if member.status not in ['member', 'administrator', 'creator']:
                del users_upi[user_id]
        except Exception as e:
            print(f"Error checking user {user_id}: {e}")
    context.bot.send_message(chat_id=ADMIN_ID, text="Group membership check complete.")

def main() -> None:
    updater = Updater(BOT_TOKEN)

    dp = updater.dispatcher

    dp.add_handler(CommandHandler('start', start))
    dp.add_handler(CallbackQueryHandler(button))
    dp.add_handler(MessageHandler(Filters.text & ~Filters.command, handle_message))

    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()
