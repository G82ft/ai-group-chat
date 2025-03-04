from asyncio import Lock
from re import search, sub


def format_input(text: str, user_name: str, is_admin: bool):
    admin = search(r'<a>[\s\S]+</a>', text)

    if admin is None or not is_admin:
        admin = ''
    else:
        admin = admin.group(0).removeprefix('<a>').removesuffix('</a>')
    user = sub(r'<a>[\s\S]+</a>', '', text)

    return (
            f'<message user_role="admin" name="Admin">\n{admin}\n</message>\n'
            + (f'<message user_role="interlocutor" name="{user_name}">\n{user}\n</message>' if user else '')
    )


class ChatLockManager:
    _locks: dict[str, Lock] = {}

    def get_lock(self, chat_id: int) -> Lock:
        if chat_id not in self._locks:
            self._locks[f'{chat_id}'] = Lock()
        return self._locks[f'{chat_id}']

    def acquire(self, chat_id: int):
        chat_id = str(chat_id)
        if chat_id not in self._locks:
            self._locks[chat_id] = Lock()
        return self._locks[chat_id].acquire()

    def release(self, chat_id: int):
        chat_id = str(chat_id)
        if chat_id not in self._locks:
            return
        self._locks[chat_id].release()
