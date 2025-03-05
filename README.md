# ai-group-chat

This is a Telegram bot that can "talk" in chats with several people. It uses [Google Gemini API](https://ai.google.dev/gemini-api/docs/).
If you reply to a bot's message, the bot will respond back.

1. [Requirements](#requirements)
2. [Running](#running)
2. [Additional help](#additional-help)

## Requirements

Docker.

## Configuring

There is an example of config [here](/config/config.example.yaml).

```yaml
tg_token: XXXXX
base_genai_token: XXXXX
genai_model: gemini-2.0-flash
base_sys_inst: config/sys_inst.txt
admins:
  - 1
  - 2
```

|       Field        | Explanation                                                                       |
|:------------------:|-----------------------------------------------------------------------------------|
|     `tg_token`     | [Telegram bot API token](https://core.telegram.org/bots/api#authorizing-your-bot) |
| `base_genai_token` | [Gemini API key](https://aistudio.google.com/app/apikey)                          |
|   `genai_model`    | [Gemini model variant](https://ai.google.dev/gemini-api/docs/models/gemini)       |
|  `base_sys_inst`   | Base system instructions.                                                         |
|      `admins`      | List of admins' user IDs.                                                         |


## Running

```shell
git clone https://github.com/G82ft/ai-group-chat.git
cd ai-group-chat/
bash ./update.sh
```

Alternatively, you can use your own key on an already working bot, by using `/set_setting api_key <api_key>` command.

It is not recommended, because the key is stored without any encryption.

## Additional help

You can get additional help with `/get_settings_info`. Here is the list af all commands:

```
start - Display info about current chat
reload_chat - [chat_id] Remove chat from cache (will reload on the next message)
reload_config - [chat_id] Remove config values from cache
get_settings_info - Display info about settings types and acceptable values
set_setting - [chat_id] <setting> <value> Change setting
get_sys_inst - <chat_id> Send system instructions as a file (DM only)
set_sys_inst - <chat_id> Set system instructions via attached document (DM only)
add_chat_context - <chat_id> Add context via messages (DM only)
stop_add_context - Stop adding context (DM only)
```
