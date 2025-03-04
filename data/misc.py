import os

# noinspection PyPackageRequirements
from google.genai import Client
# noinspection PyPackageRequirements
from google.genai.chats import Chat
# noinspection PyPackageRequirements
from google.genai.types import GenerateContentConfig

import config
from const import CHAT_SYS_INST, CHAT_PATH, CHAT_HISTORY
from data import settings, history
from shared import file_locks


async def create_chat(chat_id: int) -> Chat:
    await touch_file_structure(chat_id)
    client = Client(api_key=await settings.get_api_key(chat_id))

    return client.chats.create(
        model=config.get("genai_model"),
        config=GenerateContentConfig(
            temperature=1.5,
            system_instruction=await get_sys_inst(chat_id),
            safety_settings=await settings.get_safety_settings(chat_id)
        ),
        history=await history.get_chat_history(chat_id)
    )


async def touch_file_structure(chat_id: int | str):
    async with file_locks.get_lock(chat_id):
        os.makedirs(CHAT_PATH.format(chat_id), exist_ok=True)

        for filepath in (CHAT_HISTORY, CHAT_SYS_INST):
            open(filepath.format(chat_id), 'a').close()

    await settings.get(chat_id)


async def get_sys_inst(chat_id: int):
    sys_inst: str = ''

    if not (await (settings.get(chat_id)))["override_sys"]:
        with open(config.get("base_sys_inst"), encoding="utf-8") as f:
            sys_inst = f.read() + '\n\n'

    async with file_locks.get_lock(chat_id):
        with open(CHAT_SYS_INST.format(chat_id), encoding='utf-8') as f:
            sys_inst += f.read()

    return sys_inst
