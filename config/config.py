import yaml
from google.genai.types import SafetySetting, HarmCategory, HarmBlockThreshold


CONFIG_PATH: str = 'config/config.yaml'


def get(key: str) -> str:
    from shared import config as conf
    if key in conf:
        return conf[key]

    with open(CONFIG_PATH, 'r') as f:
        conf = yaml.load(f, Loader=yaml.FullLoader)

    return conf[key]


safety_settings = [
    SafetySetting(
        category=HarmCategory.HARM_CATEGORY_HARASSMENT,
        threshold=HarmBlockThreshold.BLOCK_NONE,
    ),
    SafetySetting(
        category=HarmCategory.HARM_CATEGORY_HATE_SPEECH,
        threshold=HarmBlockThreshold.BLOCK_NONE,
    ),
    SafetySetting(
        category=HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT,
        threshold=HarmBlockThreshold.BLOCK_NONE,
    ),
    SafetySetting(
        category=HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT,
        threshold=HarmBlockThreshold.BLOCK_NONE,
    ),
    SafetySetting(
        category=HarmCategory.HARM_CATEGORY_CIVIC_INTEGRITY,
        threshold=HarmBlockThreshold.BLOCK_NONE,
    )
]
