# noinspection PyPackageRequirements
from google.genai.chats import Chat

__all__ = [
    'chats',
    'config'
]


class Chats:
    _value: dict[int, Chat] = {}

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


class Config:
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


chats: dict[int, Chat] = Chats()  # noqa
config: dict[str, ...] = Config()  # noqa
