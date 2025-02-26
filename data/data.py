from base64 import b64decode

import yaml
import json

from google.genai.types import Content, Part

from config import config


def fetch():
    with open(config.get("data"), encoding='utf-8') as f:
        data = yaml.load(f, Loader=yaml.SafeLoader)

    return data


def write(data: dict):
    with open(config.get("data"), 'w', encoding='utf-8') as f:
        yaml.dump(data, f)


def get_chat_history(chat_id: int):
    chat_id = str(chat_id)
    with open(config.get("chats_history"), encoding='utf-8') as f:
        chats: dict = json.load(f)

    history: list[Content] = []

    for interaction in chats.get(chat_id, []):
        for role, content in zip(('user', 'model'), interaction):
            if not content:
                continue

            parts = [Part(text=content[0])]
            if len(content) > 1:
                parts.append(Part.from_bytes(data=b64decode(content[1]), mime_type='image/jpeg'))
            history.append(
                Content(
                    parts=parts,
                    role=role
                )
            )

    return history


def write_chat_history(chat_id: int, data: list[list[str]]):
    chat_id = str(chat_id)
    with open(config.get("chats_history"), 'r', encoding='utf-8') as f:
        chats: dict = json.load(f)

    if chat_id not in chats:
        chats[chat_id] = []
    chats[chat_id].append(data)

    with open(config.get("chats_history"), 'w', encoding='utf-8') as f:
        # noinspection PyTypeChecker
        json.dump(chats, f, ensure_ascii=False, indent=2)
