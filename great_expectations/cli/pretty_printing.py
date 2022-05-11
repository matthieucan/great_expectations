import re
import sys
from typing import List, Optional

from termcolor import colored


def cli_message(string: str) -> None:
    import inspect

    __frame = inspect.currentframe()
    __file = __frame.f_code.co_filename
    __func = __frame.f_code.co_name
    for (k, v) in __frame.f_locals.items():
        if any((var in k) for var in ("__frame", "__file", "__func")):
            continue
        print(f"<INTROSPECT> {__file}:{__func} - {k}:{v.__class__.__name__}")
    print(cli_colorize_string(string))


def cli_colorize_string(string: str) -> str:
    import inspect

    __frame = inspect.currentframe()
    __file = __frame.f_code.co_filename
    __func = __frame.f_code.co_name
    for (k, v) in __frame.f_locals.items():
        if any((var in k) for var in ("__frame", "__file", "__func")):
            continue
        print(f"<INTROSPECT> {__file}:{__func} - {k}:{v.__class__.__name__}")
    flags = re.DOTALL
    mod_string = re.sub(
        "<blue>(.*?)</blue>", colored("\\g<1>", "blue"), string, flags=flags
    )
    mod_string = re.sub(
        "<cyan>(.*?)</cyan>", colored("\\g<1>", "cyan"), mod_string, flags=flags
    )
    mod_string = re.sub(
        "<green>(.*?)</green>", colored("\\g<1>", "green"), mod_string, flags=flags
    )
    mod_string = re.sub(
        "<yellow>(.*?)</yellow>", colored("\\g<1>", "yellow"), mod_string, flags=flags
    )
    mod_string = re.sub(
        "<red>(.*?)</red>", colored("\\g<1>", "red"), mod_string, flags=flags
    )
    return colored(mod_string)


def display_not_implemented_message_and_exit() -> None:
    import inspect

    __frame = inspect.currentframe()
    __file = __frame.f_code.co_filename
    __func = __frame.f_code.co_name
    for (k, v) in __frame.f_locals.items():
        if any((var in k) for var in ("__frame", "__file", "__func")):
            continue
        print(f"<INTROSPECT> {__file}:{__func} - {k}:{v.__class__.__name__}")
    cli_message(
        "<red>This command is not yet implemented for the v3 (Batch Request) API</red>"
    )
    sys.exit(1)


def cli_message_list(
    string_list: List[str], list_intro_string: Optional[str] = None
) -> None:
    import inspect

    __frame = inspect.currentframe()
    __file = __frame.f_code.co_filename
    __func = __frame.f_code.co_name
    for (k, v) in __frame.f_locals.items():
        if any((var in k) for var in ("__frame", "__file", "__func")):
            continue
        print(f"<INTROSPECT> {__file}:{__func} - {k}:{v.__class__.__name__}")
    "Simple util function for displaying simple lists in cli"
    if list_intro_string:
        cli_message(list_intro_string)
    for string in string_list:
        cli_message(string)


def action_list_to_string(action_list: list) -> str:
    import inspect

    __frame = inspect.currentframe()
    __file = __frame.f_code.co_filename
    __func = __frame.f_code.co_name
    for (k, v) in __frame.f_locals.items():
        if any((var in k) for var in ("__frame", "__file", "__func")):
            continue
        print(f"<INTROSPECT> {__file}:{__func} - {k}:{v.__class__.__name__}")
    "Util function for turning an action list into pretty string"
    action_list_string = ""
    for (idx, action) in enumerate(action_list):
        action_list_string += f"{action['name']} ({action['action']['class_name']})"
        if idx == (len(action_list) - 1):
            continue
        action_list_string += " => "
    return action_list_string


def cli_message_dict(
    dict_: dict,
    indent: int = 3,
    bullet_char: str = "-",
    message_list: Optional[list] = None,
    recursion_flag: bool = False,
) -> None:
    import inspect

    __frame = inspect.currentframe()
    __file = __frame.f_code.co_filename
    __func = __frame.f_code.co_name
    for (k, v) in __frame.f_locals.items():
        if any((var in k) for var in ("__frame", "__file", "__func")):
            continue
        print(f"<INTROSPECT> {__file}:{__func} - {k}:{v.__class__.__name__}")
    "Util function for displaying nested dicts representing ge objects in cli"
    if message_list is None:
        message_list = []
    if dict_.get("name"):
        name = dict_.pop("name")
        message = f"{(' ' * indent)}<cyan>name:</cyan> {name}"
        message_list.append(message)
    if dict_.get("module_name"):
        module_name = dict_.pop("module_name")
        message = f"{(' ' * indent)}<cyan>module_name:</cyan> {module_name}"
        message_list.append(message)
    if dict_.get("class_name"):
        class_name = dict_.pop("class_name")
        message = f"{(' ' * indent)}<cyan>class_name:</cyan> {class_name}"
        message_list.append(message)
    if dict_.get("action_list"):
        action_list = dict_.pop("action_list")
        action_list_string = action_list_to_string(action_list)
        message = f"{(' ' * indent)}<cyan>action_list:</cyan> {action_list_string}"
        message_list.append(message)
    sorted_keys = sorted(dict_.keys())
    for key in sorted_keys:
        if key == "password":
            message = f"{(' ' * indent)}<cyan>password:</cyan> ******"
            message_list.append(message)
            continue
        if isinstance(dict_[key], dict):
            message = f"{(' ' * indent)}<cyan>{key}:</cyan>"
            message_list.append(message)
            cli_message_dict(
                dict_[key],
                indent=(indent + 2),
                message_list=message_list,
                recursion_flag=True,
            )
        else:
            message = f"{(' ' * indent)}<cyan>{key}:</cyan> {str(dict_[key])}"
            message_list.append(message)
    if not recursion_flag:
        if bullet_char and (indent > 1):
            first = message_list[0]
            new_first = (first[:1] + bullet_char) + first[2:]
            message_list[0] = new_first
        cli_message_list(message_list)
