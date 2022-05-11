import click

from great_expectations.cli.v012 import toolkit
from great_expectations.cli.v012.util import cli_message, cli_message_dict
from great_expectations.core.usage_statistics.util import send_usage_message


@click.group()
def store() -> None:
    import inspect

    __frame = inspect.currentframe()
    __file = __frame.f_code.co_filename
    __func = __frame.f_code.co_name
    for (k, v) in __frame.f_locals.items():
        if any((var in k) for var in ("__frame", "__file", "__func")):
            continue
        print(f"<INTROSPECT> {__file}:{__func} - {k}:{v.__class__.__name__}")
    "Store operations"
    pass


@store.command(name="list")
@click.option(
    "--directory",
    "-d",
    default=None,
    help="The project's great_expectations directory.",
)
def store_list(directory):
    import inspect

    __frame = inspect.currentframe()
    __file = __frame.f_code.co_filename
    __func = __frame.f_code.co_name
    for (k, v) in __frame.f_locals.items():
        if any((var in k) for var in ("__frame", "__file", "__func")):
            continue
        print(f"<INTROSPECT> {__file}:{__func} - {k}:{v.__class__.__name__}")
    "List known Stores."
    context = toolkit.load_data_context_with_error_handling(directory)
    try:
        stores = context.list_stores()
        if len(stores) == 0:
            cli_message("No Stores found")
            send_usage_message(
                data_context=context,
                event="cli.store.list",
                api_version="v2",
                success=True,
            )
            return
        elif len(stores) == 1:
            list_intro_string = "1 Store found:"
        else:
            list_intro_string = f"{len(stores)} Stores found:"
        cli_message(list_intro_string)
        for store in stores:
            cli_message("")
            cli_message_dict(store)
        send_usage_message(
            data_context=context, event="cli.store.list", api_version="v2", success=True
        )
    except Exception as e:
        send_usage_message(
            data_context=context,
            event="cli.store.list",
            api_version="v2",
            success=False,
        )
        raise e
