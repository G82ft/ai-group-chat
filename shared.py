# noinspection PyPackageRequirements
from google.genai.chats import Chat

from utils import ChatLockManager

__all__ = [
    'chats',
    'config',
    'file_locks'
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


# noinspection PyTypeChecker
chats: dict[int, Chat] = Dict()
# noinspection PyTypeChecker
config: dict[str, ...] = Dict()
file_locks: ChatLockManager = ChatLockManager()
