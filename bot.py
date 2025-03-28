import logging
from telegram import Update, ReplyKeyboardMarkup, InputFile
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext
from dotenv import load_dotenv
from PIL import Image
import os

# Load environment variables
load_dotenv()
TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')

# Enable logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# Define supported formats
SUPPORTED_FORMATS = {
    'Convert to JPEG': 'jpeg',
    'Convert to PNG': 'png',
    'Convert to GIF': 'gif',
    'Convert to BMP': 'bmp',
}

# Define a command handler for the /start command
def start(update: Update, context: CallbackContext) -> None:
    keyboard = [[key for key in SUPPORTED_FORMATS.keys()], ['Cancel']]
    reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True)
    update.message.reply_text('Please choose a conversion option:', reply_markup=reply_markup)

# Handle user choices
def handle_message(update: Update, context: CallbackContext) -> None:
    user_choice = update.message.text
    if user_choice == 'Cancel':
        update.message.reply_text('Operation cancelled. You can type /start to process again.')
        return

    context.user_data['conversion_type'] = SUPPORTED_FORMATS[user_choice]
    update.message.reply_text(f'You selected: {user_choice}. Now please send me the file (image) to convert.')

# Handle file upload
def handle_file(update: Update, context: CallbackContext) -> None:
    if 'conversion_type' not in context.user_data:
        update.message.reply_text('Please select a conversion option first by typing /start.')
        return

    conversion_type = context.user_data['conversion_type']

    # Get the file from the message
    file = update.message.photo[-1].get_file()  # Get the highest resolution photo
    file.download('input_image')

    try:
        # Perform the conversion
        img = Image.open('input_image')
        output_file = f'output_image.{conversion_type}'
        img.save(output_file, format=conversion_type.upper())

        # Send the converted image back to the user
        with open(output_file, 'rb') as f:
            update.message.reply_photo(photo=InputFile(f, filename=output_file))

        # Inform the user about the completed process
        update.message.reply_text('Conversion successful! You can send another image or type /start to switch formats.')
        
    except Exception as e:
        logger.error(f'Error while processing the file: {e}')
        update.message.reply_text('There was an error during the conversion. Please make sure you sent a valid image file.')

    finally:
        # Clean up files
        if os.path.exists('input_image'):
            os.remove('input_image')
        if os.path.exists(output_file):
            os.remove(output_file)

# Main function to run the bot
def main() -> None:
    updater = Updater(TOKEN)

    # Register command and message handlers
    updater.dispatcher.add_handler(CommandHandler('start', start))
    updater.dispatcher.add_handler(MessageHandler(Filters.text & ~Filters.command, handle_message))
    updater.dispatcher.add_handler(MessageHandler(Filters.photo, handle_file))

    # Start the bot
    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()
