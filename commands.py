import io
from asyncio import Lock
from base64 import b64encode

from aiogram import Router
from aiogram.enums import ParseMode
from aiogram.filters import CommandStart, Command
from aiogram.types import Message, FSInputFile
from aiogram.utils.chat_member import ADMINS

import config
from const import SETTINGS_INFO, TRUE_LITERALS, CHAT_SYS_INST
from data import history, settings
from shared import chats, config as conf, locks
from utils import format_input

cmd = Router(name='cmd')

#                 from_chat, to_chat | user_turn | messages
added_chat_context: dict[int, list[str | bool | list[list[list[str]]]]] = {}
add_ctxt_lock = Lock()


@cmd.message(CommandStart())
async def start(msg: Message):
    settings_ = await settings.get(msg.chat.id)

    msg = msg.reply_to_message or msg

    await msg.bot.send_message(
        msg.chat.id,
        f'User ID: {msg.from_user.id}\n'
        f'Is admin: {is_admin(msg)}\n'
        f'Chat ID: {msg.chat.id}\n'
        f'Chat enabled: {settings_["enabled"]}\n'
        f'Image recognition: {settings_["image_recognition"]}\n'
        f'Override system instructions: {settings_["override_sys"]}\n'
    )


@cmd.message(Command('set_setting'))
async def set_setting(msg: Message):
    if not await is_admin(msg):
        await msg.reply(f'You are not an admin.', show_alert=True)

    chat_id, key, value = msg.text.removeprefix('/set_setting').split()

    match key:
        case "enabled" | "override_sys":
            success = await settings.set_setting(int(chat_id), key, value.lower() in TRUE_LITERALS)
        case "api_key" | "image_recognition":
            success = await settings.set_setting(int(chat_id), key, value)
        case _:
            success = False

    await msg.reply(
        success and f"Setting '{key}' updated successfully." or f"Invalid value provided for '{key}'.",
    )
    await msg.delete()


@cmd.message(Command('get_settings_info'))
async def get_settings_info(msg: Message):
    result: str = ''
    values_key = (await is_admin(msg)) and 'admin_values' or 'values'

    for setting, info in SETTINGS_INFO.items():
        result += (
            f"\n'{setting}':\n"
            f"Type: '{info["type"]}'\n"
        )
        if info["type"] == bool:
            result += (
                f'Available values: '
                f'{', '.join(TRUE_LITERALS)}. Other values are considered false.\n'
            )
            continue
        elif values_key not in info:
            continue

        result += f"Available values: '{"', '".join(info[values_key])}'.\n'"


@cmd.message(Command('add_chat_context'))
async def add_chat_context(msg: Message):
    if not await is_admin(msg):
        return

    if msg.from_user.id != msg.chat.id:
        await msg.reply('You must use this command in DM with the bot.')
        return

    if msg.chat.id in added_chat_context:
        await stop_context(msg)
        return

    if len(msg.text.split()) < 2:
        await msg.reply('You need to specify chat ID as an argument.')
        return

    await msg.reply_document(
        FSInputFile(config.get("chats_history"), f'{config.get("chats_history").split('/')[-1]}.bak'),
        caption='Forward/send messages. Odd messages are from users, even are from the model.\n\n'
                '<b>WARNING: All users are considered admins and all photos will be added to the context!</b>',
        parse_mode=ParseMode.HTML
    )

    added_chat_context[msg.chat.id] = [
        msg.text.split()[-1], True, []
    ]


@cmd.message(lambda m: m.from_user.id == m.chat.id and m.chat.id in added_chat_context)
async def handle_add_chat_context(msg: Message):
    await add_ctxt_lock.acquire()
    user: str = msg.from_user.first_name
    if msg.forward_origin is not None:
        user = (
                hasattr(msg.forward_origin, 'sender_user')
                and msg.forward_origin.sender_user.first_name
                or msg.forward_origin.sender_user_name)

    if added_chat_context[msg.chat.id][1]:
        contents = [format_input(msg.text or msg.caption or '<empty>', user, True)]

        if msg.photo:
            image_file = io.BytesIO()
            await msg.bot.download_file((await msg.bot.get_file(msg.photo[0].file_id)).file_path, image_file)
            contents.append(b64encode(image_file.getvalue()).decode('ascii'))

        added_chat_context[msg.chat.id][-1].append(
            [
                contents
            ]
        )
    else:
        added_chat_context[msg.chat.id][-1][-1].append([msg.text])
    added_chat_context[msg.chat.id][1] = not added_chat_context[msg.chat.id][1]
    add_ctxt_lock.release()


@cmd.message(Command('reload_chat'))
async def reload_chat(msg: Message):
    if not await is_admin(msg):
        return

    del chats[msg.chat.id]
    await msg.reply(
        f'Chat {msg.chat.id} and system instructions reloaded.\n'
    )


@cmd.message(Command('reload_config'))
async def reload_config(msg: Message):
    if not await is_admin(msg):
        return

    conf.clear()
    await msg.reply(
        f'Config reloaded.\n'
    )


@cmd.message(Command('get_sys_inst'))
async def get_sys_inst(msg: Message):
    if (text := await validate_cmd(msg)) is not None:
        if text:
            # noinspection PyTypeChecker
            await msg.reply(text)
        return

    chat = msg.text.split()[1]

    await msg.reply_document(FSInputFile(CHAT_SYS_INST.format(chat)))


@cmd.message(Command('set_sys_inst'))
async def set_sys_inst(msg: Message):
    if (text := await validate_cmd(msg)) is not None:
        if text:
            # noinspection PyTypeChecker
            await msg.reply(text)
        return

    chat = msg.caption.split()[1]

    if not msg.document:
        await msg.reply('You need to provide a file with system instructions.')

    chat_sys_inst_path: str = CHAT_SYS_INST.format(chat)

    async with locks.get_lock(msg.chat.id):
        await msg.reply_document(
            FSInputFile(chat_sys_inst_path, f'{chat_sys_inst_path}.bak'),
            caption='System instructions backup. Writing new instructions...',
        )

    async with locks.get_lock(msg.chat.id):
        with open(chat_sys_inst_path, 'wb') as f:
            await msg.bot.download_file((await msg.bot.get_file(msg.document.file_id)).file_path, f)

    await msg.reply(f'System instructions changed for {chat}.')


async def stop_context(msg: Message):
    context = added_chat_context[msg.chat.id][-1]
    bot_msg: Message = await msg.reply('Finished receiving messages. Adding context...')

    if not added_chat_context[msg.chat.id][1]:
        context = context[:-1]
        bot_msg = await bot_msg.edit_text(f'{bot_msg.text}\nLast message is removed, because it was sent from a user.')

    for interaction in context:
        await history.write_chat_history(added_chat_context[msg.chat.id][0], interaction)

    await bot_msg.edit_text(f'{bot_msg.text}\nContext added to chat {added_chat_context[msg.chat.id][0]}.')

    del added_chat_context[msg.chat.id]


async def validate_cmd(msg: Message) -> str | None:
    text = msg.text or msg.caption
    if not await is_admin(msg):
        return ''

    if msg.from_user.id != msg.chat.id:
        return 'You must use this command in DM with the bot.'

    if len(text.split()) < 2:
        return 'You need to specify chat ID as an argument.'


async def is_admin(msg: Message) -> bool:
    if msg.from_user.id in config.get("admins"):
        return True

    return (
            isinstance(await msg.bot.get_chat_member(msg.chat.id, msg.from_user.id), ADMINS)
            and (await settings.get(msg.chat.id))["api_key"])
