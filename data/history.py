import json
from base64 import b64decode

# noinspection PyPackageRequirements
from google.genai.types import Content, Part

from const import CHAT_HISTORY
from data.misc import touch_file_structure
from shared import locks


async def get_chat_history(chat_id: int):
    await touch_file_structure(chat_id)
    history: list[Content] = []

    async with locks.get_lock(chat_id):
        with open(CHAT_HISTORY.format(chat_id), encoding='utf-8') as f:
            for interaction in f.readlines():
                interaction = json.loads(interaction)
                for role, content in zip(('user', 'model'), interaction):
                    if not content:
                        continue

                    parts = [Part(text=content[0])]
                    if len(content) > 1:
                        parts.append(Part.from_bytes(data=b64decode(content[1]), mime_type='image/jpeg'))
                    history.append(
                        Content(
                            parts=parts,  # TODO: This is awful, really needs a fix
                            role=role
                        )
                    )

    return history


async def write_chat_history(chat_id: int, data: list[list[str]]):
    async with locks.get_lock(chat_id):
        with open(CHAT_HISTORY.format(chat_id), 'a', encoding='utf-8') as f:
            print(json.dumps(data, ensure_ascii=False), flush=True, file=f)
