import os.path
from asyncio import Lock
import io
from base64 import b64encode

from aiogram import Router
from aiogram.enums import ParseMode
from aiogram.filters import CommandStart, Command
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery, FSInputFile

import config
import data
from shared import chats, config as conf
from utils import format_input

cmd = Router(name='cmd')

added_chat_context: dict[int, list[str | bool | list[list[list[str]]]]] = {}
add_ctxt_lock = Lock()


# -------------------------- chat_id | is_user_turn | messages


@cmd.message(CommandStart())
async def start(msg: Message):
    data_ = data.fetch()

    msg = msg.reply_to_message or msg

    is_admin: bool = msg.from_user.id in data_["admins"]

    await msg.bot.send_message(
        msg.chat.id,
        f'Chat ID: {msg.chat.id}\n'
        f'Is enabled: {msg.chat.id in data_["chats"]}\n'
        f'User ID: {msg.from_user.id}\n'
        f'Is admin: {is_admin}',
        reply_markup=get_actions(msg, data_)
    )


@cmd.callback_query(lambda c: c.data.startswith('data:'))
async def admin(cq: CallbackQuery):
    data_ = data.fetch()

    if cq.from_user.id not in data_["admins"]:
        await cq.answer(f'You are not an admin.', show_alert=True)

    key, action, value = cq.data.removeprefix('data:').split(':')
    value = int(value)

    match action:
        case 'add':
            data_[f'{key}s'].append(value)
        case 'remov':
            if len(data_[f'{key}s']) == 1:
                await cq.answer(f'You cannot remove the last {key}.', show_alert=True)
                return
            data_[f'{key}s'].remove(value)

    data.write(data_)
    await cq.message.edit_text(f'{key.capitalize()} {action}ed successfully.')


@cmd.message(Command('add_chat_context'))
async def add_chat_context(msg: Message):
    if msg.from_user.id not in data.fetch()["admins"]:
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
async def add_chat_context(msg: Message):
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
    if msg.from_user.id not in data.fetch()["admins"]:
        return

    del chats[msg.chat.id]
    await msg.reply(
        f'Chat {msg.chat.id} and system instructions reloaded.\n'
    )


@cmd.message(Command('reload_config'))
async def reload_config(msg: Message):
    if msg.from_user.id not in data.fetch()["admins"]:
        return

    conf.clear()
    await msg.reply(
        f'Config reloaded.\n'
    )


@cmd.message(Command('get_sys_inst'))
async def get_sys_inst(msg: Message):
    if msg.from_user.id not in data.fetch()["admins"]:
        return

    if msg.from_user.id != msg.chat.id:
        await msg.reply('You must use this command in DM with the bot.')
        return

    if len(msg.text.split()) < 2:
        await msg.reply('You need to specify chat ID as an argument.')
        return

    chat = msg.text.split()[1]

    print(os.path.exists(f'{config.get("chats_sys_inst")}{chat}.txt'), f'{config.get("chats_sys_inst")}{chat}.txt')
    await msg.reply_document(FSInputFile(f'{config.get("chats_sys_inst")}{chat}.txt'))


@cmd.message(Command('post_sys_inst'))
async def post_sys_inst(msg: Message):
    if msg.from_user.id not in data.fetch()["admins"]:
        return

    if msg.from_user.id != msg.chat.id:
        await msg.reply('You must use this command in DM with the bot.')
        return

    if len(msg.caption.split()) < 2:
        await msg.reply('You need to specify chat ID as an argument.')
        return

    chat = msg.caption.split()[1]

    if not msg.document:
        await msg.reply('You need to provide a file with system instructions.')

    chat_sys_inst_path: str = f'{config.get("chats_sys_inst")}{chat}.txt'

    await msg.reply_document(
        FSInputFile(chat_sys_inst_path, f'{chat_sys_inst_path}.bak'))

    with open(chat_sys_inst_path, 'wb') as f:
        await msg.bot.download_file((await msg.bot.get_file(msg.document.file_id)).file_path, f)

    await msg.reply(f'System instructions changed for {chat}.')


def get_actions(msg: Message, data_: dict):
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text='Add admin', callback_data=f'data:admin:add:{msg.from_user.id}')
                if msg.from_user.id not in data_["admins"] else
                InlineKeyboardButton(text='Remove admin', callback_data=f'data:admin:remov:{msg.from_user.id}')
            ],
            [
                InlineKeyboardButton(text='Allow chat', callback_data=f'data:chat:add:{msg.chat.id}')
                if msg.chat.id not in data_["chats"] else
                InlineKeyboardButton(text='Block chat', callback_data=f'data:chat:remov:{msg.chat.id}')
            ],
        ]
    )


async def stop_context(msg: Message):
    bot_msg: Message = await msg.reply('Finished receiving messages. Adding context...')
    context = added_chat_context[msg.chat.id][-1]
    if not added_chat_context[msg.chat.id][1]:
        context = context[:-1]
        await msg.bot.send_message(msg.chat.id, 'Last message is removed, because it is from user')
    for interaction in context:
        data.write_chat_history(added_chat_context[msg.chat.id][0], interaction)
    await bot_msg.edit_text(f'Context added to chat {added_chat_context[msg.chat.id][0]}.')
    del added_chat_context[msg.chat.id]
