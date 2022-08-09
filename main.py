import logging

from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import Updater, CommandHandler, ConversationHandler, MessageHandler, Filters, CallbackContext

import pdf_manager
from config import BOT_TOKEN


logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)

logger = logging.getLogger(__name__)

CHOICE, MERGE, SPLIT, CONVERT = range(4)

user_files = {}  # для хранения списка загруженных каждым польователем PDF файлов для объединения


def start(update: Update, context: CallbackContext) -> int:
    """Даёт пользователю выбрать действие с файлом"""
    reply_keyboard = [['Объединить', 'Разделить'], ["Конвертировать DOCX в PDF"]]

    update.message.reply_text(
        'Выберите действие с PDF/DOCX\n'
        'Для отмены введите /cancel',
        reply_markup=ReplyKeyboardMarkup(
            reply_keyboard, one_time_keyboard=True, input_field_placeholder='Выберите действие с PDF/DOCX',
            resize_keyboard=True
        ),
    )

    return CHOICE


def choice(update: Update, context: CallbackContext) -> int:
    """Даёт пользователю выбрать действие с PDF файлом"""
    match update.message.text:
        case "Объединить":
            reply_keyboard = [["Объединить"]]
            update.message.reply_text(
                'Пришлите PDF файлы для объединения\n'
                'После того как пришлёте все нужные файлы нажмите кнопку "Объединить"',
                reply_markup=ReplyKeyboardMarkup(
                    reply_keyboard, one_time_keyboard=True, resize_keyboard=True
                ),
            )
            return MERGE

        case "Разделить":
            update.message.reply_text(
                'Пришлите PDF файл для разделения',
                reply_markup=ReplyKeyboardRemove(),
            )
            return SPLIT

        case "Конвертировать DOCX в PDF":
            update.message.reply_text(
                'Пришлите DOCX файл для конвертирования в PDF',
                reply_markup=ReplyKeyboardRemove(),
            )
            return CONVERT

        case _:
            update.message.reply_text(
                'Действие не распознано, выберите заново\n'
                'Для отмены введите /cancel',
            )
            return CHOICE


def split(update: Update, context: CallbackContext) -> int:
    """Принимает ПДФ, разделяет его по страницам. Возвращает пользователю страницы и удаляет за собой файлы."""
    pdf_file = update.message.document.get_file()
    pdf_file.download(f'PDF Input/user_pdf_{update.message.document.file_unique_id}.pdf')

    update.message.reply_text('Ваши разделённые файлы:')

    list_of_pdfs = pdf_manager.split(f'PDF Input/user_pdf_{update.message.document.file_unique_id}.pdf')

    for file in list_of_pdfs:
        update.message.reply_document(document=open(file, 'rb'))
        pdf_manager.delete(file)

    pdf_manager.delete(f'PDF Input/user_pdf_{update.message.document.file_unique_id}.pdf')

    return ConversationHandler.END


def merge(update: Update, context: CallbackContext) -> int:
    """Принимает ПДФ, разделяет его по страницам. Возвращает пользователю страницы и удаляет за собой файлы."""
    logger.info(f"Merger update: {update.message}")

    # Присутствует ли пользователь в списке user_files
    if not str(update.message.chat.id) in user_files.keys():
        user_files.update([(str(update.message.chat.id), {"all_files": False, "filenames": []})])
        logger.info(f"user_files update: {user_files}")

    # Проверка нажатия кнопки объединить
    if update.message.text == "Объединить":
        filenames_list = user_files[str(update.message.chat.id)]["filenames"]
        user_files.update([(str(update.message.chat.id), {"all_files": True, "filenames": filenames_list})])
        logger.info(f"user_files update: {user_files}")

    # Загрузил ли пользователь все нужные файлы для объединения
    if user_files[str(update.message.chat.id)]["all_files"]:
        update.message.reply_text('Ваш объединённый файл:')
        file = pdf_manager.merge(user_files[str(update.message.chat.id)]["filenames"])
        update.message.reply_document(document=open(file, 'rb'))

        # Удаление файлов
        pdf_manager.delete(file)
        for file in user_files[str(update.message.chat.id)]["filenames"]:
            pdf_manager.delete(file)

        # Стираем список загруженных пользователем файлов
        user_files.update([(str(update.message.chat.id), {"all_files": False, "filenames": []})])
        logger.info(f"user_files update: {user_files}")

        return ConversationHandler.END

    else:
        # Загрузка файла
        pdf_file = update.message.document.get_file()
        pdf_file.download(f'PDF Input/user_pdf_{update.message.document.file_unique_id}.pdf')

        # Добавление названия файла в список загруженных пользователем файлов
        filenames_list = user_files[str(update.message.chat.id)]["filenames"]
        filenames_list.append(f'PDF Input/user_pdf_{update.message.document.file_unique_id}.pdf')
        user_files.update([(str(update.message.chat.id), {"all_files": False, "filenames": filenames_list})])
        logger.info(f"user_files update: {user_files}")

        return MERGE


def convert(update: Update, context: CallbackContext) -> int:
    """Принимает docx, конвертирует его в PDF и отправляет обратно пользователю"""
    docx_file = update.message.document.get_file()
    file_unique_id = update.message.document.file_unique_id
    docx_file.download(f'PDF Input/user_docx_{file_unique_id}.docx')

    update.message.reply_text('Ваш конвертированный файл:')

    converted_pdf_file = pdf_manager.docx_convert(f'PDF Input/user_docx_{file_unique_id}.docx')

    update.message.reply_document(document=open(converted_pdf_file, 'rb'))
    pdf_manager.delete(converted_pdf_file)

    pdf_manager.delete(f'PDF Input/user_docx_{file_unique_id}.docx')

    return ConversationHandler.END


def cancel(update: Update, context: CallbackContext) -> int:
    """Отменяет выбор действия"""
    update.message.reply_text(
        'Вы отменили выполнение действия с pdf.\nЧтобы начать заново введите /start', reply_markup=ReplyKeyboardRemove()
    )

    return ConversationHandler.END


def help_command(update: Update, context: CallbackContext) -> None:
    update.message.reply_text('Бот для объединения/разделения PDF файлов, конвертации DOCX в PDF.\n'
                              'Для начала работы с ботом введите /start')


def main() -> None:
    """Start the bot."""
    # Create the Updater and pass it your bot's token.
    updater = Updater(BOT_TOKEN)

    # Get the dispatcher to register handlers
    dispatcher = updater.dispatcher

    # Custom Handler
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            CHOICE: [MessageHandler(Filters.text, choice)],
            MERGE: [MessageHandler(Filters.document | Filters.text, merge)],
            SPLIT: [MessageHandler(Filters.document, split)],
            CONVERT: [MessageHandler(Filters.document, convert)],
        },
        fallbacks=[CommandHandler('cancel', cancel)],
    )

    dispatcher.add_handler(conv_handler)
    dispatcher.add_handler(CommandHandler("help", help_command))

    # Start the Bot
    updater.start_polling()

    # Run the bot until you press Ctrl-C or the process receives SIGINT,
    # SIGTERM or SIGABRT. This should be used most of the time, since
    # start_polling() is non-blocking and will stop the bot gracefully.
    updater.idle()


if __name__ == '__main__':
    main()
