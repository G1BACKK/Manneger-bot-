from telegram import Update
from telegram.ext import Application, ChatJoinRequestHandler, ContextTypes

class BotInstance:
    def __init__(self, token, greeting):
        self.token = token
        self.greeting = greeting
        self.app = Application.builder().token(token).build()

    async def greet_user(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        chat_id = update.chat_join_request.chat.id
        user_id = update.chat_join_request.from_user.id
        # Accept request
        await context.bot.approve_chat_join_request(chat_id, user_id)
        # Send greeting
        await context.bot.send_message(chat_id=user_id, text=self.greeting)

    def start(self):
        self.app.add_handler(ChatJoinRequestHandler(self.greet_user))
        return self.app
