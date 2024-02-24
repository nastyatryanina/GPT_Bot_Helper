import requests, logging
from transformers import AutoTokenizer
from config import MODEL, GPT_LOCAL_URL, HEADERS, MAX_TOKENS
tokenizer = AutoTokenizer.from_pretrained(MODEL)

logging.basicConfig(
    level = logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    filename="log_file.txt",
    filemode="w"
)
def count_tokens(user_request):
    tokens = tokenizer.encode(user_request)
    return len(tokens)

def is_current(user_request):
    if count_tokens(user_request) <= MAX_TOKENS:
        return True
    else:
        return False
def make_promt(user_request):
    system_mеssage = "Ты дружелюбный помощник для ответа на вопросы про Python. Давай подробный ответ на русском языке и приводи примеры кода"
    json = {
        "messages": [
            {
                "role": "user",
                "content": user_request['user_content']
            },
            {
                "role": "system",
                "content": system_mеssage
            },
            {
                "role": "assistant",
                "content": user_request['assistant_content']
            }
        ],
        "temperature": 1.2,
        "max_tokens": 25,
    }
    return json

def get_response(user_request):
    promt = make_promt(user_request)
    try:
        response = requests.post(url = GPT_LOCAL_URL, headers = HEADERS, json=promt)
        content = response.json()['choices'][0]['message']['content']
        return [True, content]
    except Exception as err:
        logging.error(err)
        return [False]
