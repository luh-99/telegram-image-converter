import os
import logging
import asyncio
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes
from PIL import Image
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")  # Load chat ID from .env

# Configure logging
logging.basicConfig(level=logging.INFO)

# Start command handler
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Send me a .webp file, and I'll convert it for you!")

# Handle document uploads
async def handle_document(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Ensure the message contains a document (and may ignore non-documents in groups)
    if update.message.chat.type in ["group", "supergroup"] and not update.message.document:
        return

    file = update.message.document
    # Check if the mime type is correct for webp files
    if file.mime_type != "image/webp":
        await update.message.reply_text("Please send a valid .webp file.")
        return

    file_path = await file.get_file()
    os.makedirs("downloads", exist_ok=True)
    webp_file = f"downloads/{file.file_id}.webp"
    await file_path.download_to_drive(webp_file)

    keyboard = [[
        InlineKeyboardButton("PNG", callback_data=f"convert_{file.file_id}_png"),
        InlineKeyboardButton("JPEG", callback_data=f"convert_{file.file_id}_jpeg"),
    ], [
        InlineKeyboardButton("GIF", callback_data=f"convert_{file.file_id}_gif"),
        InlineKeyboardButton("SVG", callback_data=f"convert_{file.file_id}_svg"),
    ]]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text("Choose a format:", reply_markup=reply_markup)

# File conversion handler
async def convert_file(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    await query.message.reply_text("⏳ Please wait...")
    await asyncio.sleep(5)  # Simulating a conversion delay

    _, file_id, format = query.data.split("_")
    webp_path = f"downloads/{file_id}.webp"
    output_path = f"downloads/{file_id}.{format}"

    try:
        if format in ["png", "jpeg"]:
            img = Image.open(webp_path).convert("RGBA")
            img.save(output_path, format.upper())
        elif format == "gif":
            img = Image.open(webp_path)
            img.save(output_path, "GIF")
        elif format == "svg":
            output_path = f"downloads/{file_id}.png"  # Saving as PNG instead
            img = Image.open(webp_path)
            img.save(output_path, "PNG")

        with open(output_path, "rb") as file:
            await context.bot.send_document(chat_id=CHAT_ID or update.effective_chat.id, document=file)

    except Exception as e:
        logging.error(f"Error during file conversion: {e}")
        await query.message.reply_text("An error occurred during conversion.")

    finally:
        # Clean up files
        if os.path.exists(webp_path):
            os.remove(webp_path)
        if os.path.exists(output_path):
            os.remove(output_path)

# Main function
async def main():
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.Document.ALL, handle_document))
    app.add_handler(CallbackQueryHandler(convert_file))

    logging.info("Bot is running...")
    await app.run_polling()

# Fix for Railway (Handles "event loop is already running" error)
if name == "main"