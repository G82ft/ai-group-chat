import yaml

from const import CONFIG_PATH


def get(key: str) -> str | list:
    from shared import config as conf
    if key in conf:
        return conf[key]

    with open(CONFIG_PATH, 'r') as f:
        conf.update(yaml.load(f, Loader=yaml.FullLoader))

    return conf[key]
