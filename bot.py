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
CHAT_ID = os.getenv("CHAT_ID")  # Load chat ID from .env

# Configure logging
logging.basicConfig(level=logging.INFO)

# Start command handler
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Send me a .webp file, and I'll convert it for you!")

# Handle document uploads
async def handle_document(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message.document:
        return

    file = update.message.document
    file_id = file.file_id
    webp_path = f"downloads/{file_id}.webp"

    await file.get_file().download(webp_path)

    # Create inline keyboard for format selection
    keyboard = [
        [InlineKeyboardButton("Convert to GIF", callback_data=f"convert_gif_{file_id}")],
        [InlineKeyboardButton("Convert to PNG", callback_data=f"convert_png_{file_id}")]
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text("Please choose the format you want to convert to:", reply_markup=reply_markup)

# Handle callback for format selection
async def convert_file(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()  # Acknowledge the callback

    data = query.data.split("_")
    format = data[1]  # 'gif' or 'png'
    file_id = data[2]

    webp_path = f"downloads/{file_id}.webp"
    output_path = None

    try:
        if format == "gif":
            output_path = f"downloads/{file_id}.gif"
            img = Image.open(webp_path)
            img.save(output_path, "GIF")
        elif format == "png":
            output_path = f"downloads/{file_id}.png"
            img = Image.open(webp_path)
            img.save(output_path, "PNG")

        with open(output_path, "rb") as file:
            await context.bot.send_document(chat_id=CHAT_ID or update.effective_chat.id, document=file)
            await query.message.reply_text("Conversion successful! The file has been sent.")

    except Exception as e:
        logging.error(f"Error during file conversion: {e}")
        await query.message.reply_text("An error occurred during conversion. Please try again.")

    finally:
        # Clean up files
        if os.path.exists(webp_path):
            os.remove(webp_path)
        if output_path and os.path.exists(output_path):
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
if __name__ == "__main__":
    import nest_asyncio
    nest_asyncio.apply()  # Allows nested event loops

    asyncio.run(main())
