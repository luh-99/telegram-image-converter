import os
import logging
import asyncio
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes
from PIL import Image
from dotenv import load_dotenv

load_dotenv()
TOKEN = os.getenv("7467798825:AAFf4L4WFZby8P_Rz5Fj9HxJtSb5gsfluxE")

logging.basicConfig(level=logging.INFO)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Send me a .webp file, and I'll convert it for you!")

async def handle_document(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.chat.type in ["group", "supergroup"] and not update.message.document:
        return

    file = update.message.document
    if file.mime_type != "image/webp":
        await update.message.reply_text("Please send a .webp file.")
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

async def convert_file(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    await query.message.reply_text("⏳ Please Wait...")
    await asyncio.sleep(5)

    _, file_id, format = query.data.split("_")
    webp_path = f"downloads/{file_id}.webp"
    output_path = f"downloads/{file_id}.{format}"

    if format in ["png", "jpeg"]:
        img = Image.open(webp_path).convert("RGBA")
        img.save(output_path, format.upper())
    elif format == "gif":
        img = Image.open(webp_path)
        img.save(output_path, "GIF")
    elif format == "svg":
        output_path = f"downloads/{file_id}.png"
        img = Image.open(webp_path)
        img.save(output_path, "PNG")

    with open(output_path, "rb") as file:
        await query.message.reply_document(document=file)

    os.remove(webp_path)
    os.remove(output_path)

async def main():
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.Document.ALL, handle_document))
    app.add_handler(CallbackQueryHandler(convert_file))

    print("Bot is running...")
    await app.run_polling()

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
