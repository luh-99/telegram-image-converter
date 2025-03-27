import os
import logging
import asyncio
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes
from PIL import Image
from dotenv import load_dotenv

load_dotenv()
TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID") # Load chat ID from .env

logging.basicConfig(level=logging.INFO)

    async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
        await update.message.reply_text("Send me a .webp file, and I'll convert it for you!")

async def handle_document(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Check if it's a group or supergroup and if there is a document
    if update.message.chat.type in ["group", "supergroup"] and not update.message.document:
        return

    file = update.message.document

    # If the file is not a .webp file, send a reply and return
    if file.mime_type != "image/webp":
        await update.message.reply_text("Please send a .webp file.")
        return

    # Download the .webp file to the server
    file_path = await file.get_file()
    os.makedirs("downloads", exist_ok=True)
    webp_file = f"downloads/{file.file_id}.webp"
    await file_path.download_to_drive(webp_file)

    # Create buttons for converting to other formats
    keyboard = [
        [
            InlineKeyboardButton("PNG", callback_data=f"convert_{file.file_id}_png"),
            InlineKeyboardButton("JPEG", callback_data=f"convert_{file.file_id}_jpeg"),
        ],
        [
            InlineKeyboardButton("GIF", callback_data=f"convert_{file.file_id}_gif"),
            InlineKeyboardButton("SVG", callback_data=f"convert_{file.file_id}_svg"),
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text("Choose a format:", reply_markup=reply_markup)

async def convert_file(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    await query.message.reply_text("⏳ Please Wait...")
    await asyncio.sleep(5)

    # Get the file ID and format from the callback data
    _, file_id, format = query.data.split("_")
    webp_path = f"downloads/{file_id}.webp"
    output_path = f"downloads/{file_id}.{format}"

    # Convert the .webp file to the chosen format
    if format in ["png", "jpeg"]:
        img = Image.open(webp_path).convert("RGBA")
        img.save(output_path, format.upper())
    elif format == "gif":
        img = Image.open(webp_path)
        img.save(output_path, "GIF")
    elif format == "svg":
        # Save as PNG before sending it as SVG (since Pillow doesn't support direct SVG output)
        output_path = f"downloads/{file_id}.png"
        img = Image.open(webp_path)
        img.save(output_path, "PNG")

    # Send the converted file back to the user
    with open(output_path, "rb") as file:
        await context.bot.send_document(chat_id=CHAT_ID or update.effective_chat.id, document=file) # Sends file back to the chat

        # Remove temporary files
        os.remove(webp_path)
        os.remove(output_path)

async def main():
    # Set up the application with the bot token
    app = Application.builder().token(TOKEN).build()

    # Add handlers for commands and messages
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.Document.ALL, handle_document))
    app.add_handler(CallbackQueryHandler(convert_file))

    print("Bot is running...")
    await app.run_polling()

if __name__ == "__main__":
    # Run the bot
    asyncio.run(main())
