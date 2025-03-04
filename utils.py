from asyncio import Lock
from re import search, sub


def format_input(text: str, user_name: str, is_admin: bool):
    admin = search(r'<a>[\s\S]+</a>', text)

    if admin is None or not is_admin:
        admin = ''
    else:
        admin = admin.group(0)
    user = sub(r'<a>[\s\S]+</a>', '', text)

    return f'{admin}\n' + (f'<u name="{user_name}">\n{user}\n</u>' if user else '')


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
