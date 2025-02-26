from re import search, sub


def format_input(text: str, user_name: str, is_admin: bool):
    admin = search(r'<a>[\s\S]+</a>', text)

    if admin is None or not is_admin:
        admin = ''
    else:
        admin = admin.group(0)
    user = sub(r'<a>[\s\S]+</a>', '', text)

    return f'{admin}\n' + (f'<u name="{user_name}">\n{user}\n</u>' if user else '')
