
from sys import stdout
from app.database.models.speakers import TelegramVotes
from threading import _start_new_thread
import telebot
from telebot import apihelper
from telebot import types
import logging
from random import randint
from dataclasses import dataclass
from telebot import AsyncTeleBot

@dataclass
class TelegramBasicConfig:
    token: str = ''
    chat_id: str = ''

class TBot(TelegramBasicConfig):

    def __init__(self, database, identity, bot_id):

        self.__logger = logging.getLogger(f'<TelegramBot> bot_name -> {bot_id}')
        self.telegram_votes = lambda: TelegramVotes(database)
        self.database_instance = database
        self.identity = identity
        self.bot_id = bot_id
        self.previus_message = ''
        self.api = None
        self.token = ''
        self.chat_id = ''

    def update_config(self, **kwargs):
        if (token:=kwargs.get('token')):
            self.stop_bot()
            self.token = token

        if (chat_id:=kwargs.get('chat_id')):
            self.chat_id = chat_id

    def auth(self):
        if self.api is not None:
            self.api.stop_polling()
        _start_new_thread(self.__auth, ())

    def __auth(self):
        self.__logger.info('Auth..')
        if not self.token:
            return
        try:

            apihelper.ENABLE_MIDDLEWARE = True
            apihelper.SESSION_TIME_TO_LIVE = 5 * 60
            self.api = AsyncTeleBot(self.token)
            self.api.callback_query_handler(
                func=lambda message: True)(self.callback_listener)
            self.api.infinity_polling()
        except:
            self.__logger.debug('on __auth', exc_info=1)

    def send_message(self, message, image_url=None, **kwargs):
        self.__logger.info('Sending message..')
        self.__logger.debug(f'bot_id: {self.bot_id}\n\nmessage: {message}\n')

        self.shortener_url = kwargs.get('button_link')
        if not self.previus_message == message:
            try:
                return self._post_message(message)
            except Exception as error:
                print(error, file=stdout)
                return

    def _post_message(self, message):

        reply_markup = types.InlineKeyboardMarkup()
        reply_markup.row_width = 2

        if self.shortener_url is not None:
            points = randint(5, 20)
            reply_markup.add(types.InlineKeyboardButton(f'{points} 🔥', callback_data=f'{points}'),
                             types.InlineKeyboardButton('✨IR AL CHOLLITO ✨', url=self.shortener_url))

        self.api.send_message(self.chat_id, message,
                              disable_web_page_preview=False, parse_mode='HTML', reply_markup=reply_markup).wait()
        self.previus_message = message
        self.__logger.info("Message sended!")

    def callback_listener(self, tlg_data):
        callback_id = tlg_data.id
        print(f'Callback listener: {callback_id}')
        user_id = tlg_data.from_user.id
        message_id = tlg_data.message.message_id
        try:
            if (callback_data := tlg_data.data).isdigit():
                if self.telegram_votes().vote(self.identity, self.bot_id, user_id, message_id):
                    self.api.answer_callback_query(callback_id, text='+ 1 🔥')
                    callback_data = int(callback_data) + 6

                    reply_markup = types.InlineKeyboardMarkup(row_width=2)
                    url_message = tlg_data.message.reply_markup.keyboard[0][1]
                    reply_markup.add(types.InlineKeyboardButton(
                        f'{callback_data} 🔥', callback_data=f'{callback_data}'), url_message)

                    self.api.edit_message_reply_markup(
                        chat_id=tlg_data.message.chat.id, message_id=message_id, inline_message_id=tlg_data.inline_message_id, reply_markup=reply_markup)
                else:
                    self.api.answer_callback_query(callback_id)
        except:
            self.__logger.error('An error ocurred in callback_listener', exc_info=1)

    def stop_bot(self):
            try:
                self.api.stop_polling()
            except AttributeError:
                return

    def start_bot(self):
        self.auth()

    def __del__(self):
        self.stop_bot()