from asyncio import Lock

# noinspection PyPackageRequirements
from google.genai.chats import Chat

__all__ = [
    'chats',
    'config',
    'locks'
]


class Dict:
    _value: dict[str, ...] = {}

    def __getattr__(self, name):
        return getattr(self._value, name)

    def __getitem__(self, item):
        return self._value[item]

    def __setitem__(self, key, value):
        self._value[key] = value

    def __delitem__(self, key):
        del self._value[key]

    def __contains__(self, item):
        return item in self._value

    def __repr__(self):
        return repr(self._value)


class ChatLockManager:
    _locks: dict[str, Lock] = {}

    def get_lock(self, chat_id: int) -> Lock:
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


# noinspection PyTypeChecker
chats: dict[int, Chat] = Dict()
# noinspection PyTypeChecker
config: dict[str, ...] = Dict()
locks: ChatLockManager = ChatLockManager()
