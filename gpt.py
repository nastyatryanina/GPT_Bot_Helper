import requests, logging
from transformers import AutoTokenizer

import database
from config import MODEL, GPT_LOCAL_URL, HEADERS, MAX_TOKENS
tokenizer = AutoTokenizer.from_pretrained(MODEL)

logging.basicConfig(
    level = logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    filename="log_file.txt",
    filemode="w"
)
promt_for_level = {
    "Junior": "Объсняй каждую строку очень подробно как начинающему программисту.",
    "Middle": "Приводи примеры кода с краткими пояснениями как человеку, который знает как программировать",
    "Senior": "Объясняй как человеку, который очень хорошо знает синтаксис, используй профессиональные термины.",
}
def count_tokens(user_request):
    tokens = tokenizer.encode(user_request)
    return len(tokens)

def is_current(user_request):
    if count_tokens(user_request) <= MAX_TOKENS:
        return True
    else:
        return False
def make_promt(user_id):
    lang = database.is_value_in_table(user_id, "lang")
    level = database.is_value_in_table(user_id, "level")
    system_mеssage = f"Ты дружелюбный помощник для ответа на вопросы про {lang}. Давай подробный ответ на русском языке и приводи примеры кода, испльзую синтаксис {lang}. {promt_for_level[level]}"
    json = {
        "messages": [
            {
                "role": "user",
                "content": database.is_value_in_table(user_id, "task")
            },
            {
                "role": "system",
                "content": system_mеssage
            },
            {
                "role": "assistant",
                "content": database.is_value_in_table(user_id, "answer")
            }
        ],
        "temperature": 1.2,
        "max_tokens": 25,
    }
    return json

def get_response(user_id):
    promt = make_promt(user_id)
    try:
        response = requests.post(url = GPT_LOCAL_URL, headers = HEADERS, json=promt)
        content = response.json()['choices'][0]['message']['content']
        return [True, content]
    except Exception as err:
        logging.error(err)
        return [False]
