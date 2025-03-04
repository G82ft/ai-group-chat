import os
import json

# noinspection PyPackageRequirements
from google.genai.types import SafetySetting, HarmCategory, HarmBlockThreshold

import config
from const import CHAT_SETTINGS, SETTINGS_VALIDATION, DEFAULT_SETTINGS, CHAT_PATH, SETTINGS_INFO
from shared import file_locks


async def get(chat_id: int) -> dict:
    settings: dict = {}
    chat_settings = CHAT_SETTINGS.format(chat_id)

    if not os.path.exists(chat_settings):
        settings = await create_default_settings(chat_id)

    if not settings:
        async with file_locks.get_lock(chat_id):
            with open(chat_settings, 'r', encoding='utf-8') as f:
                settings = json.load(f)

    return settings


async def get_safety_settings(chat_id: int) -> list[SafetySetting]:
    safety_json: dict = (await get(chat_id))["safety"]
    result: list[SafetySetting] = []

    for category, threshold in safety_json.items():
        # noinspection PyTypeChecker
        result.append(SafetySetting(
            category=HarmCategory[category],
            threshold=HarmBlockThreshold[threshold]
        ))

    return result


async def set_setting(chat_id: int, setting: str, value: any, is_admin: bool = False) -> bool:
    settings = await get(chat_id)

    if not validate(setting, value, is_admin):
        return False

    settings[setting] = value

    async with file_locks.get_lock(chat_id):
        with open(CHAT_SETTINGS.format(chat_id), 'w', encoding='utf-8') as f:
            # noinspection PyTypeChecker
            json.dump(settings, f, ensure_ascii=False, indent=4)

    return True


def validate(setting: str, value: any, is_admin: bool) -> bool:
    if setting not in SETTINGS_INFO:
        return False
    if setting not in SETTINGS_VALIDATION:
        return True

    validation = SETTINGS_VALIDATION[setting]

    if not isinstance(value, SETTINGS_INFO[setting]["type"]):
        return False

    return is_admin and validation["admin_validate"](value) or validation["validate"](value)


async def create_default_settings(chat_id: int) -> dict:
    async with file_locks.get_lock(chat_id):
        os.makedirs(CHAT_PATH.format(chat_id), exist_ok=True)

        with open(CHAT_SETTINGS.format(chat_id), 'w', encoding='utf-8') as f:
            # noinspection PyTypeChecker
            json.dump(DEFAULT_SETTINGS, f, ensure_ascii=False, indent=2)

    return DEFAULT_SETTINGS


async def get_api_key(chat_id: int) -> str:
    return (await get(chat_id))["api_key"] or config.get("base_genai_token")
