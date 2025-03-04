import io
from base64 import b64encode

from aiogram import F, Router
from aiogram.enums import ParseMode
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery, ReactionTypeEmoji
# noinspection PyPackageRequirements
from google.genai.errors import APIError
# noinspection PyPackageRequirements
from google.genai.types import Part

from commands import is_admin
from data import history, settings
from data.misc import create_chat
from shared import chats
from utils import format_input, ChatLockManager

gen = Router(name='gen')

reaction_filter = (F.reply_to_message & F.reply_to_message.from_user.id == 7584972194) | (F.chat.id == F.from_user.id)
gen_locks: ChatLockManager = ChatLockManager()


@gen.message(reaction_filter & (~F.photo))
async def handle_text(msg: Message):
    if not (await settings.get(msg.chat.id))["enabled"]:
        return

    await msg.react([ReactionTypeEmoji(emoji='👀')])

    await msg.reply(await generate_response(msg))


@gen.message(reaction_filter & F.photo)
async def handle_photo(msg: Message):
    match (await settings.get(msg.chat.id))["image_recognition"]:
        case 'ignore':
            return
        case 'no':
            await msg.reply(
                'Image recognition is disabled.\n'
                'You can disable this message by using `/set_setting image_recognition ignore`.',
                parse_mode=ParseMode.MARKDOWN
            )
        case 'ask':
            await confirm_photo(msg)
        case 'yes':
            await msg.react([ReactionTypeEmoji(emoji='👀')])
            await msg.reply(await generate_response(msg, True))
        case _:
            return


async def confirm_photo(msg: Message):
    await msg.reply(
        'Photo detected. Do you want AI to analyze it?',
        reply_markup=InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text='Yes', callback_data=f'photo:yes')],
                [InlineKeyboardButton(text='Analyze caption only', callback_data=f'photo:caption')],
                [InlineKeyboardButton(text='Cancel', callback_data=f'photo:cancel')]
            ]
        )
    )


@gen.callback_query(lambda c: c.data.startswith('photo:'))
async def handle_photo(cq: CallbackQuery):
    response = cq.data.removeprefix('photo:')

    match response:
        case 'yes':
            await cq.message.edit_text('Processing with photo...')
            await cq.message.edit_text(await generate_response(cq.message.reply_to_message, True))
        case 'caption':
            await cq.message.edit_text('Processing caption only...')
            await cq.message.edit_text(await generate_response(cq.message.reply_to_message))
        case 'cancel':
            await cq.message.edit_text('Processing request cancelled.')


async def generate_response(msg: Message, photo: bool = False):
    if msg.chat.id not in chats:
        chats[msg.chat.id] = await create_chat(msg.chat.id)

    text = msg.text or msg.caption or '<empty>'

    request = format_input(text, msg.from_user.first_name, await is_admin(msg))

    if not request:
        return 'Your message is empty.'

    contents = [Part(text=request)]
    image_file = io.BytesIO()
    if photo and msg.photo:
        await msg.bot.download_file((await msg.bot.get_file(msg.photo[0].file_id)).file_path, image_file)
        contents.append(Part.from_bytes(data=image_file.getvalue(), mime_type='image/jpeg'))

    await msg.bot.send_chat_action(msg.chat.id, 'typing')
    try:
        async with gen_locks.get_lock(msg.chat.id):
            result = chats[msg.chat.id].send_message(contents)
    except APIError as ce:
        response: str = f'Unexpected error: {ce.code} {ce.status}.\n'
        match ce.code:
            case 429:
                response += ('Too many requests. Bot is disabled.\n'
                             'Contact admin to check limits.\n'
                             'https://console.cloud.google.com/apis/dashboard')
                await settings.set_setting(msg.chat.id, "enabled", False)
            case 500:
                response += ('Input context is too long. Bot is disabled.\n'
                             'Contact admin to clear chat history.')
                await settings.set_setting(msg.chat.id, "enabled", False)
            case 503:
                response += 'Service is temporarily running out of capacity. Please try again later.'

        return response

    if result.text is None:
        response = 'Rephrase your message and try again.\n'
        if result.prompt_feedback is not None:
            response += f'Block reason: {result.prompt_feedback.block_reason.value}'
        return response

    await history.write_chat_history(
        msg.chat.id,
        [
            [request]
            + (
                [b64encode(image_file.getvalue()).decode('ascii')]
                if image_file.getvalue()
                else []
            ), [result.text]])

    return result.text or "<empty>"
