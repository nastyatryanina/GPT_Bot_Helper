from secret_info import TOKEN
import gpt, telebot, logging
bot = telebot.TeleBot(TOKEN)

logging.basicConfig(
    level = logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    filename="log_file.txt",
    filemode="w"
)
help_message = ("Я бот-помощник по python. Задавай мне вопросы(/solve_task), а нейросеть будет отвечать на них.\n"
                "Также можешь попросить ее продолжить объснение(/continue).\n"
                "Есть скрытый режим debug(/debug), который будет высылать файл с логами возникших ошибок.")
users_history = {}
def create_keyboard(buttons_list):
    keyboard = telebot.types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True, one_time_keyboard=True)
    keyboard.add(*buttons_list)
    return keyboard


@bot.message_handler(commands=['start'])
def start(message):
    logging.info("Новый пользователь")
    bot.send_message(message.chat.id, f"Привет {message.from_user.first_name}, я бот-помощник для работы с Python, использующий нейросеть для ответов. Чтобы понять, как ей пользоваться, нажми /help",
                     reply_markup=create_keyboard(['/help']))


@bot.message_handler(commands=['help'])
def support(message):
    bot.send_message(message.from_user.id,
                     text=help_message,
                     reply_markup=create_keyboard(["/solve_task"]))

@bot.message_handler(commands=['solve_task'])
def solve_task(message):
    bot.send_message(message.from_user.id, "Введи любое сообщение. Оно будет распознано как новое задание. Если до этого было какое-то незавершенное задание, то оно будет завершено."
                                           "\nМожешь попросить продолжить решение, нажав continue или начать новое, нажав solve_task")
    bot.register_next_step_handler(message, add_task)

def add_task(message):
    user_id = message.from_user.id
    if message.content_type != "text":
        bot.send_message(user_id, "Необходимо отправить именно текстовое сообщение")
        bot.register_next_step_handler(message, solve_task)
        return
    users_history[user_id] = {}
    if user_id in users_history and users_history[user_id] != {}:
        bot.send_message(user_id, "Решение предыдущей задачи завершено.")
    user_request = message.text
    if gpt.is_current(user_request):
        users_history[user_id] = {
            'user_content': user_request,
            'assistant_content': "Решим задачу по шагам: "
        }
        bot.send_message(user_id, "Новая задача добавлена и нейросети скоро тебе ответит!")
        continue_solve(message)
    else:
        bot.send_message(user_id, "Запрос превышает количество символов\nИсправь запрос")
        bot.register_next_step_handler(message, solve_task)
@bot.message_handler(commands = ["continue"])
def continue_solve(message):
    user_id = message.from_user.id
    if user_id not in users_history or users_history[user_id] == {}:
        bot.send_message(user_id, "Пока что у тебя нет начатых заданий.")
        bot.register_next_step_handler(message, solve_task)
        return
    logging.info("Запрос к нейросети")
    response = gpt.get_response(users_history[user_id])
    if response[0]:
        if response[1] == "":
            bot.send_message(user_id, "Нейросеть закончила объяснение.")
            solve_task(message)
        else:
            users_history[user_id]['assistant_content'] += response[1]
            bot.send_message(user_id, f"<i>{response[1]}</i>",
                             reply_markup=create_keyboard(["/continue", "/solve_task"]), parse_mode="HTML")
    else:
        bot.send_message(user_id,
                         "Произошла ошибка. Чтобы понять, в чем причина перейди в режим debug или заверши запрос",
                         reply_markup=create_keyboard(["/debug", "/solve_task"]))


@bot.message_handler(commands = ["debug"])
def debug(message):
    user_id = message.from_user.id
    logging.info("Режим дебаг")
    with open("log_file.txt", "rb") as f:
        bot.send_document(user_id, f)

if __name__ == "__main__":
    logging.info("Бот запущен")
    bot.infinity_polling()