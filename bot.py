from secret_info import TOKEN
import database
import gpt, telebot, logging
bot = telebot.TeleBot(TOKEN)

logging.basicConfig(
    level = logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    filename="log_file.txt",
    filemode="w"
)
help_message = ("Я бот-помощник по python. Вначале выбери язык программирования(/set_lang) и уровень сложности(/set_level).\n"
                "Задавай мне вопросы(/solve_task), а нейросеть будет отвечать на них.\n"
                "Также можешь попросить ее продолжить объснение(/continue).\n"
                "Есть скрытый режим debug(/debug), который будет высылать файл с логами возникших ошибок.")
users_history = {}
langs = ["Python", "C++", "Java Script", "SQL"]
levels = ["Junior", "Middle", "Senior"]
def create_keyboard(buttons_list):
    keyboard = telebot.types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True, one_time_keyboard=True)
    keyboard.add(*buttons_list)
    return keyboard


@bot.message_handler(commands=['start'])
def start(message):
    user_id = message.from_user.id
    logging.info("Новый пользователь")
    bot.send_message(user_id, f"Привет {message.from_user.first_name}, я бот-помощник по программированию, использующий нейросеть для ответов. Чтобы понять, как ей пользоваться, нажми /help",
                     reply_markup=create_keyboard(['/help']))


@bot.message_handler(commands=['help'])
def support(message):
    bot.send_message(message.from_user.id,
                     text=help_message,
                     reply_markup=create_keyboard(["/solve_task", "/set_level", "/set_lang"]))

@bot.message_handler(commands=['set_lang'])
def set_lang(message):
    bot.send_message(message.from_user.id,
                     text = "Выбери язык программирования, по которому возникли вопросы",
                     reply_markup = create_keyboard(langs))
    bot.register_next_step_handler(message,get_lang)


def get_lang(message):
    database.update_row_value(message.chat.id, "lang", message.text)
    database.update_row_value(message.chat.id, "task", "NULL")
    database.update_row_value(message.chat.id, "answer", "NULL")
    database.show_table()
    return


@bot.message_handler(commands=['set_level'])
def set_level(message):
    bot.send_message(message.from_user.id,
                     text="Нейросеть будет отвечать тебе, считая что твои скиллы в программировании на уровне: ",
                     reply_markup=create_keyboard(levels))
    bot.register_next_step_handler(message, get_level)


def get_level(message):
    database.update_row_value(message.chat.id, column_name="level", new_value=message.text)
    database.show_table()
    return

@bot.message_handler(commands=['solve_task'])
def solve_task(message):
    bot.send_message(message.from_user.id, "Введи любое сообщение. Оно будет распознано как новое задание. Если до этого было какое-то незавершенное задание, то оно будет завершено."
                                           "\nМожешь попросить продолжить решение, нажав continue или начать новое, нажав solve_task")
    bot.register_next_step_handler(message, add_task)


def check(message):
    user_id = message.from_user.id
    if not database.is_value_in_table(user_id, "task"):
        bot.send_message(user_id, "Добавь задание (/solve_task)")
        logging.warning(f"У пользователя с id {user_id} не добавлено задание")
        return False
        #bot.register_next_step_handler(message, solve_task, reply_markup=create_keyboard(["/solve_task"]))
    if database.is_value_in_table(user_id, "lang") not in langs:
        bot.send_message(user_id, "Выбери язык программирования (/set_lang)")
        logging.warning(f"У пользователя с id {user_id} не добавлено задание")
        return False
    if database.is_value_in_table(user_id, "level") not in levels:
        bot.send_message(user_id, "Выбери уровень (/set_level)")
        logging.warning(f"У пользователя с id {user_id} не добавлено задание")
        return False
        #bot.register_next_step_handler(message, set_level, reply_markup=create_keyboard(["/set_level"]))
    return True

def add_task(message):
    user_id = message.from_user.id
    if message.content_type != "text":
        bot.send_message(user_id, "Необходимо отправить именно текстовое сообщение")
        bot.register_next_step_handler(message, solve_task)
        return
    if database.is_value_in_table(user_id, "task"):
        bot.send_message(user_id, "Решение предыдущей задачи завершено. Язык и уровень остались прежними.")
    database.update_row_value(user_id, "answer", "Реши задачу по шагам: ")
    user_request = message.text
    if gpt.is_current(user_request):
        database.update_row_value(user_id, "task", user_request)
        if check(message):
            bot.send_message(user_id, "Новая задача добавлена и нейросети скоро тебе ответит!")
            database.show_table()
            continue_solve(message)
    else:
        bot.send_message(user_id, "Запрос превышает количество символов\nИсправь запрос")
        bot.register_next_step_handler(message, solve_task)

@bot.message_handler(commands = ["continue"])
def continue_solve(message):
    user_id = message.from_user.id
    if check(message):
        logging.info("Запрос к нейросети")
        response = gpt.get_response(user_id)
        if response[0]:
             if response[1] == "":
                 bot.send_message(user_id, "Нейросеть закончила объяснение.")
                 solve_task(message)
             else:
                 answer = database.is_value_in_table(user_id, "answer")
                 answer += response[1]
                 database.update_row_value(user_id, "answer", answer)
                 bot.send_message(user_id, f"<i>{response[1]}</i>",
                                     reply_markup=create_keyboard(["/continue", "/solve_task", "/set_level"]), parse_mode="HTML")

        else:
             bot.send_message(user_id,
                              "Произошла ошибка. Чтобы понять, в чем причина перейди в режим debug или заверши запрос",
                              reply_markup=create_keyboard(["/debug", "/solve_task"]))
    database.show_table()


@bot.message_handler(commands = ["debug"])
def debug(message):
    user_id = message.from_user.id
    logging.info("Режим дебаг")
    with open("log_file.txt", "rb") as f:
        bot.send_document(user_id, f)


@bot.message_handler(commands = ["statistics"])
def statistics(message):
    user_id = message.from_user.id
    answer = "Вот сколько пользователей задало вопрос по каждому языку: \n"
    logging.info("Вывод статистики")
    res = database.show_column("lang")
    cnt = {lang: 0 for lang in langs}
    for row in res:
        cnt[row[0]] += 1
    cnt = sorted(cnt.items(), key=lambda item: item[1], reverse = True)
    for i in cnt:
        answer += f"{i[0]}:    {i[1]} \n"
    bot.send_message(user_id, answer)


if __name__ == "__main__":
    logging.info("Бот запущен")
    bot.infinity_polling()