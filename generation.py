import io
from re import sub, search

from PIL import Image
from aiogram import F, Router
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
# noinspection PyPackageRequirements
from google import genai
# noinspection PyPackageRequirements
# noinspection PyPackageRequirements
from google.genai.types import GenerateContentConfig, Part

from config import config
from data import data
from shared import chats

client = genai.Client(api_key=config.get("genai_token"))

gen = Router(name='gen')


@gen.message((F.reply_to_message & F.reply_to_message.from_user.id == 7584972194) & (~F.photo))
async def handle_text(msg: Message):
    data_ = data.fetch()
    if msg.chat.id not in data_["chats"]:
        return

    bot_msg = await msg.reply('Received, processing...')

    await bot_msg.edit_text(await generate_response(msg))


@gen.message((F.reply_to_message & F.reply_to_message.from_user.id == 7584972194) & F.photo)
async def confirm_photo(msg: Message):
    await msg.reply(
        'Photo detected. Do you want AI to analyze it?',
        reply_markup=InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text='Yes', callback_data=f'photo:yes')],
                [InlineKeyboardButton(text='Analyze text only', callback_data=f'photo:text')],
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
        case 'text':
            await cq.message.edit_text('Processing text only...')
            await cq.message.edit_text(await generate_response(cq.message.reply_to_message))
        case 'cancel':
            await cq.message.edit_text('Processing request cancelled.')


async def generate_response(msg: Message, photo: bool = False):
    if msg.chat.id not in chats:
        chats[msg.chat.id] = create_chat(msg.chat.id)

    text = msg.text or msg.caption or '<empty>'
    admin = search(r'<a>[\s\S]+</a>', text)

    if admin is None or msg.from_user.id not in data.fetch()["admins"]:
        admin = ''
    else:
        admin = admin.group(0)
    user = sub(r'<a>[\s\S]+</a>', '', text)

    request = f'{admin}\n' + (f'<u name="{msg.from_user.first_name}">\n{user}\n</u>' if user else '')
    if not request:
        return 'Your message is empty.'

    contents = [request]
    if photo and msg.photo:
        image_file = io.BytesIO()
        await msg.bot.download_file((await msg.bot.get_file(msg.photo[0].file_id)).file_path, image_file)
        contents.append(Part.from_bytes(data=image_file.getvalue(), mime_type='image/jpeg'))

    result = chats[msg.chat.id].send_message(contents)

    if result.text is None:
        response = 'Rephrase your message and try again.\n'
        if result.prompt_feedback is not None:
            response += f'Block reason: {result.prompt_feedback.block_reason.value}'
        return response

    data.write_chat_history(msg.chat.id, (request, result.text))

    return result.text or "<empty>"


def create_chat(chat_id: int):
    with open(config.get("sys_inst")) as f:
        sys_inst: str = f.read()

    return client.chats.create(
        model="gemini-2.0-flash",
        config=GenerateContentConfig(
            temperature=1.5,
            system_instruction=sys_inst,
            safety_settings=config.safety_settings,
        ),
        history=data.get_chat_history(chat_id)
    )
