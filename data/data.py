import yaml
import json

from google.genai.types import Content, Part

from config import config


def fetch():
    with open(config.get("data")):
        data = yaml.load(open(config.get("data")), Loader=yaml.SafeLoader)

    return data


def write(data: dict):
    with open(config.get("data"), 'w') as f:
        yaml.dump(data, f)


def get_chat_history(chat_id: int):
    chat_id = str(chat_id)
    with open(config.get("chats_history")) as f:
        chats: dict = json.load(f)

    history: list[Content] = []

    for interaction in chats.get(chat_id, []):
        for role, text in zip(('user', 'model'), interaction):
            if not text:
                continue
            history.append(
                Content(
                    parts=[Part(text=text)],
                    role=role
                )
            )

    return history


def write_chat_history(chat_id: int, data: tuple[str, str]):
    chat_id = str(chat_id)
    with open(config.get("chats_history"), 'r') as f:
        chats: dict = json.load(f)

    if chat_id not in chats:
        chats[chat_id] = []
    chats[chat_id].append(data)

    with open(config.get("chats_history"), 'w') as f:
        # noinspection PyTypeChecker
        json.dump(chats, f, ensure_ascii=False, indent=2)
