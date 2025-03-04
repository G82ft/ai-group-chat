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
from shared import chats, config as conf, file_locks
from utils import format_input

cmd = Router(name='cmd')

#                 from_chat, to_chat | user_turn | messages
added_chat_context: dict[int, list[str | bool | list[list[list[str]]]]] = {}
add_ctxt_lock = Lock()


@cmd.message(CommandStart())
async def start(msg: Message):
    print(msg.from_user.first_name, msg.text)
    settings_ = await settings.get(msg.chat.id)
    print(settings_)

    msg = msg.reply_to_message or msg

    await msg.bot.send_message(
        msg.chat.id,
        f'User ID: {msg.from_user.id}\n'
        f'Is admin: {await is_admin(msg)}\n'
        f'Chat ID: {msg.chat.id}\n'
        f'Chat enabled: {settings_["enabled"]}\n'
        f'Image recognition: {settings_["image_recognition"]}\n'
        f'Override system instructions: {settings_["override_sys"]}\n'
    )


@cmd.message(Command('set_setting'))
async def set_setting(msg: Message):
    if text := await validate_cmd(msg, chat_arg=True, args_len=2):
        return await msg.reply(text)

    _, chat_id, args = parse_args(msg, chat_arg=True)
    key, value = args

    match key:
        case "enabled" | "override_sys":
            success = await settings.set_setting(chat_id, key, value.lower() in TRUE_LITERALS, await is_admin(msg))
        case "api_key" | "image_recognition":
            success = await settings.set_setting(chat_id, key, value, await is_admin(msg))
        case _:
            success = False

    await msg.bot.send_message(
        msg.chat.id,
        success and f"Setting '{key}' updated successfully." or f"Invalid value provided for '{key}'.",
    )
    await msg.delete()


@cmd.message(Command('get_settings_info'))
async def get_settings_info(msg: Message):
    result: str = ''
    values_key = (await is_admin(msg)) and 'admin_values' or 'values'

    for setting, info in SETTINGS_INFO.items():
        result += (
            f"\n{setting}:\n"
            f"Type: <{info["type"].__name__}>\n"
        )
        if info["type"] == bool:
            result += (
                f'Available values: '
                f'{', '.join(TRUE_LITERALS)}. Other values are considered false.\n'
            )
            continue
        elif values_key not in info:
            continue

        result += f"Available values: {", ".join(info[values_key])}.\n"

    await msg.reply(result)


@cmd.message(Command('add_chat_context'))
async def add_chat_context(msg: Message):
    if text := await validate_cmd(msg, chat_arg=True, dm=True):
        return await msg.bot.send_message(msg.chat.id, text)

    await msg.reply_document(
        FSInputFile(config.get("chats_history"), f'{config.get("chats_history").split('/')[-1]}.bak'),
        caption='Forward/send messages. Odd messages are from users, even are from model.\n\n'
        # TODO: mention admin
                '<b>WARNING: Photos will be added to the context only if "image_recognition" is set to "yes".</b>',
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

        if msg.photo and (await settings.get(added_chat_context[msg.chat.id][0]))["image_recognition"] == "yes":
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


@cmd.message(Command('stop_add_context'))
async def stop_add_context(msg: Message):
    if msg.chat.id not in added_chat_context:
        return await msg.reply('You have not started adding context yet.')

    context = added_chat_context[msg.chat.id][-1]
    bot_msg: Message = await msg.reply('Finished receiving messages. Adding context...')

    if not added_chat_context[msg.chat.id][1]:
        context = context[:-1]
        bot_msg = await bot_msg.edit_text(f'{bot_msg.text}\nLast message is removed, because it was sent from a user.')

    for interaction in context:
        await history.write_chat_history(added_chat_context[msg.chat.id][0], interaction)

    await bot_msg.edit_text(f'{bot_msg.text}\nContext added to chat {added_chat_context[msg.chat.id][0]}.')

    del added_chat_context[msg.chat.id]


@cmd.message(Command('reload_chat'))
async def reload_chat(msg: Message):
    if text := await validate_cmd(msg, chat_arg=True):
        return await msg.reply(text)

    if msg.chat.id not in chats:
        return await msg.reply(f'Chat {msg.chat.id} was not cached.')

    del chats[msg.chat.id]
    await msg.reply(
        f'Chat {msg.chat.id} and system instructions reloaded.\n'
    )


@cmd.message(Command('reload_config'))
async def reload_config(msg: Message):
    if text := await validate_cmd(msg, chat_arg=True):
        return await msg.reply(text)

    conf.clear()
    await msg.reply(
        f'Config reloaded.\n'
    )


@cmd.message(Command('get_sys_inst'))
async def get_sys_inst(msg: Message):
    if text := await validate_cmd(msg, chat_arg=True, dm=True):
        return await msg.bot.send_message(msg.chat.id, text)

    chat_id: int = parse_args(msg, chat_arg=True)[1]

    await msg.reply_document(FSInputFile(CHAT_SYS_INST.format(chat_id)))


@cmd.message(Command('set_sys_inst'))
async def set_sys_inst(msg: Message):
    if text := await validate_cmd(msg, chat_arg=True, dm=True):
        return await msg.bot.send_message(msg.chat.id, text)

    if not msg.document:
        await msg.reply('You need to provide a file with system instructions.')

    chat = msg.caption.split()[1]
    chat_sys_inst_path: str = CHAT_SYS_INST.format(chat)

    async with file_locks.get_lock(msg.chat.id):
        await msg.reply_document(
            FSInputFile(chat_sys_inst_path, f'{chat_sys_inst_path}.bak'),
            caption='System instructions backup. Writing new instructions...',
        )

    async with file_locks.get_lock(msg.chat.id):
        with open(chat_sys_inst_path, 'wb') as f:
            await msg.bot.download_file((await msg.bot.get_file(msg.document.file_id)).file_path, f)

    await msg.reply(f'System instructions changed for {chat}.')


def parse_args(msg: Message, chat_arg: bool = False) -> tuple[str, int, list[str]]:
    text = msg.text or msg.caption
    args = text.split()
    command = args.pop(0)

    chat_id: int = msg.chat.id
    if chat_arg and args and msg.from_user.id == chat_id:
        chat_id = int(args.pop(0))

    return command, chat_id, args


async def validate_cmd(msg: Message, *, chat_arg: bool = False, args_len: int = 0, dm: bool = False) -> str | None:
    command, chat_id, args = parse_args(msg, chat_arg)

    if len(args) < args_len:
        return f'{command} requires {args_len} arguments.'

    if not await is_admin(msg, chat_id):
        return 'You are not an admin of this chat.'

    if dm and msg.from_user.id != msg.chat.id:
        await msg.delete()
        return 'You must use this command in DM with the bot.'


async def is_admin(msg: Message, chat_id: int = None) -> bool:
    if chat_id is None:
        chat_id = msg.chat.id

    if msg.from_user.id in config.get("admins"):
        return True

    return (
            isinstance(await msg.bot.get_chat_member(chat_id, msg.from_user.id), ADMINS)
            and (await settings.get(chat_id))["api_key"])
