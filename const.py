CONFIG_PATH: str = 'config/config.yaml'
CHATS_PATH: str = 'chats/'
CHAT_PATH: str = CHATS_PATH + '{}/'
CHAT_HISTORY: str = f'{CHAT_PATH}history.jsonl'
CHAT_SYS_INST: str = f'{CHAT_PATH}sys_inst.txt'
CHAT_SETTINGS: str = f'{CHAT_PATH}settings.json'
DEFAULT_SETTINGS: dict = {
    "api_key": None,
    "image_recognition": "no",
    "safety": {
        "HARM_CATEGORY_HATE_SPEECH": "BLOCK_MEDIUM_AND_ABOVE",
        "HARM_CATEGORY_DANGEROUS_CONTENT": "BLOCK_MEDIUM_AND_ABOVE",
        "HARM_CATEGORY_HARASSMENT": "BLOCK_MEDIUM_AND_ABOVE",
        "HARM_CATEGORY_SEXUALLY_EXPLICIT": "BLOCK_MEDIUM_AND_ABOVE",
        "HARM_CATEGORY_CIVIC_INTEGRITY": "BLOCK_MEDIUM_AND_ABOVE"
    },
    "override_sys": False,
    "enabled": False
}
SETTINGS_INFO: dict = {
    "api_key": {
        "type": str
    },
    "image_recognition": {
        "type": str,
        "values": ['no', 'ignore'],
        "admin_values": ['yes', 'ask', 'no', 'ignore']
    },
    "safety": {
        "type": dict
    },
    "override_sys": {
        "type": bool
    },
    "enabled": {
        "type": bool
    }
}
SETTINGS_VALIDATION: dict = {
    "image_recognition": {
        "validate": lambda v: v in SETTINGS_INFO["image_recognition"]["values"],
        "admin_validate": lambda v: v in SETTINGS_INFO["image_recognition"]["admin_values"]
    },
    "safety": {
        "validate": lambda d: all(
            k in ["HARM_CATEGORY_HATE_SPEECH", "HARM_CATEGORY_DANGEROUS_CONTENT", "HARM_CATEGORY_HARASSMENT",
                  "HARM_CATEGORY_SEXUALLY_EXPLICIT", "HARM_CATEGORY_CIVIC_INTEGRITY"]
            and v in ['BLOCK_MEDIUM_AND_ABOVE', 'BLOCK_LOW_AND_ABOVE']
            for k, v in d.items()
        ),
        "admin_validate": lambda d: all(
            k in ["HARM_CATEGORY_HATE_SPEECH", "HARM_CATEGORY_DANGEROUS_CONTENT", "HARM_CATEGORY_HARASSMENT",
                  "HARM_CATEGORY_SEXUALLY_EXPLICIT", "HARM_CATEGORY_CIVIC_INTEGRITY"]
            and v in ['BLOCK_MEDIUM_AND_ABOVE', 'BLOCK_LOW_AND_ABOVE', 'BLOCK_ONLY_HIGH', 'BLOCK_NONE', 'OFF']
            for k, v in d.items()
        )
    },
    "override_sys": {
        "validate": lambda v: not v,
        "admin_validate": lambda _: True
    },
    "enabled": {
        "validate": lambda v: not v,
        "admin_validate": lambda _: True
    }
}
TRUE_LITERALS: tuple[str, ...] = ('true', '1', 'yes')
