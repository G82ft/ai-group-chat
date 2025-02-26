from aiogram import Router
from aiogram.filters import CommandStart, Command
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery

from data import data
from shared import chats, config

cmd = Router(name='cmd')


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
        case 'delet':
            if len(data_[f'{key}s']) == 1:
                await cq.answer(f'You cannot remove the last {key}.', show_alert=True)
                return
            data_[f'{key}s'].remove(value)

    data.write(data_)
    await cq.message.edit_text(f'{key.capitalize()} {action}ed successfully.')


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

    config.clear()
    await msg.reply(
        f'Config reloaded.\n'
    )


def get_actions(msg: Message, data_: dict):
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text='Add admin', callback_data=f'data:admin:add:{msg.from_user.id}')
                if msg.from_user.id not in data_["admins"] else
                InlineKeyboardButton(text='Remove admin', callback_data=f'data:admin:delet:{msg.from_user.id}')
            ],
            [
                InlineKeyboardButton(text='Allow chat', callback_data=f'data:chat:add:{msg.chat.id}')
                if msg.chat.id not in data_["chats"] else
                InlineKeyboardButton(text='Block chat', callback_data=f'data:chat:delet:{msg.chat.id}')
            ],
        ]
    )
