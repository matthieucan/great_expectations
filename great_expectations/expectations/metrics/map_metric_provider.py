import inspect
import logging
from functools import wraps
from typing import Any, Callable, Dict, List, Optional, Type, Union

import numpy as np

import great_expectations.exceptions as ge_exceptions
from great_expectations.core import ExpectationConfiguration
from great_expectations.core.util import convert_to_json_serializable
from great_expectations.execution_engine import (
    ExecutionEngine,
    PandasExecutionEngine,
    SparkDFExecutionEngine,
    SqlAlchemyExecutionEngine,
)
from great_expectations.execution_engine.execution_engine import (
    MetricDomainTypes,
    MetricFunctionTypes,
    MetricPartialFunctionTypes,
)
from great_expectations.execution_engine.sqlalchemy_execution_engine import (
    OperationalError,
)
from great_expectations.expectations.metrics import MetaMetricProvider
from great_expectations.expectations.metrics.import_manager import F, sa
from great_expectations.expectations.metrics.metric_provider import (
    MetricProvider,
    metric_partial,
)
from great_expectations.expectations.metrics.util import Engine, Insert, Label, Select
from great_expectations.expectations.registry import (
    get_metric_provider,
    register_metric,
)
from great_expectations.util import (
    generate_temporary_table_name,
    get_sqlalchemy_selectable,
)
from great_expectations.validator.metric_configuration import MetricConfiguration

logger = logging.getLogger(__name__)


def column_function_partial(
    engine: Type[ExecutionEngine], partial_fn_type: str = None, **kwargs
):
    import inspect

    __frame = inspect.currentframe()
    __file = __frame.f_code.co_filename
    __func = __frame.f_code.co_name
    for (k, v) in __frame.f_locals.items():
        if any((var in k) for var in ("__frame", "__file", "__func")):
            continue
        print(f"<INTROSPECT> {__file}:{__func} - {k}:{v.__class__.__name__}")
    "Provides engine-specific support for authoring a metric_fn with a simplified signature.\n\n    A metric function that is decorated as a column_function_partial will be called with the engine-specific column type\n    and any value_kwargs associated with the Metric for which the provider function is being declared.\n\n    Args:\n        engine:\n        partial_fn_type:\n        **kwargs:\n\n    Returns:\n        An annotated metric_function which will be called with a simplified signature.\n\n    "
    domain_type = MetricDomainTypes.COLUMN
    if issubclass(engine, PandasExecutionEngine):
        if partial_fn_type is None:
            partial_fn_type = MetricPartialFunctionTypes.MAP_SERIES
        partial_fn_type = MetricPartialFunctionTypes(partial_fn_type)
        if partial_fn_type != MetricPartialFunctionTypes.MAP_SERIES:
            raise ValueError(
                "PandasExecutionEngine only supports map_series for column_function_partial partial_fn_type"
            )

        def wrapper(metric_fn: Callable):
            import inspect

            __frame = inspect.currentframe()
            __file = __frame.f_code.co_filename
            __func = __frame.f_code.co_name
            for (k, v) in __frame.f_locals.items():
                if any((var in k) for var in ("__frame", "__file", "__func")):
                    continue
                print(f"<INTROSPECT> {__file}:{__func} - {k}:{v.__class__.__name__}")

            @metric_partial(
                engine=engine,
                partial_fn_type=partial_fn_type,
                domain_type=domain_type,
                **kwargs,
            )
            @wraps(metric_fn)
            def inner_func(
                cls,
                execution_engine: PandasExecutionEngine,
                metric_domain_kwargs: Dict,
                metric_value_kwargs: Dict,
                metrics: Dict[(str, Any)],
                runtime_configuration: Dict,
            ):
                import inspect

                __frame = inspect.currentframe()
                __file = __frame.f_code.co_filename
                __func = __frame.f_code.co_name
                for (k, v) in __frame.f_locals.items():
                    if any((var in k) for var in ("__frame", "__file", "__func")):
                        continue
                    print(
                        f"<INTROSPECT> {__file}:{__func} - {k}:{v.__class__.__name__}"
                    )
                filter_column_isnull = kwargs.get(
                    "filter_column_isnull", getattr(cls, "filter_column_isnull", False)
                )
                (
                    df,
                    compute_domain_kwargs,
                    accessor_domain_kwargs,
                ) = execution_engine.get_compute_domain(
                    domain_kwargs=metric_domain_kwargs, domain_type=domain_type
                )
                column_name = accessor_domain_kwargs["column"]
                if column_name not in metrics["table.columns"]:
                    raise ge_exceptions.InvalidMetricAccessorDomainKwargsKeyError(
                        message=f'Error: The column "{column_name}" in BatchData does not exist.'
                    )
                if filter_column_isnull:
                    df = df[df[column_name].notnull()]
                values = metric_fn(
                    cls, df[column_name], **metric_value_kwargs, _metrics=metrics
                )
                return (values, compute_domain_kwargs, accessor_domain_kwargs)

            return inner_func

        return wrapper
    elif issubclass(engine, SqlAlchemyExecutionEngine):
        if partial_fn_type is None:
            partial_fn_type = MetricPartialFunctionTypes.MAP_FN
        partial_fn_type = MetricPartialFunctionTypes(partial_fn_type)
        if partial_fn_type not in [MetricPartialFunctionTypes.MAP_FN]:
            raise ValueError(
                "SqlAlchemyExecutionEngine only supports map_fn for column_function_partial partial_fn_type"
            )

        def wrapper(metric_fn: Callable):
            import inspect

            __frame = inspect.currentframe()
            __file = __frame.f_code.co_filename
            __func = __frame.f_code.co_name
            for (k, v) in __frame.f_locals.items():
                if any((var in k) for var in ("__frame", "__file", "__func")):
                    continue
                print(f"<INTROSPECT> {__file}:{__func} - {k}:{v.__class__.__name__}")

            @metric_partial(
                engine=engine,
                partial_fn_type=partial_fn_type,
                domain_type=domain_type,
                **kwargs,
            )
            @wraps(metric_fn)
            def inner_func(
                cls,
                execution_engine: SqlAlchemyExecutionEngine,
                metric_domain_kwargs: Dict,
                metric_value_kwargs: Dict,
                metrics: Dict[(str, Any)],
                runtime_configuration: Dict,
            ):
                import inspect

                __frame = inspect.currentframe()
                __file = __frame.f_code.co_filename
                __func = __frame.f_code.co_name
                for (k, v) in __frame.f_locals.items():
                    if any((var in k) for var in ("__frame", "__file", "__func")):
                        continue
                    print(
                        f"<INTROSPECT> {__file}:{__func} - {k}:{v.__class__.__name__}"
                    )
                filter_column_isnull = kwargs.get(
                    "filter_column_isnull", getattr(cls, "filter_column_isnull", False)
                )
                if filter_column_isnull:
                    compute_domain_kwargs = execution_engine.add_column_row_condition(
                        metric_domain_kwargs
                    )
                else:
                    compute_domain_kwargs = metric_domain_kwargs
                (
                    selectable,
                    compute_domain_kwargs,
                    accessor_domain_kwargs,
                ) = execution_engine.get_compute_domain(
                    domain_kwargs=compute_domain_kwargs, domain_type=domain_type
                )
                column_name = accessor_domain_kwargs["column"]
                if column_name not in metrics["table.columns"]:
                    raise ge_exceptions.InvalidMetricAccessorDomainKwargsKeyError(
                        message=f'Error: The column "{column_name}" in BatchData does not exist.'
                    )
                dialect = execution_engine.dialect_module
                column_function = metric_fn(
                    cls,
                    sa.column(column_name),
                    **metric_value_kwargs,
                    _dialect=dialect,
                    _table=selectable,
                    _metrics=metrics,
                )
                return (column_function, compute_domain_kwargs, accessor_domain_kwargs)

            return inner_func

        return wrapper
    elif issubclass(engine, SparkDFExecutionEngine):
        if partial_fn_type is None:
            partial_fn_type = MetricPartialFunctionTypes.MAP_FN
        partial_fn_type = MetricPartialFunctionTypes(partial_fn_type)
        if partial_fn_type not in [
            MetricPartialFunctionTypes.MAP_FN,
            MetricPartialFunctionTypes.WINDOW_FN,
        ]:
            raise ValueError(
                "SparkDFExecutionEngine only supports map_fn and window_fn for column_function_partial partial_fn_type"
            )

        def wrapper(metric_fn: Callable):
            import inspect

            __frame = inspect.currentframe()
            __file = __frame.f_code.co_filename
            __func = __frame.f_code.co_name
            for (k, v) in __frame.f_locals.items():
                if any((var in k) for var in ("__frame", "__file", "__func")):
                    continue
                print(f"<INTROSPECT> {__file}:{__func} - {k}:{v.__class__.__name__}")

            @metric_partial(
                engine=engine,
                partial_fn_type=partial_fn_type,
                domain_type=domain_type,
                **kwargs,
            )
            @wraps(metric_fn)
            def inner_func(
                cls,
                execution_engine: SparkDFExecutionEngine,
                metric_domain_kwargs: Dict,
                metric_value_kwargs: Dict,
                metrics: Dict[(str, Any)],
                runtime_configuration: Dict,
            ):
                import inspect

                __frame = inspect.currentframe()
                __file = __frame.f_code.co_filename
                __func = __frame.f_code.co_name
                for (k, v) in __frame.f_locals.items():
                    if any((var in k) for var in ("__frame", "__file", "__func")):
                        continue
                    print(
                        f"<INTROSPECT> {__file}:{__func} - {k}:{v.__class__.__name__}"
                    )
                filter_column_isnull = kwargs.get(
                    "filter_column_isnull", getattr(cls, "filter_column_isnull", False)
                )
                if filter_column_isnull:
                    compute_domain_kwargs = execution_engine.add_column_row_condition(
                        metric_domain_kwargs
                    )
                else:
                    compute_domain_kwargs = metric_domain_kwargs
                (
                    data,
                    compute_domain_kwargs,
                    accessor_domain_kwargs,
                ) = execution_engine.get_compute_domain(
                    domain_kwargs=compute_domain_kwargs, domain_type=domain_type
                )
                column_name = accessor_domain_kwargs["column"]
                if column_name not in metrics["table.columns"]:
                    raise ge_exceptions.InvalidMetricAccessorDomainKwargsKeyError(
                        message=f'Error: The column "{column_name}" in BatchData does not exist.'
                    )
                column = data[column_name]
                column_function = metric_fn(
                    cls,
                    column=column,
                    **metric_value_kwargs,
                    _metrics=metrics,
                    _compute_domain_kwargs=compute_domain_kwargs,
                )
                return (column_function, compute_domain_kwargs, accessor_domain_kwargs)

            return inner_func

        return wrapper
    else:
        raise ValueError("Unsupported engine for column_function_partial")


def column_condition_partial(
    engine: Type[ExecutionEngine],
    partial_fn_type: Optional[Union[(str, MetricPartialFunctionTypes)]] = None,
    **kwargs,
):
    import inspect

    __frame = inspect.currentframe()
    __file = __frame.f_code.co_filename
    __func = __frame.f_code.co_name
    for (k, v) in __frame.f_locals.items():
        if any((var in k) for var in ("__frame", "__file", "__func")):
            continue
        print(f"<INTROSPECT> {__file}:{__func} - {k}:{v.__class__.__name__}")
    "Provides engine-specific support for authoring a metric_fn with a simplified signature.\n\n    A column_condition_partial must provide a map function that evaluates to a boolean value; it will be used to provide\n    supplemental metrics, such as the unexpected_value count, unexpected_values, and unexpected_rows.\n\n    A metric function that is decorated as a column_condition_partial will be called with the engine-specific column\n    type and any value_kwargs associated with the Metric for which the provider function is being declared.\n\n\n\n    Args:\n        engine:\n        partial_fn_type:\n        **kwargs:\n\n    Returns:\n        An annotated metric_function which will be called with a simplified signature.\n\n    "
    domain_type = MetricDomainTypes.COLUMN
    if issubclass(engine, PandasExecutionEngine):
        if partial_fn_type is None:
            partial_fn_type = MetricPartialFunctionTypes.MAP_CONDITION_SERIES
        partial_fn_type = MetricPartialFunctionTypes(partial_fn_type)
        if partial_fn_type not in [MetricPartialFunctionTypes.MAP_CONDITION_SERIES]:
            raise ValueError(
                "PandasExecutionEngine only supports map_condition_series for column_condition_partial partial_fn_type"
            )

        def wrapper(metric_fn: Callable):
            import inspect

            __frame = inspect.currentframe()
            __file = __frame.f_code.co_filename
            __func = __frame.f_code.co_name
            for (k, v) in __frame.f_locals.items():
                if any((var in k) for var in ("__frame", "__file", "__func")):
                    continue
                print(f"<INTROSPECT> {__file}:{__func} - {k}:{v.__class__.__name__}")

            @metric_partial(
                engine=engine,
                partial_fn_type=partial_fn_type,
                domain_type=domain_type,
                **kwargs,
            )
            @wraps(metric_fn)
            def inner_func(
                cls,
                execution_engine: PandasExecutionEngine,
                metric_domain_kwargs: Dict,
                metric_value_kwargs: Dict,
                metrics: Dict[(str, Any)],
                runtime_configuration: Dict,
            ):
                import inspect

                __frame = inspect.currentframe()
                __file = __frame.f_code.co_filename
                __func = __frame.f_code.co_name
                for (k, v) in __frame.f_locals.items():
                    if any((var in k) for var in ("__frame", "__file", "__func")):
                        continue
                    print(
                        f"<INTROSPECT> {__file}:{__func} - {k}:{v.__class__.__name__}"
                    )
                filter_column_isnull = kwargs.get(
                    "filter_column_isnull", getattr(cls, "filter_column_isnull", True)
                )
                (
                    df,
                    compute_domain_kwargs,
                    accessor_domain_kwargs,
                ) = execution_engine.get_compute_domain(
                    domain_kwargs=metric_domain_kwargs, domain_type=domain_type
                )
                column_name = accessor_domain_kwargs["column"]
                if column_name not in metrics["table.columns"]:
                    raise ge_exceptions.InvalidMetricAccessorDomainKwargsKeyError(
                        message=f'Error: The column "{column_name}" in BatchData does not exist.'
                    )
                if filter_column_isnull:
                    df = df[df[column_name].notnull()]
                meets_expectation_series = metric_fn(
                    cls, df[column_name], **metric_value_kwargs, _metrics=metrics
                )
                return (
                    (~meets_expectation_series),
                    compute_domain_kwargs,
                    accessor_domain_kwargs,
                )

            return inner_func

        return wrapper
    elif issubclass(engine, SqlAlchemyExecutionEngine):
        if partial_fn_type is None:
            partial_fn_type = MetricPartialFunctionTypes.MAP_CONDITION_FN
        partial_fn_type = MetricPartialFunctionTypes(partial_fn_type)
        if partial_fn_type not in [
            MetricPartialFunctionTypes.MAP_CONDITION_FN,
            MetricPartialFunctionTypes.WINDOW_CONDITION_FN,
        ]:
            raise ValueError(
                "SqlAlchemyExecutionEngine only supports map_condition_fn and window_condition_fn for column_condition_partial partial_fn_type"
            )

        def wrapper(metric_fn: Callable):
            import inspect

            __frame = inspect.currentframe()
            __file = __frame.f_code.co_filename
            __func = __frame.f_code.co_name
            for (k, v) in __frame.f_locals.items():
                if any((var in k) for var in ("__frame", "__file", "__func")):
                    continue
                print(f"<INTROSPECT> {__file}:{__func} - {k}:{v.__class__.__name__}")

            @metric_partial(
                engine=engine,
                partial_fn_type=partial_fn_type,
                domain_type=domain_type,
                **kwargs,
            )
            @wraps(metric_fn)
            def inner_func(
                cls,
                execution_engine: SqlAlchemyExecutionEngine,
                metric_domain_kwargs: Dict,
                metric_value_kwargs: Dict,
                metrics: Dict[(str, Any)],
                runtime_configuration: Dict,
            ):
                import inspect

                __frame = inspect.currentframe()
                __file = __frame.f_code.co_filename
                __func = __frame.f_code.co_name
                for (k, v) in __frame.f_locals.items():
                    if any((var in k) for var in ("__frame", "__file", "__func")):
                        continue
                    print(
                        f"<INTROSPECT> {__file}:{__func} - {k}:{v.__class__.__name__}"
                    )
                filter_column_isnull = kwargs.get(
                    "filter_column_isnull", getattr(cls, "filter_column_isnull", True)
                )
                (
                    selectable,
                    compute_domain_kwargs,
                    accessor_domain_kwargs,
                ) = execution_engine.get_compute_domain(
                    metric_domain_kwargs, domain_type=domain_type
                )
                column_name = accessor_domain_kwargs["column"]
                if column_name not in metrics["table.columns"]:
                    raise ge_exceptions.InvalidMetricAccessorDomainKwargsKeyError(
                        message=f'Error: The column "{column_name}" in BatchData does not exist.'
                    )
                sqlalchemy_engine: Engine = execution_engine.engine
                dialect = execution_engine.dialect_module
                expected_condition = metric_fn(
                    cls,
                    sa.column(column_name),
                    **metric_value_kwargs,
                    _dialect=dialect,
                    _table=selectable,
                    _sqlalchemy_engine=sqlalchemy_engine,
                    _metrics=metrics,
                )
                if filter_column_isnull:
                    unexpected_condition = sa.and_(
                        sa.not_(sa.column(column_name).is_(None)),
                        sa.not_(expected_condition),
                    )
                else:
                    unexpected_condition = sa.not_(expected_condition)
                return (
                    unexpected_condition,
                    compute_domain_kwargs,
                    accessor_domain_kwargs,
                )

            return inner_func

        return wrapper
    elif issubclass(engine, SparkDFExecutionEngine):
        if partial_fn_type is None:
            partial_fn_type = MetricPartialFunctionTypes.MAP_CONDITION_FN
        partial_fn_type = MetricPartialFunctionTypes(partial_fn_type)
        if partial_fn_type not in [
            MetricPartialFunctionTypes.MAP_CONDITION_FN,
            MetricPartialFunctionTypes.WINDOW_CONDITION_FN,
        ]:
            raise ValueError(
                "SparkDFExecutionEngine only supports map_condition_fn and window_condition_fn for column_condition_partial partial_fn_type"
            )

        def wrapper(metric_fn: Callable):
            import inspect

            __frame = inspect.currentframe()
            __file = __frame.f_code.co_filename
            __func = __frame.f_code.co_name
            for (k, v) in __frame.f_locals.items():
                if any((var in k) for var in ("__frame", "__file", "__func")):
                    continue
                print(f"<INTROSPECT> {__file}:{__func} - {k}:{v.__class__.__name__}")

            @metric_partial(
                engine=engine,
                partial_fn_type=partial_fn_type,
                domain_type=domain_type,
                **kwargs,
            )
            @wraps(metric_fn)
            def inner_func(
                cls,
                execution_engine: SparkDFExecutionEngine,
                metric_domain_kwargs: Dict,
                metric_value_kwargs: Dict,
                metrics: Dict[(str, Any)],
                runtime_configuration: Dict,
            ):
                import inspect

                __frame = inspect.currentframe()
                __file = __frame.f_code.co_filename
                __func = __frame.f_code.co_name
                for (k, v) in __frame.f_locals.items():
                    if any((var in k) for var in ("__frame", "__file", "__func")):
                        continue
                    print(
                        f"<INTROSPECT> {__file}:{__func} - {k}:{v.__class__.__name__}"
                    )
                filter_column_isnull = kwargs.get(
                    "filter_column_isnull", getattr(cls, "filter_column_isnull", True)
                )
                (
                    data,
                    compute_domain_kwargs,
                    accessor_domain_kwargs,
                ) = execution_engine.get_compute_domain(
                    domain_kwargs=metric_domain_kwargs, domain_type=domain_type
                )
                column_name = accessor_domain_kwargs["column"]
                if column_name not in metrics["table.columns"]:
                    raise ge_exceptions.InvalidMetricAccessorDomainKwargsKeyError(
                        message=f'Error: The column "{column_name}" in BatchData does not exist.'
                    )
                column = data[column_name]
                expected_condition = metric_fn(
                    cls,
                    column,
                    **metric_value_kwargs,
                    _table=data,
                    _metrics=metrics,
                    _compute_domain_kwargs=compute_domain_kwargs,
                    _accessor_domain_kwargs=accessor_domain_kwargs,
                )
                if partial_fn_type == MetricPartialFunctionTypes.WINDOW_CONDITION_FN:
                    if filter_column_isnull:
                        compute_domain_kwargs = (
                            execution_engine.add_column_row_condition(
                                compute_domain_kwargs, column_name=column_name
                            )
                        )
                    unexpected_condition = ~expected_condition
                elif filter_column_isnull:
                    unexpected_condition = column.isNotNull() & (~expected_condition)
                else:
                    unexpected_condition = ~expected_condition
                return (
                    unexpected_condition,
                    compute_domain_kwargs,
                    accessor_domain_kwargs,
                )

            return inner_func

        return wrapper
    else:
        raise ValueError("Unsupported engine for column_condition_partial")


def column_pair_function_partial(
    engine: Type[ExecutionEngine], partial_fn_type: str = None, **kwargs
):
    import inspect

    __frame = inspect.currentframe()
    __file = __frame.f_code.co_filename
    __func = __frame.f_code.co_name
    for (k, v) in __frame.f_locals.items():
        if any((var in k) for var in ("__frame", "__file", "__func")):
            continue
        print(f"<INTROSPECT> {__file}:{__func} - {k}:{v.__class__.__name__}")
    "Provides engine-specific support for authoring a metric_fn with a simplified signature.\n\n    A metric function that is decorated as a column_pair_function_partial will be called with the engine-specific\n    column_list type and any value_kwargs associated with the Metric for which the provider function is being declared.\n\n    Args:\n        engine:\n        partial_fn_type:\n        **kwargs:\n\n    Returns:\n        An annotated metric_function which will be called with a simplified signature.\n\n    "
    domain_type = MetricDomainTypes.COLUMN_PAIR
    if issubclass(engine, PandasExecutionEngine):
        if partial_fn_type is None:
            partial_fn_type = MetricPartialFunctionTypes.MAP_SERIES
        partial_fn_type = MetricPartialFunctionTypes(partial_fn_type)
        if partial_fn_type != MetricPartialFunctionTypes.MAP_SERIES:
            raise ValueError(
                "PandasExecutionEngine only supports map_series for column_pair_function_partial partial_fn_type"
            )

        def wrapper(metric_fn: Callable):
            import inspect

            __frame = inspect.currentframe()
            __file = __frame.f_code.co_filename
            __func = __frame.f_code.co_name
            for (k, v) in __frame.f_locals.items():
                if any((var in k) for var in ("__frame", "__file", "__func")):
                    continue
                print(f"<INTROSPECT> {__file}:{__func} - {k}:{v.__class__.__name__}")

            @metric_partial(
                engine=engine,
                partial_fn_type=partial_fn_type,
                domain_type=domain_type,
                **kwargs,
            )
            @wraps(metric_fn)
            def inner_func(
                cls,
                execution_engine: PandasExecutionEngine,
                metric_domain_kwargs: Dict,
                metric_value_kwargs: Dict,
                metrics: Dict[(str, Any)],
                runtime_configuration: Dict,
            ):
                import inspect

                __frame = inspect.currentframe()
                __file = __frame.f_code.co_filename
                __func = __frame.f_code.co_name
                for (k, v) in __frame.f_locals.items():
                    if any((var in k) for var in ("__frame", "__file", "__func")):
                        continue
                    print(
                        f"<INTROSPECT> {__file}:{__func} - {k}:{v.__class__.__name__}"
                    )
                (
                    df,
                    compute_domain_kwargs,
                    accessor_domain_kwargs,
                ) = execution_engine.get_compute_domain(
                    domain_kwargs=metric_domain_kwargs, domain_type=domain_type
                )
                column_A_name = accessor_domain_kwargs["column_A"]
                column_B_name = accessor_domain_kwargs["column_B"]
                column_list = [column_A_name, column_B_name]
                for column_name in column_list:
                    if column_name not in metrics["table.columns"]:
                        raise ge_exceptions.InvalidMetricAccessorDomainKwargsKeyError(
                            message=f'Error: The column "{column_name}" in BatchData does not exist.'
                        )
                values = metric_fn(
                    cls,
                    df[column_A_name],
                    df[column_B_name],
                    **metric_value_kwargs,
                    _metrics=metrics,
                )
                return (values, compute_domain_kwargs, accessor_domain_kwargs)

            return inner_func

        return wrapper
    elif issubclass(engine, SqlAlchemyExecutionEngine):
        if partial_fn_type is None:
            partial_fn_type = MetricPartialFunctionTypes.MAP_FN
        partial_fn_type = MetricPartialFunctionTypes(partial_fn_type)
        if partial_fn_type != MetricPartialFunctionTypes.MAP_FN:
            raise ValueError(
                "SqlAlchemyExecutionEngine only supports map_fn for column_pair_function_partial partial_fn_type"
            )

        def wrapper(metric_fn: Callable):
            import inspect

            __frame = inspect.currentframe()
            __file = __frame.f_code.co_filename
            __func = __frame.f_code.co_name
            for (k, v) in __frame.f_locals.items():
                if any((var in k) for var in ("__frame", "__file", "__func")):
                    continue
                print(f"<INTROSPECT> {__file}:{__func} - {k}:{v.__class__.__name__}")

            @metric_partial(
                engine=engine,
                partial_fn_type=partial_fn_type,
                domain_type=domain_type,
                **kwargs,
            )
            @wraps(metric_fn)
            def inner_func(
                cls,
                execution_engine: SqlAlchemyExecutionEngine,
                metric_domain_kwargs: Dict,
                metric_value_kwargs: Dict,
                metrics: Dict[(str, Any)],
                runtime_configuration: Dict,
            ):
                import inspect

                __frame = inspect.currentframe()
                __file = __frame.f_code.co_filename
                __func = __frame.f_code.co_name
                for (k, v) in __frame.f_locals.items():
                    if any((var in k) for var in ("__frame", "__file", "__func")):
                        continue
                    print(
                        f"<INTROSPECT> {__file}:{__func} - {k}:{v.__class__.__name__}"
                    )
                (
                    selectable,
                    compute_domain_kwargs,
                    accessor_domain_kwargs,
                ) = execution_engine.get_compute_domain(
                    domain_kwargs=metric_domain_kwargs, domain_type=domain_type
                )
                column_A_name = accessor_domain_kwargs["column_A"]
                column_B_name = accessor_domain_kwargs["column_B"]
                column_list = [column_A_name, column_B_name]
                for column_name in column_list:
                    if column_name not in metrics["table.columns"]:
                        raise ge_exceptions.InvalidMetricAccessorDomainKwargsKeyError(
                            message=f'Error: The column "{column_name}" in BatchData does not exist.'
                        )
                column_pair_function = metric_fn(
                    cls,
                    sa.column(column_A_name),
                    sa.column(column_B_name),
                    **metric_value_kwargs,
                    _metrics=metrics,
                )
                return (
                    column_pair_function,
                    compute_domain_kwargs,
                    accessor_domain_kwargs,
                )

            return inner_func

        return wrapper
    elif issubclass(engine, SparkDFExecutionEngine):
        if partial_fn_type is None:
            partial_fn_type = MetricPartialFunctionTypes.MAP_FN
        partial_fn_type = MetricPartialFunctionTypes(partial_fn_type)
        if partial_fn_type != MetricPartialFunctionTypes.MAP_FN:
            raise ValueError(
                "SparkDFExecutionEngine only supports map_fn for column_pair_function_partial partial_fn_type"
            )

        def wrapper(metric_fn: Callable):
            import inspect

            __frame = inspect.currentframe()
            __file = __frame.f_code.co_filename
            __func = __frame.f_code.co_name
            for (k, v) in __frame.f_locals.items():
                if any((var in k) for var in ("__frame", "__file", "__func")):
                    continue
                print(f"<INTROSPECT> {__file}:{__func} - {k}:{v.__class__.__name__}")

            @metric_partial(
                engine=engine,
                partial_fn_type=partial_fn_type,
                domain_type=domain_type,
                **kwargs,
            )
            @wraps(metric_fn)
            def inner_func(
                cls,
                execution_engine: SparkDFExecutionEngine,
                metric_domain_kwargs: Dict,
                metric_value_kwargs: Dict,
                metrics: Dict[(str, Any)],
                runtime_configuration: Dict,
            ):
                import inspect

                __frame = inspect.currentframe()
                __file = __frame.f_code.co_filename
                __func = __frame.f_code.co_name
                for (k, v) in __frame.f_locals.items():
                    if any((var in k) for var in ("__frame", "__file", "__func")):
                        continue
                    print(
                        f"<INTROSPECT> {__file}:{__func} - {k}:{v.__class__.__name__}"
                    )
                (
                    data,
                    compute_domain_kwargs,
                    accessor_domain_kwargs,
                ) = execution_engine.get_compute_domain(
                    domain_kwargs=metric_domain_kwargs, domain_type=domain_type
                )
                column_A_name = accessor_domain_kwargs["column_A"]
                column_B_name = accessor_domain_kwargs["column_B"]
                column_list = [column_A_name, column_B_name]
                for column_name in column_list:
                    if column_name not in metrics["table.columns"]:
                        raise ge_exceptions.InvalidMetricAccessorDomainKwargsKeyError(
                            message=f'Error: The column "{column_name}" in BatchData does not exist.'
                        )
                column_pair_function = metric_fn(
                    cls,
                    data[column_A_name],
                    data[column_B_name],
                    **metric_value_kwargs,
                    _metrics=metrics,
                )
                return (
                    column_pair_function,
                    compute_domain_kwargs,
                    accessor_domain_kwargs,
                )

            return inner_func

        return wrapper
    else:
        raise ValueError("Unsupported engine for column_pair_function_partial")


def column_pair_condition_partial(
    engine: Type[ExecutionEngine],
    partial_fn_type: Optional[Union[(str, MetricPartialFunctionTypes)]] = None,
    **kwargs,
):
    import inspect

    __frame = inspect.currentframe()
    __file = __frame.f_code.co_filename
    __func = __frame.f_code.co_name
    for (k, v) in __frame.f_locals.items():
        if any((var in k) for var in ("__frame", "__file", "__func")):
            continue
        print(f"<INTROSPECT> {__file}:{__func} - {k}:{v.__class__.__name__}")
    "Provides engine-specific support for authoring a metric_fn with a simplified signature. A\n    column_pair_condition_partial must provide a map function that evaluates to a boolean value; it will be used to\n    provide supplemental metrics, such as the unexpected_value count, unexpected_values, and unexpected_rows.\n\n    A metric function that is decorated as a column_pair_condition_partial will be called with the engine-specific\n    column_list type and any value_kwargs associated with the Metric for which the provider function is being declared.\n\n    Args:\n        engine:\n        partial_fn_type:\n        **kwargs:\n\n    Returns:\n        An annotated metric_function which will be called with a simplified signature.\n\n    "
    domain_type = MetricDomainTypes.COLUMN_PAIR
    if issubclass(engine, PandasExecutionEngine):
        if partial_fn_type is None:
            partial_fn_type = MetricPartialFunctionTypes.MAP_CONDITION_SERIES
        partial_fn_type = MetricPartialFunctionTypes(partial_fn_type)
        if partial_fn_type not in [MetricPartialFunctionTypes.MAP_CONDITION_SERIES]:
            raise ValueError(
                "PandasExecutionEngine only supports map_condition_series for column_pair_condition_partial partial_fn_type"
            )

        def wrapper(metric_fn: Callable):
            import inspect

            __frame = inspect.currentframe()
            __file = __frame.f_code.co_filename
            __func = __frame.f_code.co_name
            for (k, v) in __frame.f_locals.items():
                if any((var in k) for var in ("__frame", "__file", "__func")):
                    continue
                print(f"<INTROSPECT> {__file}:{__func} - {k}:{v.__class__.__name__}")

            @metric_partial(
                engine=engine,
                partial_fn_type=partial_fn_type,
                domain_type=domain_type,
                **kwargs,
            )
            @wraps(metric_fn)
            def inner_func(
                cls,
                execution_engine: PandasExecutionEngine,
                metric_domain_kwargs: Dict,
                metric_value_kwargs: Dict,
                metrics: Dict[(str, Any)],
                runtime_configuration: Dict,
            ):
                import inspect

                __frame = inspect.currentframe()
                __file = __frame.f_code.co_filename
                __func = __frame.f_code.co_name
                for (k, v) in __frame.f_locals.items():
                    if any((var in k) for var in ("__frame", "__file", "__func")):
                        continue
                    print(
                        f"<INTROSPECT> {__file}:{__func} - {k}:{v.__class__.__name__}"
                    )
                (
                    df,
                    compute_domain_kwargs,
                    accessor_domain_kwargs,
                ) = execution_engine.get_compute_domain(
                    domain_kwargs=metric_domain_kwargs, domain_type=domain_type
                )
                column_A_name = accessor_domain_kwargs["column_A"]
                column_B_name = accessor_domain_kwargs["column_B"]
                column_list = [column_A_name, column_B_name]
                for column_name in column_list:
                    if column_name not in metrics["table.columns"]:
                        raise ge_exceptions.InvalidMetricAccessorDomainKwargsKeyError(
                            message=f'Error: The column "{column_name}" in BatchData does not exist.'
                        )
                meets_expectation_series = metric_fn(
                    cls,
                    df[column_A_name],
                    df[column_B_name],
                    **metric_value_kwargs,
                    _metrics=metrics,
                )
                return (
                    (~meets_expectation_series),
                    compute_domain_kwargs,
                    accessor_domain_kwargs,
                )

            return inner_func

        return wrapper
    elif issubclass(engine, SqlAlchemyExecutionEngine):
        if partial_fn_type is None:
            partial_fn_type = MetricPartialFunctionTypes.MAP_CONDITION_FN
        partial_fn_type = MetricPartialFunctionTypes(partial_fn_type)
        if partial_fn_type not in [
            MetricPartialFunctionTypes.MAP_CONDITION_FN,
            MetricPartialFunctionTypes.WINDOW_CONDITION_FN,
        ]:
            raise ValueError(
                "SqlAlchemyExecutionEngine only supports map_condition_fn and window_condition_fn for column_pair_condition_partial partial_fn_type"
            )

        def wrapper(metric_fn: Callable):
            import inspect

            __frame = inspect.currentframe()
            __file = __frame.f_code.co_filename
            __func = __frame.f_code.co_name
            for (k, v) in __frame.f_locals.items():
                if any((var in k) for var in ("__frame", "__file", "__func")):
                    continue
                print(f"<INTROSPECT> {__file}:{__func} - {k}:{v.__class__.__name__}")

            @metric_partial(
                engine=engine,
                partial_fn_type=partial_fn_type,
                domain_type=domain_type,
                **kwargs,
            )
            @wraps(metric_fn)
            def inner_func(
                cls,
                execution_engine: SqlAlchemyExecutionEngine,
                metric_domain_kwargs: Dict,
                metric_value_kwargs: Dict,
                metrics: Dict[(str, Any)],
                runtime_configuration: Dict,
            ):
                import inspect

                __frame = inspect.currentframe()
                __file = __frame.f_code.co_filename
                __func = __frame.f_code.co_name
                for (k, v) in __frame.f_locals.items():
                    if any((var in k) for var in ("__frame", "__file", "__func")):
                        continue
                    print(
                        f"<INTROSPECT> {__file}:{__func} - {k}:{v.__class__.__name__}"
                    )
                (
                    selectable,
                    compute_domain_kwargs,
                    accessor_domain_kwargs,
                ) = execution_engine.get_compute_domain(
                    domain_kwargs=metric_domain_kwargs, domain_type=domain_type
                )
                column_A_name = accessor_domain_kwargs["column_A"]
                column_B_name = accessor_domain_kwargs["column_B"]
                column_list = [column_A_name, column_B_name]
                for column_name in column_list:
                    if column_name not in metrics["table.columns"]:
                        raise ge_exceptions.InvalidMetricAccessorDomainKwargsKeyError(
                            message=f'Error: The column "{column_name}" in BatchData does not exist.'
                        )
                sqlalchemy_engine: Engine = execution_engine.engine
                dialect = execution_engine.dialect_module
                expected_condition = metric_fn(
                    cls,
                    sa.column(column_A_name),
                    sa.column(column_B_name),
                    **metric_value_kwargs,
                    _dialect=dialect,
                    _table=selectable,
                    _sqlalchemy_engine=sqlalchemy_engine,
                    _metrics=metrics,
                )
                unexpected_condition = sa.not_(expected_condition)
                return (
                    unexpected_condition,
                    compute_domain_kwargs,
                    accessor_domain_kwargs,
                )

            return inner_func

        return wrapper
    elif issubclass(engine, SparkDFExecutionEngine):
        if partial_fn_type is None:
            partial_fn_type = MetricPartialFunctionTypes.MAP_CONDITION_FN
        partial_fn_type = MetricPartialFunctionTypes(partial_fn_type)
        if partial_fn_type not in [
            MetricPartialFunctionTypes.MAP_CONDITION_FN,
            MetricPartialFunctionTypes.WINDOW_CONDITION_FN,
        ]:
            raise ValueError(
                "SparkDFExecutionEngine only supports map_condition_fn and window_condition_fn for column_pair_condition_partial partial_fn_type"
            )

        def wrapper(metric_fn: Callable):
            import inspect

            __frame = inspect.currentframe()
            __file = __frame.f_code.co_filename
            __func = __frame.f_code.co_name
            for (k, v) in __frame.f_locals.items():
                if any((var in k) for var in ("__frame", "__file", "__func")):
                    continue
                print(f"<INTROSPECT> {__file}:{__func} - {k}:{v.__class__.__name__}")

            @metric_partial(
                engine=engine,
                partial_fn_type=partial_fn_type,
                domain_type=domain_type,
                **kwargs,
            )
            @wraps(metric_fn)
            def inner_func(
                cls,
                execution_engine: SparkDFExecutionEngine,
                metric_domain_kwargs: Dict,
                metric_value_kwargs: Dict,
                metrics: Dict[(str, Any)],
                runtime_configuration: Dict,
            ):
                import inspect

                __frame = inspect.currentframe()
                __file = __frame.f_code.co_filename
                __func = __frame.f_code.co_name
                for (k, v) in __frame.f_locals.items():
                    if any((var in k) for var in ("__frame", "__file", "__func")):
                        continue
                    print(
                        f"<INTROSPECT> {__file}:{__func} - {k}:{v.__class__.__name__}"
                    )
                (
                    data,
                    compute_domain_kwargs,
                    accessor_domain_kwargs,
                ) = execution_engine.get_compute_domain(
                    domain_kwargs=metric_domain_kwargs, domain_type=domain_type
                )
                column_A_name = accessor_domain_kwargs["column_A"]
                column_B_name = accessor_domain_kwargs["column_B"]
                column_list = [column_A_name, column_B_name]
                for column_name in column_list:
                    if column_name not in metrics["table.columns"]:
                        raise ge_exceptions.InvalidMetricAccessorDomainKwargsKeyError(
                            message=f'Error: The column "{column_name}" in BatchData does not exist.'
                        )
                expected_condition = metric_fn(
                    cls,
                    data[column_A_name],
                    data[column_B_name],
                    **metric_value_kwargs,
                    _metrics=metrics,
                )
                return (
                    (~expected_condition),
                    compute_domain_kwargs,
                    accessor_domain_kwargs,
                )

            return inner_func

        return wrapper
    else:
        raise ValueError("Unsupported engine for column_pair_condition_partial")


def multicolumn_function_partial(
    engine: Type[ExecutionEngine], partial_fn_type: str = None, **kwargs
):
    import inspect

    __frame = inspect.currentframe()
    __file = __frame.f_code.co_filename
    __func = __frame.f_code.co_name
    for (k, v) in __frame.f_locals.items():
        if any((var in k) for var in ("__frame", "__file", "__func")):
            continue
        print(f"<INTROSPECT> {__file}:{__func} - {k}:{v.__class__.__name__}")
    "Provides engine-specific support for authoring a metric_fn with a simplified signature.\n\n    A metric function that is decorated as a multicolumn_function_partial will be called with the engine-specific\n    column_list type and any value_kwargs associated with the Metric for which the provider function is being declared.\n\n    Args:\n        engine:\n        partial_fn_type:\n        **kwargs:\n\n    Returns:\n        An annotated metric_function which will be called with a simplified signature.\n\n    "
    domain_type = MetricDomainTypes.MULTICOLUMN
    if issubclass(engine, PandasExecutionEngine):
        if partial_fn_type is None:
            partial_fn_type = MetricPartialFunctionTypes.MAP_SERIES
        partial_fn_type = MetricPartialFunctionTypes(partial_fn_type)
        if partial_fn_type != MetricPartialFunctionTypes.MAP_SERIES:
            raise ValueError(
                "PandasExecutionEngine only supports map_series for multicolumn_function_partial partial_fn_type"
            )

        def wrapper(metric_fn: Callable):
            import inspect

            __frame = inspect.currentframe()
            __file = __frame.f_code.co_filename
            __func = __frame.f_code.co_name
            for (k, v) in __frame.f_locals.items():
                if any((var in k) for var in ("__frame", "__file", "__func")):
                    continue
                print(f"<INTROSPECT> {__file}:{__func} - {k}:{v.__class__.__name__}")

            @metric_partial(
                engine=engine,
                partial_fn_type=partial_fn_type,
                domain_type=domain_type,
                **kwargs,
            )
            @wraps(metric_fn)
            def inner_func(
                cls,
                execution_engine: PandasExecutionEngine,
                metric_domain_kwargs: Dict,
                metric_value_kwargs: Dict,
                metrics: Dict[(str, Any)],
                runtime_configuration: Dict,
            ):
                import inspect

                __frame = inspect.currentframe()
                __file = __frame.f_code.co_filename
                __func = __frame.f_code.co_name
                for (k, v) in __frame.f_locals.items():
                    if any((var in k) for var in ("__frame", "__file", "__func")):
                        continue
                    print(
                        f"<INTROSPECT> {__file}:{__func} - {k}:{v.__class__.__name__}"
                    )
                (
                    df,
                    compute_domain_kwargs,
                    accessor_domain_kwargs,
                ) = execution_engine.get_compute_domain(
                    domain_kwargs=metric_domain_kwargs, domain_type=domain_type
                )
                column_list = accessor_domain_kwargs["column_list"]
                for column_name in column_list:
                    if column_name not in metrics["table.columns"]:
                        raise ge_exceptions.InvalidMetricAccessorDomainKwargsKeyError(
                            message=f'Error: The column "{column_name}" in BatchData does not exist.'
                        )
                values = metric_fn(
                    cls, df[column_list], **metric_value_kwargs, _metrics=metrics
                )
                return (values, compute_domain_kwargs, accessor_domain_kwargs)

            return inner_func

        return wrapper
    elif issubclass(engine, SqlAlchemyExecutionEngine):
        if partial_fn_type is None:
            partial_fn_type = MetricPartialFunctionTypes.MAP_FN
        partial_fn_type = MetricPartialFunctionTypes(partial_fn_type)
        if partial_fn_type != MetricPartialFunctionTypes.MAP_FN:
            raise ValueError(
                "SqlAlchemyExecutionEngine only supports map_fn for multicolumn_function_partial partial_fn_type"
            )

        def wrapper(metric_fn: Callable):
            import inspect

            __frame = inspect.currentframe()
            __file = __frame.f_code.co_filename
            __func = __frame.f_code.co_name
            for (k, v) in __frame.f_locals.items():
                if any((var in k) for var in ("__frame", "__file", "__func")):
                    continue
                print(f"<INTROSPECT> {__file}:{__func} - {k}:{v.__class__.__name__}")

            @metric_partial(
                engine=engine,
                partial_fn_type=partial_fn_type,
                domain_type=domain_type,
                **kwargs,
            )
            @wraps(metric_fn)
            def inner_func(
                cls,
                execution_engine: SqlAlchemyExecutionEngine,
                metric_domain_kwargs: Dict,
                metric_value_kwargs: Dict,
                metrics: Dict[(str, Any)],
                runtime_configuration: Dict,
            ):
                import inspect

                __frame = inspect.currentframe()
                __file = __frame.f_code.co_filename
                __func = __frame.f_code.co_name
                for (k, v) in __frame.f_locals.items():
                    if any((var in k) for var in ("__frame", "__file", "__func")):
                        continue
                    print(
                        f"<INTROSPECT> {__file}:{__func} - {k}:{v.__class__.__name__}"
                    )
                (
                    selectable,
                    compute_domain_kwargs,
                    accessor_domain_kwargs,
                ) = execution_engine.get_compute_domain(
                    domain_kwargs=metric_domain_kwargs, domain_type=domain_type
                )
                column_list = accessor_domain_kwargs["column_list"]
                table_columns = metrics["table.columns"]
                for column_name in column_list:
                    if column_name not in table_columns:
                        raise ge_exceptions.InvalidMetricAccessorDomainKwargsKeyError(
                            message=f'Error: The column "{column_name}" in BatchData does not exist.'
                        )
                sqlalchemy_engine: Engine = execution_engine.engine
                column_selector = [
                    sa.column(column_name) for column_name in column_list
                ]
                dialect = execution_engine.dialect_module
                multicolumn_function = metric_fn(
                    cls,
                    column_selector,
                    **metric_value_kwargs,
                    _column_names=column_list,
                    _table_columns=table_columns,
                    _dialect=dialect,
                    _table=selectable,
                    _sqlalchemy_engine=sqlalchemy_engine,
                    _metrics=metrics,
                )
                return (
                    multicolumn_function,
                    compute_domain_kwargs,
                    accessor_domain_kwargs,
                )

            return inner_func

        return wrapper
    elif issubclass(engine, SparkDFExecutionEngine):
        if partial_fn_type is None:
            partial_fn_type = MetricPartialFunctionTypes.MAP_FN
        partial_fn_type = MetricPartialFunctionTypes(partial_fn_type)
        if partial_fn_type != MetricPartialFunctionTypes.MAP_FN:
            raise ValueError(
                "SparkDFExecutionEngine only supports map_fn for multicolumn_function_partial partial_fn_type"
            )

        def wrapper(metric_fn: Callable):
            import inspect

            __frame = inspect.currentframe()
            __file = __frame.f_code.co_filename
            __func = __frame.f_code.co_name
            for (k, v) in __frame.f_locals.items():
                if any((var in k) for var in ("__frame", "__file", "__func")):
                    continue
                print(f"<INTROSPECT> {__file}:{__func} - {k}:{v.__class__.__name__}")

            @metric_partial(
                engine=engine,
                partial_fn_type=partial_fn_type,
                domain_type=domain_type,
                **kwargs,
            )
            @wraps(metric_fn)
            def inner_func(
                cls,
                execution_engine: SparkDFExecutionEngine,
                metric_domain_kwargs: Dict,
                metric_value_kwargs: Dict,
                metrics: Dict[(str, Any)],
                runtime_configuration: Dict,
            ):
                import inspect

                __frame = inspect.currentframe()
                __file = __frame.f_code.co_filename
                __func = __frame.f_code.co_name
                for (k, v) in __frame.f_locals.items():
                    if any((var in k) for var in ("__frame", "__file", "__func")):
                        continue
                    print(
                        f"<INTROSPECT> {__file}:{__func} - {k}:{v.__class__.__name__}"
                    )
                (
                    data,
                    compute_domain_kwargs,
                    accessor_domain_kwargs,
                ) = execution_engine.get_compute_domain(
                    domain_kwargs=metric_domain_kwargs, domain_type=domain_type
                )
                column_list = accessor_domain_kwargs["column_list"]
                for column_name in column_list:
                    if column_name not in metrics["table.columns"]:
                        raise ge_exceptions.InvalidMetricAccessorDomainKwargsKeyError(
                            message=f'Error: The column "{column_name}" in BatchData does not exist.'
                        )
                multicolumn_function = metric_fn(
                    cls, data[column_list], **metric_value_kwargs, _metrics=metrics
                )
                return (
                    multicolumn_function,
                    compute_domain_kwargs,
                    accessor_domain_kwargs,
                )

            return inner_func

        return wrapper
    else:
        raise ValueError("Unsupported engine for multicolumn_function_partial")


def multicolumn_condition_partial(
    engine: Type[ExecutionEngine],
    partial_fn_type: Optional[Union[(str, MetricPartialFunctionTypes)]] = None,
    **kwargs,
):
    import inspect

    __frame = inspect.currentframe()
    __file = __frame.f_code.co_filename
    __func = __frame.f_code.co_name
    for (k, v) in __frame.f_locals.items():
        if any((var in k) for var in ("__frame", "__file", "__func")):
            continue
        print(f"<INTROSPECT> {__file}:{__func} - {k}:{v.__class__.__name__}")
    "Provides engine-specific support for authoring a metric_fn with a simplified signature. A\n    multicolumn_condition_partial must provide a map function that evaluates to a boolean value; it will be used to\n    provide supplemental metrics, such as the unexpected_value count, unexpected_values, and unexpected_rows.\n\n    A metric function that is decorated as a multicolumn_condition_partial will be called with the engine-specific\n    column_list type and any value_kwargs associated with the Metric for which the provider function is being declared.\n\n    Args:\n        engine:\n        partial_fn_type:\n        **kwargs:\n\n    Returns:\n        An annotated metric_function which will be called with a simplified signature.\n\n    "
    domain_type = MetricDomainTypes.MULTICOLUMN
    if issubclass(engine, PandasExecutionEngine):
        if partial_fn_type is None:
            partial_fn_type = MetricPartialFunctionTypes.MAP_CONDITION_SERIES
        partial_fn_type = MetricPartialFunctionTypes(partial_fn_type)
        if partial_fn_type not in [MetricPartialFunctionTypes.MAP_CONDITION_SERIES]:
            raise ValueError(
                "PandasExecutionEngine only supports map_condition_series for multicolumn_condition_partial partial_fn_type"
            )

        def wrapper(metric_fn: Callable):
            import inspect

            __frame = inspect.currentframe()
            __file = __frame.f_code.co_filename
            __func = __frame.f_code.co_name
            for (k, v) in __frame.f_locals.items():
                if any((var in k) for var in ("__frame", "__file", "__func")):
                    continue
                print(f"<INTROSPECT> {__file}:{__func} - {k}:{v.__class__.__name__}")

            @metric_partial(
                engine=engine,
                partial_fn_type=partial_fn_type,
                domain_type=domain_type,
                **kwargs,
            )
            @wraps(metric_fn)
            def inner_func(
                cls,
                execution_engine: PandasExecutionEngine,
                metric_domain_kwargs: Dict,
                metric_value_kwargs: Dict,
                metrics: Dict[(str, Any)],
                runtime_configuration: Dict,
            ):
                import inspect

                __frame = inspect.currentframe()
                __file = __frame.f_code.co_filename
                __func = __frame.f_code.co_name
                for (k, v) in __frame.f_locals.items():
                    if any((var in k) for var in ("__frame", "__file", "__func")):
                        continue
                    print(
                        f"<INTROSPECT> {__file}:{__func} - {k}:{v.__class__.__name__}"
                    )
                (
                    df,
                    compute_domain_kwargs,
                    accessor_domain_kwargs,
                ) = execution_engine.get_compute_domain(
                    domain_kwargs=metric_domain_kwargs, domain_type=domain_type
                )
                column_list = accessor_domain_kwargs["column_list"]
                for column_name in column_list:
                    if column_name not in metrics["table.columns"]:
                        raise ge_exceptions.InvalidMetricAccessorDomainKwargsKeyError(
                            message=f'Error: The column "{column_name}" in BatchData does not exist.'
                        )
                meets_expectation_series = metric_fn(
                    cls, df[column_list], **metric_value_kwargs, _metrics=metrics
                )
                return (
                    (~meets_expectation_series),
                    compute_domain_kwargs,
                    accessor_domain_kwargs,
                )

            return inner_func

        return wrapper
    elif issubclass(engine, SqlAlchemyExecutionEngine):
        if partial_fn_type is None:
            partial_fn_type = MetricPartialFunctionTypes.MAP_CONDITION_FN
        partial_fn_type = MetricPartialFunctionTypes(partial_fn_type)
        if partial_fn_type not in [
            MetricPartialFunctionTypes.MAP_CONDITION_FN,
            MetricPartialFunctionTypes.WINDOW_CONDITION_FN,
        ]:
            raise ValueError(
                "SqlAlchemyExecutionEngine only supports map_condition_fn and window_condition_fn for multicolumn_condition_partial partial_fn_type"
            )

        def wrapper(metric_fn: Callable):
            import inspect

            __frame = inspect.currentframe()
            __file = __frame.f_code.co_filename
            __func = __frame.f_code.co_name
            for (k, v) in __frame.f_locals.items():
                if any((var in k) for var in ("__frame", "__file", "__func")):
                    continue
                print(f"<INTROSPECT> {__file}:{__func} - {k}:{v.__class__.__name__}")

            @metric_partial(
                engine=engine,
                partial_fn_type=partial_fn_type,
                domain_type=domain_type,
                **kwargs,
            )
            @wraps(metric_fn)
            def inner_func(
                cls,
                execution_engine: SqlAlchemyExecutionEngine,
                metric_domain_kwargs: Dict,
                metric_value_kwargs: Dict,
                metrics: Dict[(str, Any)],
                runtime_configuration: Dict,
            ):
                import inspect

                __frame = inspect.currentframe()
                __file = __frame.f_code.co_filename
                __func = __frame.f_code.co_name
                for (k, v) in __frame.f_locals.items():
                    if any((var in k) for var in ("__frame", "__file", "__func")):
                        continue
                    print(
                        f"<INTROSPECT> {__file}:{__func} - {k}:{v.__class__.__name__}"
                    )
                (
                    selectable,
                    compute_domain_kwargs,
                    accessor_domain_kwargs,
                ) = execution_engine.get_compute_domain(
                    domain_kwargs=metric_domain_kwargs, domain_type=domain_type
                )
                column_list = accessor_domain_kwargs["column_list"]
                for column_name in column_list:
                    if column_name not in metrics["table.columns"]:
                        raise ge_exceptions.InvalidMetricAccessorDomainKwargsKeyError(
                            message=f'Error: The column "{column_name}" in BatchData does not exist.'
                        )
                sqlalchemy_engine: Engine = execution_engine.engine
                column_selector = [
                    sa.column(column_name) for column_name in column_list
                ]
                dialect = execution_engine.dialect_module
                expected_condition = metric_fn(
                    cls,
                    column_selector,
                    **metric_value_kwargs,
                    _dialect=dialect,
                    _table=selectable,
                    _sqlalchemy_engine=sqlalchemy_engine,
                    _metrics=metrics,
                )
                unexpected_condition = sa.not_(expected_condition)
                return (
                    unexpected_condition,
                    compute_domain_kwargs,
                    accessor_domain_kwargs,
                )

            return inner_func

        return wrapper
    elif issubclass(engine, SparkDFExecutionEngine):
        if partial_fn_type is None:
            partial_fn_type = MetricPartialFunctionTypes.MAP_CONDITION_FN
        partial_fn_type = MetricPartialFunctionTypes(partial_fn_type)
        if partial_fn_type not in [
            MetricPartialFunctionTypes.MAP_CONDITION_FN,
            MetricPartialFunctionTypes.WINDOW_CONDITION_FN,
        ]:
            raise ValueError(
                "SparkDFExecutionEngine only supports map_condition_fn and window_condition_fn for multicolumn_condition_partial partial_fn_type"
            )

        def wrapper(metric_fn: Callable):
            import inspect

            __frame = inspect.currentframe()
            __file = __frame.f_code.co_filename
            __func = __frame.f_code.co_name
            for (k, v) in __frame.f_locals.items():
                if any((var in k) for var in ("__frame", "__file", "__func")):
                    continue
                print(f"<INTROSPECT> {__file}:{__func} - {k}:{v.__class__.__name__}")

            @metric_partial(
                engine=engine,
                partial_fn_type=partial_fn_type,
                domain_type=domain_type,
                **kwargs,
            )
            @wraps(metric_fn)
            def inner_func(
                cls,
                execution_engine: SparkDFExecutionEngine,
                metric_domain_kwargs: Dict,
                metric_value_kwargs: Dict,
                metrics: Dict[(str, Any)],
                runtime_configuration: Dict,
            ):
                import inspect

                __frame = inspect.currentframe()
                __file = __frame.f_code.co_filename
                __func = __frame.f_code.co_name
                for (k, v) in __frame.f_locals.items():
                    if any((var in k) for var in ("__frame", "__file", "__func")):
                        continue
                    print(
                        f"<INTROSPECT> {__file}:{__func} - {k}:{v.__class__.__name__}"
                    )
                (
                    data,
                    compute_domain_kwargs,
                    accessor_domain_kwargs,
                ) = execution_engine.get_compute_domain(
                    domain_kwargs=metric_domain_kwargs, domain_type=domain_type
                )
                column_list = accessor_domain_kwargs["column_list"]
                for column_name in column_list:
                    if column_name not in metrics["table.columns"]:
                        raise ge_exceptions.InvalidMetricAccessorDomainKwargsKeyError(
                            message=f'Error: The column "{column_name}" in BatchData does not exist.'
                        )
                expected_condition = metric_fn(
                    cls, data[column_list], **metric_value_kwargs, _metrics=metrics
                )
                return (
                    (~expected_condition),
                    compute_domain_kwargs,
                    accessor_domain_kwargs,
                )

            return inner_func

        return wrapper
    else:
        raise ValueError("Unsupported engine for multicolumn_condition_partial")


def _pandas_map_condition_unexpected_count(
    cls,
    execution_engine: PandasExecutionEngine,
    metric_domain_kwargs: Dict,
    metric_value_kwargs: Dict,
    metrics: Dict[(str, Any)],
    **kwargs,
):
    import inspect

    __frame = inspect.currentframe()
    __file = __frame.f_code.co_filename
    __func = __frame.f_code.co_name
    for (k, v) in __frame.f_locals.items():
        if any((var in k) for var in ("__frame", "__file", "__func")):
            continue
        print(f"<INTROSPECT> {__file}:{__func} - {k}:{v.__class__.__name__}")
    "Returns unexpected count for MapExpectations"
    return np.count_nonzero(metrics["unexpected_condition"][0])


def _pandas_column_map_condition_values(
    cls,
    execution_engine: PandasExecutionEngine,
    metric_domain_kwargs: Dict,
    metric_value_kwargs: Dict,
    metrics: Dict[(str, Any)],
    **kwargs,
):
    import inspect

    __frame = inspect.currentframe()
    __file = __frame.f_code.co_filename
    __func = __frame.f_code.co_name
    for (k, v) in __frame.f_locals.items():
        if any((var in k) for var in ("__frame", "__file", "__func")):
            continue
        print(f"<INTROSPECT> {__file}:{__func} - {k}:{v.__class__.__name__}")
    "Return values from the specified domain that match the map-style metric in the metrics dictionary."
    (
        boolean_mapped_unexpected_values,
        compute_domain_kwargs,
        accessor_domain_kwargs,
    ) = metrics["unexpected_condition"]
    df = execution_engine.get_domain_records(domain_kwargs=compute_domain_kwargs)
    filter_column_isnull = kwargs.get(
        "filter_column_isnull", getattr(cls, "filter_column_isnull", False)
    )
    if "column" not in accessor_domain_kwargs:
        raise ValueError(
            'No "column" found in provided metric_domain_kwargs, but it is required for a column map metric\n(_pandas_column_map_condition_values).\n'
        )
    column_name = accessor_domain_kwargs["column"]
    if column_name not in metrics["table.columns"]:
        raise ge_exceptions.InvalidMetricAccessorDomainKwargsKeyError(
            message=f'Error: The column "{column_name}" in BatchData does not exist.'
        )
    if filter_column_isnull:
        df = df[df[column_name].notnull()]
    domain_values = df[column_name]
    domain_values = domain_values[(boolean_mapped_unexpected_values == True)]
    result_format = metric_value_kwargs["result_format"]
    if result_format["result_format"] == "COMPLETE":
        return list(domain_values)
    else:
        return list(domain_values[: result_format["partial_unexpected_count"]])


def _pandas_column_pair_map_condition_values(
    cls,
    execution_engine: PandasExecutionEngine,
    metric_domain_kwargs: Dict,
    metric_value_kwargs: Dict,
    metrics: Dict[(str, Any)],
    **kwargs,
):
    import inspect

    __frame = inspect.currentframe()
    __file = __frame.f_code.co_filename
    __func = __frame.f_code.co_name
    for (k, v) in __frame.f_locals.items():
        if any((var in k) for var in ("__frame", "__file", "__func")):
            continue
        print(f"<INTROSPECT> {__file}:{__func} - {k}:{v.__class__.__name__}")
    "Return values from the specified domain that match the map-style metric in the metrics dictionary."
    (
        boolean_mapped_unexpected_values,
        compute_domain_kwargs,
        accessor_domain_kwargs,
    ) = metrics["unexpected_condition"]
    '\n    In order to invoke the "ignore_row_if" filtering logic, "execution_engine.get_domain_records()" must be supplied\n    with all of the available "domain_kwargs" keys.\n    '
    domain_kwargs = dict(**compute_domain_kwargs, **accessor_domain_kwargs)
    df = execution_engine.get_domain_records(domain_kwargs=domain_kwargs)
    if not (("column_A" in domain_kwargs) and ("column_B" in domain_kwargs)):
        raise ValueError(
            'No "column_A" and "column_B" found in provided metric_domain_kwargs, but it is required for a column pair map metric\n(_pandas_column_pair_map_condition_values).\n'
        )
    column_A_name = accessor_domain_kwargs["column_A"]
    column_B_name = accessor_domain_kwargs["column_B"]
    column_list = [column_A_name, column_B_name]
    for column_name in column_list:
        if column_name not in metrics["table.columns"]:
            raise ge_exceptions.InvalidMetricAccessorDomainKwargsKeyError(
                message=f'Error: The column "{column_name}" in BatchData does not exist.'
            )
    domain_values = df[column_list]
    domain_values = domain_values[(boolean_mapped_unexpected_values == True)]
    result_format = metric_value_kwargs["result_format"]
    unexpected_list = [
        value_pair
        for value_pair in zip(
            domain_values[column_A_name].values, domain_values[column_B_name].values
        )
    ]
    if result_format["result_format"] == "COMPLETE":
        return unexpected_list
    else:
        return unexpected_list[: result_format["partial_unexpected_count"]]


def _pandas_column_pair_map_condition_filtered_row_count(
    cls,
    execution_engine: PandasExecutionEngine,
    metric_domain_kwargs: Dict,
    metric_value_kwargs: Dict,
    metrics: Dict[(str, Any)],
    **kwargs,
):
    import inspect

    __frame = inspect.currentframe()
    __file = __frame.f_code.co_filename
    __func = __frame.f_code.co_name
    for (k, v) in __frame.f_locals.items():
        if any((var in k) for var in ("__frame", "__file", "__func")):
            continue
        print(f"<INTROSPECT> {__file}:{__func} - {k}:{v.__class__.__name__}")
    "Return record counts from the specified domain that match the map-style metric in the metrics dictionary."
    (_, compute_domain_kwargs, accessor_domain_kwargs) = metrics["unexpected_condition"]
    '\n    In order to invoke the "ignore_row_if" filtering logic, "execution_engine.get_domain_records()" must be supplied\n    with all of the available "domain_kwargs" keys.\n    '
    domain_kwargs = dict(**compute_domain_kwargs, **accessor_domain_kwargs)
    df = execution_engine.get_domain_records(domain_kwargs=domain_kwargs)
    if not (("column_A" in domain_kwargs) and ("column_B" in domain_kwargs)):
        raise ValueError(
            'No "column_A" and "column_B" found in provided metric_domain_kwargs, but it is required for a column pair map metric\n(_pandas_column_pair_map_condition_filtered_row_count).\n'
        )
    column_A_name = accessor_domain_kwargs["column_A"]
    column_B_name = accessor_domain_kwargs["column_B"]
    column_list = [column_A_name, column_B_name]
    for column_name in column_list:
        if column_name not in metrics["table.columns"]:
            raise ge_exceptions.InvalidMetricAccessorDomainKwargsKeyError(
                message=f'Error: The column "{column_name}" in BatchData does not exist.'
            )
    return df.shape[0]


def _pandas_multicolumn_map_condition_values(
    cls,
    execution_engine: PandasExecutionEngine,
    metric_domain_kwargs: Dict,
    metric_value_kwargs: Dict,
    metrics: Dict[(str, Any)],
    **kwargs,
):
    import inspect

    __frame = inspect.currentframe()
    __file = __frame.f_code.co_filename
    __func = __frame.f_code.co_name
    for (k, v) in __frame.f_locals.items():
        if any((var in k) for var in ("__frame", "__file", "__func")):
            continue
        print(f"<INTROSPECT> {__file}:{__func} - {k}:{v.__class__.__name__}")
    "Return values from the specified domain that match the map-style metric in the metrics dictionary."
    (
        boolean_mapped_unexpected_values,
        compute_domain_kwargs,
        accessor_domain_kwargs,
    ) = metrics["unexpected_condition"]
    '\n    In order to invoke the "ignore_row_if" filtering logic, "execution_engine.get_domain_records()" must be supplied\n    with all of the available "domain_kwargs" keys.\n    '
    domain_kwargs = dict(**compute_domain_kwargs, **accessor_domain_kwargs)
    df = execution_engine.get_domain_records(domain_kwargs=domain_kwargs)
    if "column_list" not in accessor_domain_kwargs:
        raise ValueError(
            'No "column_list" found in provided metric_domain_kwargs, but it is required for a multicolumn map metric\n(_pandas_multicolumn_map_condition_values).\n'
        )
    column_list = accessor_domain_kwargs["column_list"]
    for column_name in column_list:
        if column_name not in metrics["table.columns"]:
            raise ge_exceptions.InvalidMetricAccessorDomainKwargsKeyError(
                message=f'Error: The column "{column_name}" in BatchData does not exist.'
            )
    domain_values = df[column_list]
    domain_values = domain_values[(boolean_mapped_unexpected_values == True)]
    result_format = metric_value_kwargs["result_format"]
    if result_format["result_format"] == "COMPLETE":
        return domain_values.to_dict("records")
    else:
        return domain_values[: result_format["partial_unexpected_count"]].to_dict(
            "records"
        )


def _pandas_multicolumn_map_condition_filtered_row_count(
    cls,
    execution_engine: PandasExecutionEngine,
    metric_domain_kwargs: Dict,
    metric_value_kwargs: Dict,
    metrics: Dict[(str, Any)],
    **kwargs,
):
    import inspect

    __frame = inspect.currentframe()
    __file = __frame.f_code.co_filename
    __func = __frame.f_code.co_name
    for (k, v) in __frame.f_locals.items():
        if any((var in k) for var in ("__frame", "__file", "__func")):
            continue
        print(f"<INTROSPECT> {__file}:{__func} - {k}:{v.__class__.__name__}")
    "Return record counts from the specified domain that match the map-style metric in the metrics dictionary."
    (_, compute_domain_kwargs, accessor_domain_kwargs) = metrics["unexpected_condition"]
    '\n    In order to invoke the "ignore_row_if" filtering logic, "execution_engine.get_domain_records()" must be supplied\n    with all of the available "domain_kwargs" keys.\n    '
    domain_kwargs = dict(**compute_domain_kwargs, **accessor_domain_kwargs)
    df = execution_engine.get_domain_records(domain_kwargs=domain_kwargs)
    if "column_list" not in accessor_domain_kwargs:
        raise ValueError(
            'No "column_list" found in provided metric_domain_kwargs, but it is required for a multicolumn map metric\n(_pandas_multicolumn_map_condition_filtered_row_count).\n'
        )
    column_list = accessor_domain_kwargs["column_list"]
    for column_name in column_list:
        if column_name not in metrics["table.columns"]:
            raise ge_exceptions.InvalidMetricAccessorDomainKwargsKeyError(
                message=f'Error: The column "{column_name}" in BatchData does not exist.'
            )
    return df.shape[0]


def _pandas_column_map_series_and_domain_values(
    cls,
    execution_engine: PandasExecutionEngine,
    metric_domain_kwargs: Dict,
    metric_value_kwargs: Dict,
    metrics: Dict[(str, Any)],
    **kwargs,
):
    import inspect

    __frame = inspect.currentframe()
    __file = __frame.f_code.co_filename
    __func = __frame.f_code.co_name
    for (k, v) in __frame.f_locals.items():
        if any((var in k) for var in ("__frame", "__file", "__func")):
            continue
        print(f"<INTROSPECT> {__file}:{__func} - {k}:{v.__class__.__name__}")
    "Return values from the specified domain that match the map-style metric in the metrics dictionary."
    (
        boolean_mapped_unexpected_values,
        compute_domain_kwargs,
        accessor_domain_kwargs,
    ) = metrics["unexpected_condition"]
    (map_series, compute_domain_kwargs_2, accessor_domain_kwargs_2) = metrics[
        "metric_partial_fn"
    ]
    assert (
        compute_domain_kwargs == compute_domain_kwargs_2
    ), "map_series and condition must have the same compute domain"
    assert (
        accessor_domain_kwargs == accessor_domain_kwargs_2
    ), "map_series and condition must have the same accessor kwargs"
    df = execution_engine.get_domain_records(domain_kwargs=compute_domain_kwargs)
    filter_column_isnull = kwargs.get(
        "filter_column_isnull", getattr(cls, "filter_column_isnull", False)
    )
    if "column" not in accessor_domain_kwargs:
        raise ValueError(
            'No "column" found in provided metric_domain_kwargs, but it is required for a column map metric\n(_pandas_column_map_series_and_domain_values).\n'
        )
    column_name = accessor_domain_kwargs["column"]
    if column_name not in metrics["table.columns"]:
        raise ge_exceptions.InvalidMetricAccessorDomainKwargsKeyError(
            message=f'Error: The column "{column_name}" in BatchData does not exist.'
        )
    if filter_column_isnull:
        df = df[df[column_name].notnull()]
    domain_values = df[column_name]
    domain_values = domain_values[(boolean_mapped_unexpected_values == True)]
    map_series = map_series[(boolean_mapped_unexpected_values == True)]
    result_format = metric_value_kwargs["result_format"]
    if result_format["result_format"] == "COMPLETE":
        return (list(domain_values), list(map_series))
    else:
        return (
            list(domain_values[: result_format["partial_unexpected_count"]]),
            list(map_series[: result_format["partial_unexpected_count"]]),
        )


def _pandas_map_condition_index(
    cls,
    execution_engine: PandasExecutionEngine,
    metric_domain_kwargs: Dict,
    metric_value_kwargs: Dict,
    metrics: Dict[(str, Any)],
    **kwargs,
):
    import inspect

    __frame = inspect.currentframe()
    __file = __frame.f_code.co_filename
    __func = __frame.f_code.co_name
    for (k, v) in __frame.f_locals.items():
        if any((var in k) for var in ("__frame", "__file", "__func")):
            continue
        print(f"<INTROSPECT> {__file}:{__func} - {k}:{v.__class__.__name__}")
    (
        boolean_mapped_unexpected_values,
        compute_domain_kwargs,
        accessor_domain_kwargs,
    ) = metrics.get("unexpected_condition")
    '\n    In order to invoke the "ignore_row_if" filtering logic, "execution_engine.get_domain_records()" must be supplied\n    with all of the available "domain_kwargs" keys.\n    '
    domain_kwargs = dict(**compute_domain_kwargs, **accessor_domain_kwargs)
    df = execution_engine.get_domain_records(domain_kwargs=domain_kwargs)
    filter_column_isnull = kwargs.get(
        "filter_column_isnull", getattr(cls, "filter_column_isnull", False)
    )
    if "column" in accessor_domain_kwargs:
        column_name = accessor_domain_kwargs["column"]
        if column_name not in metrics["table.columns"]:
            raise ge_exceptions.InvalidMetricAccessorDomainKwargsKeyError(
                message=f'Error: The column "{column_name}" in BatchData does not exist.'
            )
        if filter_column_isnull:
            df = df[df[column_name].notnull()]
    elif "column_list" in accessor_domain_kwargs:
        column_list = accessor_domain_kwargs["column_list"]
        for column_name in column_list:
            if column_name not in metrics["table.columns"]:
                raise ge_exceptions.InvalidMetricAccessorDomainKwargsKeyError(
                    message=f'Error: The column "{column_name}" in BatchData does not exist.'
                )
    result_format = metric_value_kwargs["result_format"]
    df = df[boolean_mapped_unexpected_values]
    if result_format["result_format"] == "COMPLETE":
        return list(df.index)
    return list(df.index[: result_format["partial_unexpected_count"]])


def _pandas_column_map_condition_value_counts(
    cls,
    execution_engine: PandasExecutionEngine,
    metric_domain_kwargs: Dict,
    metric_value_kwargs: Dict,
    metrics: Dict[(str, Any)],
    **kwargs,
):
    import inspect

    __frame = inspect.currentframe()
    __file = __frame.f_code.co_filename
    __func = __frame.f_code.co_name
    for (k, v) in __frame.f_locals.items():
        if any((var in k) for var in ("__frame", "__file", "__func")):
            continue
        print(f"<INTROSPECT> {__file}:{__func} - {k}:{v.__class__.__name__}")
    "Returns respective value counts for distinct column values"
    (
        boolean_mapped_unexpected_values,
        compute_domain_kwargs,
        accessor_domain_kwargs,
    ) = metrics.get("unexpected_condition")
    df = execution_engine.get_domain_records(domain_kwargs=compute_domain_kwargs)
    filter_column_isnull = kwargs.get(
        "filter_column_isnull", getattr(cls, "filter_column_isnull", False)
    )
    column_name = accessor_domain_kwargs["column"]
    if "column" not in accessor_domain_kwargs:
        raise ValueError(
            'No "column" found in provided metric_domain_kwargs, but it is required for a column map metric\n(_pandas_column_map_condition_value_counts).\n'
        )
    if column_name not in metrics["table.columns"]:
        raise ge_exceptions.InvalidMetricAccessorDomainKwargsKeyError(
            message=f'Error: The column "{column_name}" in BatchData does not exist.'
        )
    if filter_column_isnull:
        df = df[df[column_name].notnull()]
    domain_values = df[column_name]
    result_format = metric_value_kwargs["result_format"]
    value_counts = None
    try:
        value_counts = domain_values[boolean_mapped_unexpected_values].value_counts()
    except ValueError:
        try:
            value_counts = (
                domain_values[boolean_mapped_unexpected_values]
                .apply(tuple)
                .value_counts()
            )
        except ValueError:
            pass
    if not value_counts:
        raise ge_exceptions.MetricComputationError("Unable to compute value counts")
    if result_format["result_format"] == "COMPLETE":
        return value_counts
    else:
        return value_counts[result_format["partial_unexpected_count"]]


def _pandas_map_condition_rows(
    cls,
    execution_engine: PandasExecutionEngine,
    metric_domain_kwargs: Dict,
    metric_value_kwargs: Dict,
    metrics: Dict[(str, Any)],
    **kwargs,
):
    import inspect

    __frame = inspect.currentframe()
    __file = __frame.f_code.co_filename
    __func = __frame.f_code.co_name
    for (k, v) in __frame.f_locals.items():
        if any((var in k) for var in ("__frame", "__file", "__func")):
            continue
        print(f"<INTROSPECT> {__file}:{__func} - {k}:{v.__class__.__name__}")
    "Return values from the specified domain (ignoring the column constraint) that match the map-style metric in the metrics dictionary."
    (
        boolean_mapped_unexpected_values,
        compute_domain_kwargs,
        accessor_domain_kwargs,
    ) = metrics.get("unexpected_condition")
    '\n    In order to invoke the "ignore_row_if" filtering logic, "execution_engine.get_domain_records()" must be supplied\n    with all of the available "domain_kwargs" keys.\n    '
    domain_kwargs = dict(**compute_domain_kwargs, **accessor_domain_kwargs)
    df = execution_engine.get_domain_records(domain_kwargs=domain_kwargs)
    filter_column_isnull = kwargs.get(
        "filter_column_isnull", getattr(cls, "filter_column_isnull", False)
    )
    if "column" in accessor_domain_kwargs:
        column_name = accessor_domain_kwargs["column"]
        if column_name not in metrics["table.columns"]:
            raise ge_exceptions.InvalidMetricAccessorDomainKwargsKeyError(
                message=f'Error: The column "{column_name}" in BatchData does not exist.'
            )
        if filter_column_isnull:
            df = df[df[column_name].notnull()]
    elif "column_list" in accessor_domain_kwargs:
        column_list = accessor_domain_kwargs["column_list"]
        for column_name in column_list:
            if column_name not in metrics["table.columns"]:
                raise ge_exceptions.InvalidMetricAccessorDomainKwargsKeyError(
                    message=f'Error: The column "{column_name}" in BatchData does not exist.'
                )
    result_format = metric_value_kwargs["result_format"]
    df = df[boolean_mapped_unexpected_values]
    if result_format["result_format"] == "COMPLETE":
        return df
    return df.iloc[: result_format["partial_unexpected_count"]]


def _sqlalchemy_map_condition_unexpected_count_aggregate_fn(
    cls,
    execution_engine: SqlAlchemyExecutionEngine,
    metric_domain_kwargs: Dict,
    metric_value_kwargs: Dict,
    metrics: Dict[(str, Any)],
    **kwargs,
):
    import inspect

    __frame = inspect.currentframe()
    __file = __frame.f_code.co_filename
    __func = __frame.f_code.co_name
    for (k, v) in __frame.f_locals.items():
        if any((var in k) for var in ("__frame", "__file", "__func")):
            continue
        print(f"<INTROSPECT> {__file}:{__func} - {k}:{v.__class__.__name__}")
    "Returns unexpected count for MapExpectations"
    (unexpected_condition, compute_domain_kwargs, accessor_domain_kwargs) = metrics.get(
        "unexpected_condition"
    )
    return (
        sa.func.sum(sa.case([(unexpected_condition, 1)], else_=0)),
        compute_domain_kwargs,
        accessor_domain_kwargs,
    )


def _sqlalchemy_map_condition_unexpected_count_value(
    cls,
    execution_engine: SqlAlchemyExecutionEngine,
    metric_domain_kwargs: Dict,
    metric_value_kwargs: Dict,
    metrics: Dict[(str, Any)],
    **kwargs,
):
    import inspect

    __frame = inspect.currentframe()
    __file = __frame.f_code.co_filename
    __func = __frame.f_code.co_name
    for (k, v) in __frame.f_locals.items():
        if any((var in k) for var in ("__frame", "__file", "__func")):
            continue
        print(f"<INTROSPECT> {__file}:{__func} - {k}:{v.__class__.__name__}")
    "Returns unexpected count for MapExpectations. This is a *value* metric, which is useful for\n    when the unexpected_condition is a window function.\n    "
    (unexpected_condition, compute_domain_kwargs, accessor_domain_kwargs) = metrics.get(
        "unexpected_condition"
    )
    '\n    In order to invoke the "ignore_row_if" filtering logic, "execution_engine.get_domain_records()" must be supplied\n    with all of the available "domain_kwargs" keys.\n    '
    domain_kwargs = dict(**compute_domain_kwargs, **accessor_domain_kwargs)
    selectable = execution_engine.get_domain_records(domain_kwargs=domain_kwargs)
    count_case_statement: List[Label] = sa.case(
        [(unexpected_condition, sa.sql.expression.cast(1, sa.Numeric))],
        else_=sa.sql.expression.cast(0, sa.Numeric),
    ).label("condition")
    count_selectable: Select = sa.select([count_case_statement])
    if not MapMetricProvider.is_sqlalchemy_metric_selectable(map_metric_provider=cls):
        selectable = get_sqlalchemy_selectable(selectable)
        count_selectable = count_selectable.select_from(selectable)
    try:
        if execution_engine.engine.dialect.name.lower() == "mssql":
            temp_table_name: str = generate_temporary_table_name(
                default_table_name_prefix="#ge_temp_"
            )
            with execution_engine.engine.begin():
                metadata: sa.MetaData = sa.MetaData(execution_engine.engine)
                temp_table_obj: sa.Table = sa.Table(
                    temp_table_name,
                    metadata,
                    sa.Column(
                        "condition", sa.Integer, primary_key=False, nullable=False
                    ),
                )
                temp_table_obj.create(execution_engine.engine, checkfirst=True)
                inner_case_query: Insert = temp_table_obj.insert().from_select(
                    [count_case_statement], count_selectable
                )
                execution_engine.engine.execute(inner_case_query)
                count_selectable = temp_table_obj
        count_selectable = get_sqlalchemy_selectable(count_selectable)
        unexpected_count_query: Select = (
            sa.select([sa.func.sum(sa.column("condition")).label("unexpected_count")])
            .select_from(count_selectable)
            .alias("UnexpectedCountSubquery")
        )
        unexpected_count: Union[(float, int)] = execution_engine.engine.execute(
            sa.select([unexpected_count_query.c.unexpected_count])
        ).scalar()
        try:
            unexpected_count = int(unexpected_count)
        except TypeError:
            unexpected_count = 0
    except OperationalError as oe:
        exception_message: str = f"An SQL execution Exception occurred: {str(oe)}."
        raise ge_exceptions.InvalidMetricAccessorDomainKwargsKeyError(
            message=exception_message
        )
    return convert_to_json_serializable(unexpected_count)


def _sqlalchemy_column_map_condition_values(
    cls,
    execution_engine: SqlAlchemyExecutionEngine,
    metric_domain_kwargs: Dict,
    metric_value_kwargs: Dict,
    metrics: Dict[(str, Any)],
    **kwargs,
):
    import inspect

    __frame = inspect.currentframe()
    __file = __frame.f_code.co_filename
    __func = __frame.f_code.co_name
    for (k, v) in __frame.f_locals.items():
        if any((var in k) for var in ("__frame", "__file", "__func")):
            continue
        print(f"<INTROSPECT> {__file}:{__func} - {k}:{v.__class__.__name__}")
    "\n    Particularly for the purpose of finding unexpected values, returns all the metric values which do not meet an\n    expected Expectation condition for ColumnMapExpectation Expectations.\n    "
    (unexpected_condition, compute_domain_kwargs, accessor_domain_kwargs) = metrics.get(
        "unexpected_condition"
    )
    selectable = execution_engine.get_domain_records(
        domain_kwargs=compute_domain_kwargs
    )
    if "column" not in accessor_domain_kwargs:
        raise ValueError(
            'No "column" found in provided metric_domain_kwargs, but it is required for a column map metric\n(_sqlalchemy_column_map_condition_values).\n'
        )
    column_name = accessor_domain_kwargs["column"]
    if column_name not in metrics["table.columns"]:
        raise ge_exceptions.InvalidMetricAccessorDomainKwargsKeyError(
            message=f'Error: The column "{column_name}" in BatchData does not exist.'
        )
    query = sa.select([sa.column(column_name).label("unexpected_values")]).where(
        unexpected_condition
    )
    if not MapMetricProvider.is_sqlalchemy_metric_selectable(map_metric_provider=cls):
        query = query.select_from(selectable)
    result_format = metric_value_kwargs["result_format"]
    if result_format["result_format"] != "COMPLETE":
        query = query.limit(result_format["partial_unexpected_count"])
    elif (result_format["result_format"] == "COMPLETE") and (
        execution_engine.engine.dialect.name.lower() == "bigquery"
    ):
        logger.warning(
            "BigQuery imposes a limit of 10000 parameters on individual queries; if your data contains more than 10000 columns your results will be truncated."
        )
        query = query.limit(10000)
    return [
        val.unexpected_values
        for val in execution_engine.engine.execute(query).fetchall()
    ]


def _sqlalchemy_column_pair_map_condition_values(
    cls,
    execution_engine: SqlAlchemyExecutionEngine,
    metric_domain_kwargs: Dict,
    metric_value_kwargs: Dict,
    metrics: Dict[(str, Any)],
    **kwargs,
):
    import inspect

    __frame = inspect.currentframe()
    __file = __frame.f_code.co_filename
    __func = __frame.f_code.co_name
    for (k, v) in __frame.f_locals.items():
        if any((var in k) for var in ("__frame", "__file", "__func")):
            continue
        print(f"<INTROSPECT> {__file}:{__func} - {k}:{v.__class__.__name__}")
    "Return values from the specified domain that match the map-style metric in the metrics dictionary."
    (
        boolean_mapped_unexpected_values,
        compute_domain_kwargs,
        accessor_domain_kwargs,
    ) = metrics["unexpected_condition"]
    '\n    In order to invoke the "ignore_row_if" filtering logic, "execution_engine.get_domain_records()" must be supplied\n    with all of the available "domain_kwargs" keys.\n    '
    domain_kwargs = dict(**compute_domain_kwargs, **accessor_domain_kwargs)
    selectable = execution_engine.get_domain_records(domain_kwargs=domain_kwargs)
    column_A_name = accessor_domain_kwargs["column_A"]
    column_B_name = accessor_domain_kwargs["column_B"]
    column_list = [column_A_name, column_B_name]
    for column_name in column_list:
        if column_name not in metrics["table.columns"]:
            raise ge_exceptions.InvalidMetricAccessorDomainKwargsKeyError(
                message=f'Error: The column "{column_name}" in BatchData does not exist.'
            )
    query = sa.select(
        [
            sa.column(column_A_name).label("unexpected_values_A"),
            sa.column(column_B_name).label("unexpected_values_B"),
        ]
    ).where(boolean_mapped_unexpected_values)
    if not MapMetricProvider.is_sqlalchemy_metric_selectable(map_metric_provider=cls):
        selectable = get_sqlalchemy_selectable(selectable)
        query = query.select_from(selectable)
    result_format = metric_value_kwargs["result_format"]
    if result_format["result_format"] != "COMPLETE":
        query = query.limit(result_format["partial_unexpected_count"])
    unexpected_list = [
        (val.unexpected_values_A, val.unexpected_values_B)
        for val in execution_engine.engine.execute(query).fetchall()
    ]
    return unexpected_list


def _sqlalchemy_column_pair_map_condition_filtered_row_count(
    cls,
    execution_engine: SqlAlchemyExecutionEngine,
    metric_domain_kwargs: Dict,
    metric_value_kwargs: Dict,
    metrics: Dict[(str, Any)],
    **kwargs,
):
    import inspect

    __frame = inspect.currentframe()
    __file = __frame.f_code.co_filename
    __func = __frame.f_code.co_name
    for (k, v) in __frame.f_locals.items():
        if any((var in k) for var in ("__frame", "__file", "__func")):
            continue
        print(f"<INTROSPECT> {__file}:{__func} - {k}:{v.__class__.__name__}")
    "Return record counts from the specified domain that match the map-style metric in the metrics dictionary."
    (_, compute_domain_kwargs, accessor_domain_kwargs) = metrics["unexpected_condition"]
    '\n    In order to invoke the "ignore_row_if" filtering logic, "execution_engine.get_domain_records()" must be supplied\n    with all of the available "domain_kwargs" keys.\n    '
    domain_kwargs = dict(**compute_domain_kwargs, **accessor_domain_kwargs)
    selectable = execution_engine.get_domain_records(domain_kwargs=domain_kwargs)
    column_A_name = accessor_domain_kwargs["column_A"]
    column_B_name = accessor_domain_kwargs["column_B"]
    column_list = [column_A_name, column_B_name]
    for column_name in column_list:
        if column_name not in metrics["table.columns"]:
            raise ge_exceptions.InvalidMetricAccessorDomainKwargsKeyError(
                message=f'Error: The column "{column_name}" in BatchData does not exist.'
            )
    return execution_engine.engine.execute(
        sa.select([sa.func.count()]).select_from(selectable)
    ).scalar()


def _sqlalchemy_multicolumn_map_condition_values(
    cls,
    execution_engine: SqlAlchemyExecutionEngine,
    metric_domain_kwargs: Dict,
    metric_value_kwargs: Dict,
    metrics: Dict[(str, Any)],
    **kwargs,
):
    import inspect

    __frame = inspect.currentframe()
    __file = __frame.f_code.co_filename
    __func = __frame.f_code.co_name
    for (k, v) in __frame.f_locals.items():
        if any((var in k) for var in ("__frame", "__file", "__func")):
            continue
        print(f"<INTROSPECT> {__file}:{__func} - {k}:{v.__class__.__name__}")
    "Return values from the specified domain that match the map-style metric in the metrics dictionary."
    (
        boolean_mapped_unexpected_values,
        compute_domain_kwargs,
        accessor_domain_kwargs,
    ) = metrics["unexpected_condition"]
    '\n    In order to invoke the "ignore_row_if" filtering logic, "execution_engine.get_domain_records()" must be supplied\n    with all of the available "domain_kwargs" keys.\n    '
    domain_kwargs = dict(**compute_domain_kwargs, **accessor_domain_kwargs)
    selectable = execution_engine.get_domain_records(domain_kwargs=domain_kwargs)
    if "column_list" not in accessor_domain_kwargs:
        raise ValueError(
            'No "column_list" found in provided metric_domain_kwargs, but it is required for a multicolumn map metric\n(_sqlalchemy_multicolumn_map_condition_values).\n'
        )
    column_list = accessor_domain_kwargs["column_list"]
    for column_name in column_list:
        if column_name not in metrics["table.columns"]:
            raise ge_exceptions.InvalidMetricAccessorDomainKwargsKeyError(
                message=f'Error: The column "{column_name}" in BatchData does not exist.'
            )
    column_selector = [sa.column(column_name) for column_name in column_list]
    query = sa.select(column_selector).where(boolean_mapped_unexpected_values)
    if not MapMetricProvider.is_sqlalchemy_metric_selectable(map_metric_provider=cls):
        selectable = get_sqlalchemy_selectable(selectable)
        query = query.select_from(selectable)
    result_format = metric_value_kwargs["result_format"]
    if result_format["result_format"] != "COMPLETE":
        query = query.limit(result_format["partial_unexpected_count"])
    return [dict(val) for val in execution_engine.engine.execute(query).fetchall()]


def _sqlalchemy_multicolumn_map_condition_filtered_row_count(
    cls,
    execution_engine: SqlAlchemyExecutionEngine,
    metric_domain_kwargs: Dict,
    metric_value_kwargs: Dict,
    metrics: Dict[(str, Any)],
    **kwargs,
):
    import inspect

    __frame = inspect.currentframe()
    __file = __frame.f_code.co_filename
    __func = __frame.f_code.co_name
    for (k, v) in __frame.f_locals.items():
        if any((var in k) for var in ("__frame", "__file", "__func")):
            continue
        print(f"<INTROSPECT> {__file}:{__func} - {k}:{v.__class__.__name__}")
    "Return record counts from the specified domain that match the map-style metric in the metrics dictionary."
    (_, compute_domain_kwargs, accessor_domain_kwargs) = metrics["unexpected_condition"]
    '\n    In order to invoke the "ignore_row_if" filtering logic, "execution_engine.get_domain_records()" must be supplied\n    with all of the available "domain_kwargs" keys.\n    '
    domain_kwargs = dict(**compute_domain_kwargs, **accessor_domain_kwargs)
    selectable = execution_engine.get_domain_records(domain_kwargs=domain_kwargs)
    if "column_list" not in accessor_domain_kwargs:
        raise ValueError(
            'No "column_list" found in provided metric_domain_kwargs, but it is required for a multicolumn map metric\n(_sqlalchemy_multicolumn_map_condition_filtered_row_count).\n'
        )
    column_list = accessor_domain_kwargs["column_list"]
    for column_name in column_list:
        if column_name not in metrics["table.columns"]:
            raise ge_exceptions.InvalidMetricAccessorDomainKwargsKeyError(
                message=f'Error: The column "{column_name}" in BatchData does not exist.'
            )
    selectable = get_sqlalchemy_selectable(selectable)
    return execution_engine.engine.execute(
        sa.select([sa.func.count()]).select_from(selectable)
    ).scalar()


def _sqlalchemy_column_map_condition_value_counts(
    cls,
    execution_engine: SqlAlchemyExecutionEngine,
    metric_domain_kwargs: Dict,
    metric_value_kwargs: Dict,
    metrics: Dict[(str, Any)],
    **kwargs,
):
    import inspect

    __frame = inspect.currentframe()
    __file = __frame.f_code.co_filename
    __func = __frame.f_code.co_name
    for (k, v) in __frame.f_locals.items():
        if any((var in k) for var in ("__frame", "__file", "__func")):
            continue
        print(f"<INTROSPECT> {__file}:{__func} - {k}:{v.__class__.__name__}")
    "\n    Returns value counts for all the metric values which do not meet an expected Expectation condition for instances\n    of ColumnMapExpectation.\n    "
    (unexpected_condition, compute_domain_kwargs, accessor_domain_kwargs) = metrics.get(
        "unexpected_condition"
    )
    selectable = execution_engine.get_domain_records(
        domain_kwargs=compute_domain_kwargs
    )
    if "column" not in accessor_domain_kwargs:
        raise ValueError(
            'No "column" found in provided metric_domain_kwargs, but it is required for a column map metric\n(_sqlalchemy_column_map_condition_value_counts).\n'
        )
    column_name = accessor_domain_kwargs["column"]
    if column_name not in metrics["table.columns"]:
        raise ge_exceptions.InvalidMetricAccessorDomainKwargsKeyError(
            message=f'Error: The column "{column_name}" in BatchData does not exist.'
        )
    column: sa.Column = sa.column(column_name)
    query = (
        sa.select([column, sa.func.count(column)])
        .where(unexpected_condition)
        .group_by(column)
    )
    if not MapMetricProvider.is_sqlalchemy_metric_selectable(map_metric_provider=cls):
        query = query.select_from(selectable)
    return execution_engine.engine.execute(query).fetchall()


def _sqlalchemy_map_condition_rows(
    cls,
    execution_engine: SqlAlchemyExecutionEngine,
    metric_domain_kwargs: Dict,
    metric_value_kwargs: Dict,
    metrics: Dict[(str, Any)],
    **kwargs,
):
    import inspect

    __frame = inspect.currentframe()
    __file = __frame.f_code.co_filename
    __func = __frame.f_code.co_name
    for (k, v) in __frame.f_locals.items():
        if any((var in k) for var in ("__frame", "__file", "__func")):
            continue
        print(f"<INTROSPECT> {__file}:{__func} - {k}:{v.__class__.__name__}")
    "\n    Returns all rows of the metric values which do not meet an expected Expectation condition for instances\n    of ColumnMapExpectation.\n    "
    (unexpected_condition, compute_domain_kwargs, accessor_domain_kwargs) = metrics.get(
        "unexpected_condition"
    )
    '\n    In order to invoke the "ignore_row_if" filtering logic, "execution_engine.get_domain_records()" must be supplied\n    with all of the available "domain_kwargs" keys.\n    '
    domain_kwargs = dict(**compute_domain_kwargs, **accessor_domain_kwargs)
    selectable = execution_engine.get_domain_records(domain_kwargs=domain_kwargs)
    table_columns = metrics.get("table.columns")
    column_selector = [sa.column(column_name) for column_name in table_columns]
    query = sa.select(column_selector).where(unexpected_condition)
    if not MapMetricProvider.is_sqlalchemy_metric_selectable(map_metric_provider=cls):
        selectable = get_sqlalchemy_selectable(selectable)
        query = query.select_from(selectable)
    result_format = metric_value_kwargs["result_format"]
    if result_format["result_format"] != "COMPLETE":
        query = query.limit(result_format["partial_unexpected_count"])
    try:
        return execution_engine.engine.execute(query).fetchall()
    except OperationalError as oe:
        exception_message: str = f"An SQL execution Exception occurred: {str(oe)}."
        raise ge_exceptions.InvalidMetricAccessorDomainKwargsKeyError(
            message=exception_message
        )


def _spark_map_condition_unexpected_count_aggregate_fn(
    cls,
    execution_engine: SparkDFExecutionEngine,
    metric_domain_kwargs: Dict,
    metric_value_kwargs: Dict,
    metrics: Dict[(str, Any)],
    **kwargs,
):
    import inspect

    __frame = inspect.currentframe()
    __file = __frame.f_code.co_filename
    __func = __frame.f_code.co_name
    for (k, v) in __frame.f_locals.items():
        if any((var in k) for var in ("__frame", "__file", "__func")):
            continue
        print(f"<INTROSPECT> {__file}:{__func} - {k}:{v.__class__.__name__}")
    (unexpected_condition, compute_domain_kwargs, accessor_domain_kwargs) = metrics.get(
        "unexpected_condition"
    )
    return (
        F.sum(F.when(unexpected_condition, 1).otherwise(0)),
        compute_domain_kwargs,
        accessor_domain_kwargs,
    )


def _spark_map_condition_unexpected_count_value(
    cls,
    execution_engine: SparkDFExecutionEngine,
    metric_domain_kwargs: Dict,
    metric_value_kwargs: Dict,
    metrics: Dict[(str, Any)],
    **kwargs,
):
    import inspect

    __frame = inspect.currentframe()
    __file = __frame.f_code.co_filename
    __func = __frame.f_code.co_name
    for (k, v) in __frame.f_locals.items():
        if any((var in k) for var in ("__frame", "__file", "__func")):
            continue
        print(f"<INTROSPECT> {__file}:{__func} - {k}:{v.__class__.__name__}")
    (unexpected_condition, compute_domain_kwargs, accessor_domain_kwargs) = metrics.get(
        "unexpected_condition"
    )
    '\n    In order to invoke the "ignore_row_if" filtering logic, "execution_engine.get_domain_records()" must be supplied\n    with all of the available "domain_kwargs" keys.\n    '
    domain_kwargs = dict(**compute_domain_kwargs, **accessor_domain_kwargs)
    df = execution_engine.get_domain_records(domain_kwargs=domain_kwargs)
    data = df.withColumn("__unexpected", unexpected_condition)
    filtered = data.filter(F.col("__unexpected") == True).drop(F.col("__unexpected"))
    return filtered.count()


def _spark_column_map_condition_values(
    cls,
    execution_engine: SparkDFExecutionEngine,
    metric_domain_kwargs: Dict,
    metric_value_kwargs: Dict,
    metrics: Dict[(str, Any)],
    **kwargs,
):
    import inspect

    __frame = inspect.currentframe()
    __file = __frame.f_code.co_filename
    __func = __frame.f_code.co_name
    for (k, v) in __frame.f_locals.items():
        if any((var in k) for var in ("__frame", "__file", "__func")):
            continue
        print(f"<INTROSPECT> {__file}:{__func} - {k}:{v.__class__.__name__}")
    "Return values from the specified domain that match the map-style metric in the metrics dictionary."
    (unexpected_condition, compute_domain_kwargs, accessor_domain_kwargs) = metrics.get(
        "unexpected_condition"
    )
    df = execution_engine.get_domain_records(domain_kwargs=compute_domain_kwargs)
    if "column" not in accessor_domain_kwargs:
        raise ValueError(
            'No "column" found in provided metric_domain_kwargs, but it is required for a column map metric\n(_spark_column_map_condition_values).\n'
        )
    column_name = accessor_domain_kwargs["column"]
    if column_name not in metrics["table.columns"]:
        raise ge_exceptions.InvalidMetricAccessorDomainKwargsKeyError(
            message=f'Error: The column "{column_name}" in BatchData does not exist.'
        )
    data = df.withColumn("__unexpected", unexpected_condition)
    filtered = data.filter(F.col("__unexpected") == True).drop(F.col("__unexpected"))
    result_format = metric_value_kwargs["result_format"]
    if result_format["result_format"] == "COMPLETE":
        rows = filtered.select(F.col(column_name).alias(column_name)).collect()
    else:
        rows = (
            filtered.select(F.col(column_name).alias(column_name))
            .limit(result_format["partial_unexpected_count"])
            .collect()
        )
    return [row[column_name] for row in rows]


def _spark_column_map_condition_value_counts(
    cls,
    execution_engine: SparkDFExecutionEngine,
    metric_domain_kwargs: Dict,
    metric_value_kwargs: Dict,
    metrics: Dict[(str, Any)],
    **kwargs,
):
    import inspect

    __frame = inspect.currentframe()
    __file = __frame.f_code.co_filename
    __func = __frame.f_code.co_name
    for (k, v) in __frame.f_locals.items():
        if any((var in k) for var in ("__frame", "__file", "__func")):
            continue
        print(f"<INTROSPECT> {__file}:{__func} - {k}:{v.__class__.__name__}")
    (unexpected_condition, compute_domain_kwargs, accessor_domain_kwargs) = metrics.get(
        "unexpected_condition"
    )
    df = execution_engine.get_domain_records(domain_kwargs=compute_domain_kwargs)
    if "column" not in accessor_domain_kwargs:
        raise ValueError(
            'No "column" found in provided metric_domain_kwargs, but it is required for a column map metric\n(_spark_column_map_condition_value_counts).\n'
        )
    column_name = accessor_domain_kwargs["column"]
    if column_name not in metrics["table.columns"]:
        raise ge_exceptions.InvalidMetricAccessorDomainKwargsKeyError(
            message=f'Error: The column "{column_name}" in BatchData does not exist.'
        )
    data = df.withColumn("__unexpected", unexpected_condition)
    filtered = data.filter(F.col("__unexpected") == True).drop(F.col("__unexpected"))
    result_format = metric_value_kwargs["result_format"]
    value_counts = filtered.groupBy(F.col(column_name).alias(column_name)).count()
    if result_format["result_format"] == "COMPLETE":
        rows = value_counts.collect()
    else:
        rows = value_counts.collect()[: result_format["partial_unexpected_count"]]
    return rows


def _spark_map_condition_rows(
    cls,
    execution_engine: SparkDFExecutionEngine,
    metric_domain_kwargs: Dict,
    metric_value_kwargs: Dict,
    metrics: Dict[(str, Any)],
    **kwargs,
):
    import inspect

    __frame = inspect.currentframe()
    __file = __frame.f_code.co_filename
    __func = __frame.f_code.co_name
    for (k, v) in __frame.f_locals.items():
        if any((var in k) for var in ("__frame", "__file", "__func")):
            continue
        print(f"<INTROSPECT> {__file}:{__func} - {k}:{v.__class__.__name__}")
    (unexpected_condition, compute_domain_kwargs, accessor_domain_kwargs) = metrics.get(
        "unexpected_condition"
    )
    '\n    In order to invoke the "ignore_row_if" filtering logic, "execution_engine.get_domain_records()" must be supplied\n    with all of the available "domain_kwargs" keys.\n    '
    domain_kwargs = dict(**compute_domain_kwargs, **accessor_domain_kwargs)
    df = execution_engine.get_domain_records(domain_kwargs=domain_kwargs)
    data = df.withColumn("__unexpected", unexpected_condition)
    filtered = data.filter(F.col("__unexpected") == True).drop(F.col("__unexpected"))
    result_format = metric_value_kwargs["result_format"]
    if result_format["result_format"] == "COMPLETE":
        return filtered.collect()
    else:
        return filtered.limit(result_format["partial_unexpected_count"]).collect()


def _spark_column_pair_map_condition_values(
    cls,
    execution_engine: SparkDFExecutionEngine,
    metric_domain_kwargs: Dict,
    metric_value_kwargs: Dict,
    metrics: Dict[(str, Any)],
    **kwargs,
):
    import inspect

    __frame = inspect.currentframe()
    __file = __frame.f_code.co_filename
    __func = __frame.f_code.co_name
    for (k, v) in __frame.f_locals.items():
        if any((var in k) for var in ("__frame", "__file", "__func")):
            continue
        print(f"<INTROSPECT> {__file}:{__func} - {k}:{v.__class__.__name__}")
    "Return values from the specified domain that match the map-style metric in the metrics dictionary."
    (unexpected_condition, compute_domain_kwargs, accessor_domain_kwargs) = metrics[
        "unexpected_condition"
    ]
    '\n    In order to invoke the "ignore_row_if" filtering logic, "execution_engine.get_domain_records()" must be supplied\n    with all of the available "domain_kwargs" keys.\n    '
    domain_kwargs = dict(**compute_domain_kwargs, **accessor_domain_kwargs)
    df = execution_engine.get_domain_records(domain_kwargs=domain_kwargs)
    column_A_name = accessor_domain_kwargs["column_A"]
    column_B_name = accessor_domain_kwargs["column_B"]
    column_list = [column_A_name, column_B_name]
    for column_name in column_list:
        if column_name not in metrics["table.columns"]:
            raise ge_exceptions.InvalidMetricAccessorDomainKwargsKeyError(
                message=f'Error: The column "{column_name}" in BatchData does not exist.'
            )
    data = df.withColumn("__unexpected", unexpected_condition)
    filtered = data.filter(F.col("__unexpected") == True).drop(F.col("__unexpected"))
    result_format = metric_value_kwargs["result_format"]
    if result_format["result_format"] == "COMPLETE":
        rows = filtered.select(
            [
                F.col(column_A_name).alias(column_A_name),
                F.col(column_B_name).alias(column_B_name),
            ]
        ).collect()
    else:
        rows = (
            filtered.select(
                [
                    F.col(column_A_name).alias(column_A_name),
                    F.col(column_B_name).alias(column_B_name),
                ]
            )
            .limit(result_format["partial_unexpected_count"])
            .collect()
        )
    unexpected_list = [(row[column_A_name], row[column_B_name]) for row in rows]
    return unexpected_list


def _spark_column_pair_map_condition_filtered_row_count(
    cls,
    execution_engine: SparkDFExecutionEngine,
    metric_domain_kwargs: Dict,
    metric_value_kwargs: Dict,
    metrics: Dict[(str, Any)],
    **kwargs,
):
    import inspect

    __frame = inspect.currentframe()
    __file = __frame.f_code.co_filename
    __func = __frame.f_code.co_name
    for (k, v) in __frame.f_locals.items():
        if any((var in k) for var in ("__frame", "__file", "__func")):
            continue
        print(f"<INTROSPECT> {__file}:{__func} - {k}:{v.__class__.__name__}")
    "Return record counts from the specified domain that match the map-style metric in the metrics dictionary."
    (_, compute_domain_kwargs, accessor_domain_kwargs) = metrics["unexpected_condition"]
    '\n    In order to invoke the "ignore_row_if" filtering logic, "execution_engine.get_domain_records()" must be supplied\n    with all of the available "domain_kwargs" keys.\n    '
    domain_kwargs = dict(**compute_domain_kwargs, **accessor_domain_kwargs)
    df = execution_engine.get_domain_records(domain_kwargs=domain_kwargs)
    column_A_name = accessor_domain_kwargs["column_A"]
    column_B_name = accessor_domain_kwargs["column_B"]
    column_list = [column_A_name, column_B_name]
    for column_name in column_list:
        if column_name not in metrics["table.columns"]:
            raise ge_exceptions.InvalidMetricAccessorDomainKwargsKeyError(
                message=f'Error: The column "{column_name}" in BatchData does not exist.'
            )
    return df.count()


def _spark_multicolumn_map_condition_values(
    cls,
    execution_engine: SqlAlchemyExecutionEngine,
    metric_domain_kwargs: Dict,
    metric_value_kwargs: Dict,
    metrics: Dict[(str, Any)],
    **kwargs,
):
    import inspect

    __frame = inspect.currentframe()
    __file = __frame.f_code.co_filename
    __func = __frame.f_code.co_name
    for (k, v) in __frame.f_locals.items():
        if any((var in k) for var in ("__frame", "__file", "__func")):
            continue
        print(f"<INTROSPECT> {__file}:{__func} - {k}:{v.__class__.__name__}")
    "Return values from the specified domain that match the map-style metric in the metrics dictionary."
    (unexpected_condition, compute_domain_kwargs, accessor_domain_kwargs) = metrics[
        "unexpected_condition"
    ]
    '\n    In order to invoke the "ignore_row_if" filtering logic, "execution_engine.get_domain_records()" must be supplied\n    with all of the available "domain_kwargs" keys.\n    '
    domain_kwargs = dict(**compute_domain_kwargs, **accessor_domain_kwargs)
    df = execution_engine.get_domain_records(domain_kwargs=domain_kwargs)
    if "column_list" not in accessor_domain_kwargs:
        raise ValueError(
            'No "column_list" found in provided metric_domain_kwargs, but it is required for a multicolumn map metric\n(_spark_multicolumn_map_condition_values).\n'
        )
    column_list = accessor_domain_kwargs["column_list"]
    for column_name in column_list:
        if column_name not in metrics["table.columns"]:
            raise ge_exceptions.InvalidMetricAccessorDomainKwargsKeyError(
                message=f'Error: The column "{column_name}" in BatchData does not exist.'
            )
    data = df.withColumn("__unexpected", unexpected_condition)
    filtered = data.filter(F.col("__unexpected") == True).drop(F.col("__unexpected"))
    column_selector = [
        F.col(column_name).alias(column_name) for column_name in column_list
    ]
    domain_values = filtered.select(column_selector)
    result_format = metric_value_kwargs["result_format"]
    if result_format["result_format"] == "COMPLETE":
        domain_values = (
            domain_values.select(column_selector).toPandas().to_dict("records")
        )
    else:
        domain_values = (
            domain_values.select(column_selector)
            .limit(result_format["partial_unexpected_count"])
            .toPandas()
            .to_dict("records")
        )
    return domain_values


def _spark_multicolumn_map_condition_filtered_row_count(
    cls,
    execution_engine: SparkDFExecutionEngine,
    metric_domain_kwargs: Dict,
    metric_value_kwargs: Dict,
    metrics: Dict[(str, Any)],
    **kwargs,
):
    import inspect

    __frame = inspect.currentframe()
    __file = __frame.f_code.co_filename
    __func = __frame.f_code.co_name
    for (k, v) in __frame.f_locals.items():
        if any((var in k) for var in ("__frame", "__file", "__func")):
            continue
        print(f"<INTROSPECT> {__file}:{__func} - {k}:{v.__class__.__name__}")
    "Return record counts from the specified domain that match the map-style metric in the metrics dictionary."
    (_, compute_domain_kwargs, accessor_domain_kwargs) = metrics["unexpected_condition"]
    '\n    In order to invoke the "ignore_row_if" filtering logic, "execution_engine.get_domain_records()" must be supplied\n    with all of the available "domain_kwargs" keys.\n    '
    domain_kwargs = dict(**compute_domain_kwargs, **accessor_domain_kwargs)
    df = execution_engine.get_domain_records(domain_kwargs=domain_kwargs)
    if "column_list" not in accessor_domain_kwargs:
        raise ValueError(
            'No "column_list" found in provided metric_domain_kwargs, but it is required for a multicolumn map metric\n(_spark_multicolumn_map_condition_filtered_row_count).\n'
        )
    column_list = accessor_domain_kwargs["column_list"]
    for column_name in column_list:
        if column_name not in metrics["table.columns"]:
            raise ge_exceptions.InvalidMetricAccessorDomainKwargsKeyError(
                message=f'Error: The column "{column_name}" in BatchData does not exist.'
            )
    return df.count()


class MapMetricProvider(MetricProvider):
    condition_domain_keys = ("batch_id", "table", "row_condition", "condition_parser")
    function_domain_keys = ("batch_id", "table", "row_condition", "condition_parser")
    condition_value_keys = tuple()
    function_value_keys = tuple()
    filter_column_isnull = True
    SQLALCHEMY_SELECTABLE_METRICS = {
        "compound_columns.count",
        "compound_columns.unique",
    }

    @classmethod
    def _register_metric_functions(cls):
        import inspect

        __frame = inspect.currentframe()
        __file = __frame.f_code.co_filename
        __func = __frame.f_code.co_name
        for (k, v) in __frame.f_locals.items():
            if any((var in k) for var in ("__frame", "__file", "__func")):
                continue
            print(f"<INTROSPECT> {__file}:{__func} - {k}:{v.__class__.__name__}")
        if (not hasattr(cls, "function_metric_name")) and (
            not hasattr(cls, "condition_metric_name")
        ):
            return
        for (attr, candidate_metric_fn) in inspect.getmembers(cls):
            if not hasattr(candidate_metric_fn, "metric_engine"):
                continue
            metric_fn_type = getattr(candidate_metric_fn, "metric_fn_type")
            engine = candidate_metric_fn.metric_engine
            if not issubclass(engine, ExecutionEngine):
                raise ValueError(
                    "metric functions must be defined with an Execution Engine"
                )
            if metric_fn_type in [
                MetricPartialFunctionTypes.MAP_CONDITION_SERIES,
                MetricPartialFunctionTypes.MAP_CONDITION_FN,
                MetricPartialFunctionTypes.WINDOW_CONDITION_FN,
            ]:
                if not hasattr(cls, "condition_metric_name"):
                    raise ValueError(
                        "A MapMetricProvider must have a metric_condition_name to have a decorated column_condition_partial method."
                    )
                condition_provider = candidate_metric_fn
                metric_name = cls.condition_metric_name
                metric_domain_keys = cls.condition_domain_keys
                metric_value_keys = cls.condition_value_keys
                metric_definition_kwargs = getattr(
                    condition_provider, "metric_definition_kwargs", {}
                )
                domain_type = getattr(
                    condition_provider,
                    "domain_type",
                    metric_definition_kwargs.get(
                        "domain_type", MetricDomainTypes.TABLE
                    ),
                )
                if issubclass(engine, PandasExecutionEngine):
                    register_metric(
                        metric_name=f"{metric_name}.condition",
                        metric_domain_keys=metric_domain_keys,
                        metric_value_keys=metric_value_keys,
                        execution_engine=engine,
                        metric_class=cls,
                        metric_provider=condition_provider,
                        metric_fn_type=metric_fn_type,
                    )
                    register_metric(
                        metric_name=f"{metric_name}.unexpected_count",
                        metric_domain_keys=metric_domain_keys,
                        metric_value_keys=metric_value_keys,
                        execution_engine=engine,
                        metric_class=cls,
                        metric_provider=_pandas_map_condition_unexpected_count,
                        metric_fn_type=MetricFunctionTypes.VALUE,
                    )
                    register_metric(
                        metric_name=f"{metric_name}.unexpected_index_list",
                        metric_domain_keys=metric_domain_keys,
                        metric_value_keys=(*metric_value_keys, "result_format"),
                        execution_engine=engine,
                        metric_class=cls,
                        metric_provider=_pandas_map_condition_index,
                        metric_fn_type=MetricFunctionTypes.VALUE,
                    )
                    register_metric(
                        metric_name=f"{metric_name}.unexpected_rows",
                        metric_domain_keys=metric_domain_keys,
                        metric_value_keys=(*metric_value_keys, "result_format"),
                        execution_engine=engine,
                        metric_class=cls,
                        metric_provider=_pandas_map_condition_rows,
                        metric_fn_type=MetricFunctionTypes.VALUE,
                    )
                    if domain_type == MetricDomainTypes.COLUMN:
                        register_metric(
                            metric_name=f"{metric_name}.unexpected_values",
                            metric_domain_keys=metric_domain_keys,
                            metric_value_keys=(*metric_value_keys, "result_format"),
                            execution_engine=engine,
                            metric_class=cls,
                            metric_provider=_pandas_column_map_condition_values,
                            metric_fn_type=MetricFunctionTypes.VALUE,
                        )
                        register_metric(
                            metric_name=f"{metric_name}.unexpected_value_counts",
                            metric_domain_keys=metric_domain_keys,
                            metric_value_keys=(*metric_value_keys, "result_format"),
                            execution_engine=engine,
                            metric_class=cls,
                            metric_provider=_pandas_column_map_condition_value_counts,
                            metric_fn_type=MetricFunctionTypes.VALUE,
                        )
                    elif domain_type == MetricDomainTypes.COLUMN_PAIR:
                        register_metric(
                            metric_name=f"{metric_name}.unexpected_values",
                            metric_domain_keys=metric_domain_keys,
                            metric_value_keys=(*metric_value_keys, "result_format"),
                            execution_engine=engine,
                            metric_class=cls,
                            metric_provider=_pandas_column_pair_map_condition_values,
                            metric_fn_type=MetricFunctionTypes.VALUE,
                        )
                        register_metric(
                            metric_name=f"{metric_name}.filtered_row_count",
                            metric_domain_keys=metric_domain_keys,
                            metric_value_keys=(*metric_value_keys, "result_format"),
                            execution_engine=engine,
                            metric_class=cls,
                            metric_provider=_pandas_column_pair_map_condition_filtered_row_count,
                            metric_fn_type=MetricFunctionTypes.VALUE,
                        )
                    elif domain_type == MetricDomainTypes.MULTICOLUMN:
                        register_metric(
                            metric_name=f"{metric_name}.unexpected_values",
                            metric_domain_keys=metric_domain_keys,
                            metric_value_keys=(*metric_value_keys, "result_format"),
                            execution_engine=engine,
                            metric_class=cls,
                            metric_provider=_pandas_multicolumn_map_condition_values,
                            metric_fn_type=MetricFunctionTypes.VALUE,
                        )
                        register_metric(
                            metric_name=f"{metric_name}.filtered_row_count",
                            metric_domain_keys=metric_domain_keys,
                            metric_value_keys=(*metric_value_keys, "result_format"),
                            execution_engine=engine,
                            metric_class=cls,
                            metric_provider=_pandas_multicolumn_map_condition_filtered_row_count,
                            metric_fn_type=MetricFunctionTypes.VALUE,
                        )
                elif issubclass(engine, SqlAlchemyExecutionEngine):
                    register_metric(
                        metric_name=f"{metric_name}.condition",
                        metric_domain_keys=metric_domain_keys,
                        metric_value_keys=metric_value_keys,
                        execution_engine=engine,
                        metric_class=cls,
                        metric_provider=condition_provider,
                        metric_fn_type=metric_fn_type,
                    )
                    register_metric(
                        metric_name=f"{metric_name}.unexpected_rows",
                        metric_domain_keys=metric_domain_keys,
                        metric_value_keys=(*metric_value_keys, "result_format"),
                        execution_engine=engine,
                        metric_class=cls,
                        metric_provider=_sqlalchemy_map_condition_rows,
                        metric_fn_type=MetricFunctionTypes.VALUE,
                    )
                    if metric_fn_type == MetricPartialFunctionTypes.MAP_CONDITION_FN:
                        if domain_type == MetricDomainTypes.COLUMN:
                            register_metric(
                                metric_name=(
                                    metric_name + ".unexpected_count.aggregate_fn"
                                ),
                                metric_domain_keys=metric_domain_keys,
                                metric_value_keys=metric_value_keys,
                                execution_engine=engine,
                                metric_class=cls,
                                metric_provider=_sqlalchemy_map_condition_unexpected_count_aggregate_fn,
                                metric_fn_type=MetricPartialFunctionTypes.AGGREGATE_FN,
                            )
                            register_metric(
                                metric_name=f"{metric_name}.unexpected_count",
                                metric_domain_keys=metric_domain_keys,
                                metric_value_keys=metric_value_keys,
                                execution_engine=engine,
                                metric_class=cls,
                                metric_provider=None,
                                metric_fn_type=MetricFunctionTypes.VALUE,
                            )
                        else:
                            register_metric(
                                metric_name=f"{metric_name}.unexpected_count",
                                metric_domain_keys=metric_domain_keys,
                                metric_value_keys=metric_value_keys,
                                execution_engine=engine,
                                metric_class=cls,
                                metric_provider=_sqlalchemy_map_condition_unexpected_count_value,
                                metric_fn_type=MetricFunctionTypes.VALUE,
                            )
                    elif (
                        metric_fn_type == MetricPartialFunctionTypes.WINDOW_CONDITION_FN
                    ):
                        register_metric(
                            metric_name=f"{metric_name}.unexpected_count",
                            metric_domain_keys=metric_domain_keys,
                            metric_value_keys=metric_value_keys,
                            execution_engine=engine,
                            metric_class=cls,
                            metric_provider=_sqlalchemy_map_condition_unexpected_count_value,
                            metric_fn_type=MetricFunctionTypes.VALUE,
                        )
                    if domain_type == MetricDomainTypes.COLUMN:
                        register_metric(
                            metric_name=f"{metric_name}.unexpected_values",
                            metric_domain_keys=metric_domain_keys,
                            metric_value_keys=(*metric_value_keys, "result_format"),
                            execution_engine=engine,
                            metric_class=cls,
                            metric_provider=_sqlalchemy_column_map_condition_values,
                            metric_fn_type=MetricFunctionTypes.VALUE,
                        )
                        register_metric(
                            metric_name=f"{metric_name}.unexpected_value_counts",
                            metric_domain_keys=metric_domain_keys,
                            metric_value_keys=(*metric_value_keys, "result_format"),
                            execution_engine=engine,
                            metric_class=cls,
                            metric_provider=_sqlalchemy_column_map_condition_value_counts,
                            metric_fn_type=MetricFunctionTypes.VALUE,
                        )
                    elif domain_type == MetricDomainTypes.COLUMN_PAIR:
                        register_metric(
                            metric_name=f"{metric_name}.unexpected_values",
                            metric_domain_keys=metric_domain_keys,
                            metric_value_keys=(*metric_value_keys, "result_format"),
                            execution_engine=engine,
                            metric_class=cls,
                            metric_provider=_sqlalchemy_column_pair_map_condition_values,
                            metric_fn_type=MetricFunctionTypes.VALUE,
                        )
                        register_metric(
                            metric_name=f"{metric_name}.filtered_row_count",
                            metric_domain_keys=metric_domain_keys,
                            metric_value_keys=(*metric_value_keys, "result_format"),
                            execution_engine=engine,
                            metric_class=cls,
                            metric_provider=_sqlalchemy_column_pair_map_condition_filtered_row_count,
                            metric_fn_type=MetricFunctionTypes.VALUE,
                        )
                    elif domain_type == MetricDomainTypes.MULTICOLUMN:
                        register_metric(
                            metric_name=f"{metric_name}.unexpected_values",
                            metric_domain_keys=metric_domain_keys,
                            metric_value_keys=(*metric_value_keys, "result_format"),
                            execution_engine=engine,
                            metric_class=cls,
                            metric_provider=_sqlalchemy_multicolumn_map_condition_values,
                            metric_fn_type=MetricFunctionTypes.VALUE,
                        )
                        register_metric(
                            metric_name=f"{metric_name}.filtered_row_count",
                            metric_domain_keys=metric_domain_keys,
                            metric_value_keys=(*metric_value_keys, "result_format"),
                            execution_engine=engine,
                            metric_class=cls,
                            metric_provider=_sqlalchemy_multicolumn_map_condition_filtered_row_count,
                            metric_fn_type=MetricFunctionTypes.VALUE,
                        )
                elif issubclass(engine, SparkDFExecutionEngine):
                    register_metric(
                        metric_name=f"{metric_name}.condition",
                        metric_domain_keys=metric_domain_keys,
                        metric_value_keys=metric_value_keys,
                        execution_engine=engine,
                        metric_class=cls,
                        metric_provider=condition_provider,
                        metric_fn_type=metric_fn_type,
                    )
                    register_metric(
                        metric_name=f"{metric_name}.unexpected_rows",
                        metric_domain_keys=metric_domain_keys,
                        metric_value_keys=(*metric_value_keys, "result_format"),
                        execution_engine=engine,
                        metric_class=cls,
                        metric_provider=_spark_map_condition_rows,
                        metric_fn_type=MetricFunctionTypes.VALUE,
                    )
                    if metric_fn_type == MetricPartialFunctionTypes.MAP_CONDITION_FN:
                        if domain_type == MetricDomainTypes.COLUMN:
                            register_metric(
                                metric_name=(
                                    metric_name + ".unexpected_count.aggregate_fn"
                                ),
                                metric_domain_keys=metric_domain_keys,
                                metric_value_keys=metric_value_keys,
                                execution_engine=engine,
                                metric_class=cls,
                                metric_provider=_spark_map_condition_unexpected_count_aggregate_fn,
                                metric_fn_type=MetricPartialFunctionTypes.AGGREGATE_FN,
                            )
                            register_metric(
                                metric_name=f"{metric_name}.unexpected_count",
                                metric_domain_keys=metric_domain_keys,
                                metric_value_keys=metric_value_keys,
                                execution_engine=engine,
                                metric_class=cls,
                                metric_provider=None,
                                metric_fn_type=MetricFunctionTypes.VALUE,
                            )
                        else:
                            register_metric(
                                metric_name=f"{metric_name}.unexpected_count",
                                metric_domain_keys=metric_domain_keys,
                                metric_value_keys=metric_value_keys,
                                execution_engine=engine,
                                metric_class=cls,
                                metric_provider=_spark_map_condition_unexpected_count_value,
                                metric_fn_type=MetricFunctionTypes.VALUE,
                            )
                    elif (
                        metric_fn_type == MetricPartialFunctionTypes.WINDOW_CONDITION_FN
                    ):
                        register_metric(
                            metric_name=f"{metric_name}.unexpected_count",
                            metric_domain_keys=metric_domain_keys,
                            metric_value_keys=metric_value_keys,
                            execution_engine=engine,
                            metric_class=cls,
                            metric_provider=_spark_map_condition_unexpected_count_value,
                            metric_fn_type=MetricFunctionTypes.VALUE,
                        )
                    if domain_type == MetricDomainTypes.COLUMN:
                        register_metric(
                            metric_name=f"{metric_name}.unexpected_values",
                            metric_domain_keys=metric_domain_keys,
                            metric_value_keys=(*metric_value_keys, "result_format"),
                            execution_engine=engine,
                            metric_class=cls,
                            metric_provider=_spark_column_map_condition_values,
                            metric_fn_type=MetricFunctionTypes.VALUE,
                        )
                        register_metric(
                            metric_name=f"{metric_name}.unexpected_value_counts",
                            metric_domain_keys=metric_domain_keys,
                            metric_value_keys=(*metric_value_keys, "result_format"),
                            execution_engine=engine,
                            metric_class=cls,
                            metric_provider=_spark_column_map_condition_value_counts,
                            metric_fn_type=MetricFunctionTypes.VALUE,
                        )
                    elif domain_type == MetricDomainTypes.COLUMN_PAIR:
                        register_metric(
                            metric_name=f"{metric_name}.unexpected_values",
                            metric_domain_keys=metric_domain_keys,
                            metric_value_keys=(*metric_value_keys, "result_format"),
                            execution_engine=engine,
                            metric_class=cls,
                            metric_provider=_spark_column_pair_map_condition_values,
                            metric_fn_type=MetricFunctionTypes.VALUE,
                        )
                        register_metric(
                            metric_name=f"{metric_name}.filtered_row_count",
                            metric_domain_keys=metric_domain_keys,
                            metric_value_keys=(*metric_value_keys, "result_format"),
                            execution_engine=engine,
                            metric_class=cls,
                            metric_provider=_spark_column_pair_map_condition_filtered_row_count,
                            metric_fn_type=MetricFunctionTypes.VALUE,
                        )
                    elif domain_type == MetricDomainTypes.MULTICOLUMN:
                        register_metric(
                            metric_name=f"{metric_name}.unexpected_values",
                            metric_domain_keys=metric_domain_keys,
                            metric_value_keys=(*metric_value_keys, "result_format"),
                            execution_engine=engine,
                            metric_class=cls,
                            metric_provider=_spark_multicolumn_map_condition_values,
                            metric_fn_type=MetricFunctionTypes.VALUE,
                        )
                        register_metric(
                            metric_name=f"{metric_name}.filtered_row_count",
                            metric_domain_keys=metric_domain_keys,
                            metric_value_keys=(*metric_value_keys, "result_format"),
                            execution_engine=engine,
                            metric_class=cls,
                            metric_provider=_spark_multicolumn_map_condition_filtered_row_count,
                            metric_fn_type=MetricFunctionTypes.VALUE,
                        )
            elif metric_fn_type in [
                MetricPartialFunctionTypes.MAP_SERIES,
                MetricPartialFunctionTypes.MAP_FN,
                MetricPartialFunctionTypes.WINDOW_FN,
            ]:
                if not hasattr(cls, "function_metric_name"):
                    raise ValueError(
                        "A MapMetricProvider must have a function_metric_name to have a decorated column_function_partial method."
                    )
                map_function_provider = candidate_metric_fn
                metric_name = cls.function_metric_name
                metric_domain_keys = cls.function_domain_keys
                metric_value_keys = cls.function_value_keys
                register_metric(
                    metric_name=f"{metric_name}.map",
                    metric_domain_keys=metric_domain_keys,
                    metric_value_keys=metric_value_keys,
                    execution_engine=engine,
                    metric_class=cls,
                    metric_provider=map_function_provider,
                    metric_fn_type=metric_fn_type,
                )

    @classmethod
    def _get_evaluation_dependencies(
        cls,
        metric: MetricConfiguration,
        configuration: Optional[ExpectationConfiguration] = None,
        execution_engine: Optional[ExecutionEngine] = None,
        runtime_configuration: Optional[dict] = None,
    ):
        import inspect

        __frame = inspect.currentframe()
        __file = __frame.f_code.co_filename
        __func = __frame.f_code.co_name
        for (k, v) in __frame.f_locals.items():
            if any((var in k) for var in ("__frame", "__file", "__func")):
                continue
            print(f"<INTROSPECT> {__file}:{__func} - {k}:{v.__class__.__name__}")
        metric_name = metric.metric_name
        base_metric_value_kwargs = {
            k: v
            for (k, v) in metric.metric_value_kwargs.items()
            if (k != "result_format")
        }
        dependencies = {}
        metric_suffix = ".unexpected_count"
        if metric_name.endswith(metric_suffix):
            try:
                _ = get_metric_provider(f"{metric_name}.aggregate_fn", execution_engine)
                has_aggregate_fn = True
            except ge_exceptions.MetricProviderError:
                has_aggregate_fn = False
            if has_aggregate_fn:
                dependencies["metric_partial_fn"] = MetricConfiguration(
                    f"{metric_name}.aggregate_fn",
                    metric.metric_domain_kwargs,
                    base_metric_value_kwargs,
                )
            else:
                dependencies["unexpected_condition"] = MetricConfiguration(
                    f"{metric_name[:(- len(metric_suffix))]}.condition",
                    metric.metric_domain_kwargs,
                    base_metric_value_kwargs,
                )
        metric_suffix = ".unexpected_count.aggregate_fn"
        if metric_name.endswith(metric_suffix):
            dependencies["unexpected_condition"] = MetricConfiguration(
                f"{metric_name[:(- len(metric_suffix))]}.condition",
                metric.metric_domain_kwargs,
                base_metric_value_kwargs,
            )
        for metric_suffix in [
            ".unexpected_values",
            ".unexpected_value_counts",
            ".unexpected_index_list",
            ".unexpected_rows",
            ".filtered_row_count",
        ]:
            if metric_name.endswith(metric_suffix):
                dependencies["unexpected_condition"] = MetricConfiguration(
                    f"{metric_name[:(- len(metric_suffix))]}.condition",
                    metric.metric_domain_kwargs,
                    base_metric_value_kwargs,
                )
        try:
            _ = get_metric_provider(f"{metric_name}.map", execution_engine)
            dependencies["metric_map_fn"] = MetricConfiguration(
                f"{metric_name}.map",
                metric.metric_domain_kwargs,
                metric.metric_value_kwargs,
            )
        except ge_exceptions.MetricProviderError:
            pass
        return dependencies

    @staticmethod
    def is_sqlalchemy_metric_selectable(
        map_metric_provider: MetaMetricProvider,
    ) -> bool:
        import inspect

        __frame = inspect.currentframe()
        __file = __frame.f_code.co_filename
        __func = __frame.f_code.co_name
        for (k, v) in __frame.f_locals.items():
            if any((var in k) for var in ("__frame", "__file", "__func")):
                continue
            print(f"<INTROSPECT> {__file}:{__func} - {k}:{v.__class__.__name__}")
        '\n        :param map_metric_provider: object of type "MapMetricProvider", whose SQLAlchemy implementation is inspected\n        :return: boolean indicating whether or not the returned value of a method implementing the metric resolves all\n        columns -- hence the caller must not use "select_from" clause as part of its own SQLAlchemy query; otherwise an\n        unwanted selectable (e.g., table) will be added to "FROM", leading to duplicated and/or erroneous results.\n        '
        return (
            hasattr(map_metric_provider, "condition_metric_name")
            and (
                map_metric_provider.condition_metric_name
                in MapMetricProvider.SQLALCHEMY_SELECTABLE_METRICS
            )
        ) or (
            hasattr(map_metric_provider, "function_metric_name")
            and (
                map_metric_provider.function_metric_name
                in MapMetricProvider.SQLALCHEMY_SELECTABLE_METRICS
            )
        )


class ColumnMapMetricProvider(MapMetricProvider):
    condition_domain_keys = (
        "batch_id",
        "table",
        "column",
        "row_condition",
        "condition_parser",
    )
    function_domain_keys = (
        "batch_id",
        "table",
        "column",
        "row_condition",
        "condition_parser",
    )
    condition_value_keys = tuple()
    function_value_keys = tuple()

    @classmethod
    def _get_evaluation_dependencies(
        cls,
        metric: MetricConfiguration,
        configuration: Optional[ExpectationConfiguration] = None,
        execution_engine: Optional[ExecutionEngine] = None,
        runtime_configuration: Optional[dict] = None,
    ):
        import inspect

        __frame = inspect.currentframe()
        __file = __frame.f_code.co_filename
        __func = __frame.f_code.co_name
        for (k, v) in __frame.f_locals.items():
            if any((var in k) for var in ("__frame", "__file", "__func")):
                continue
            print(f"<INTROSPECT> {__file}:{__func} - {k}:{v.__class__.__name__}")
        dependencies: dict = super()._get_evaluation_dependencies(
            metric=metric,
            configuration=configuration,
            execution_engine=execution_engine,
            runtime_configuration=runtime_configuration,
        )
        table_domain_kwargs: dict = {
            k: v for (k, v) in metric.metric_domain_kwargs.items() if (k != "column")
        }
        dependencies["table.column_types"] = MetricConfiguration(
            metric_name="table.column_types",
            metric_domain_kwargs=table_domain_kwargs,
            metric_value_kwargs={"include_nested": True},
            metric_dependencies=None,
        )
        dependencies["table.columns"] = MetricConfiguration(
            metric_name="table.columns",
            metric_domain_kwargs=table_domain_kwargs,
            metric_value_kwargs=None,
            metric_dependencies=None,
        )
        dependencies["table.row_count"] = MetricConfiguration(
            metric_name="table.row_count",
            metric_domain_kwargs=table_domain_kwargs,
            metric_value_kwargs=None,
            metric_dependencies=None,
        )
        return dependencies


class ColumnPairMapMetricProvider(MapMetricProvider):
    condition_domain_keys = (
        "batch_id",
        "table",
        "column_A",
        "column_B",
        "row_condition",
        "condition_parser",
        "ignore_row_if",
    )
    function_domain_keys = (
        "batch_id",
        "table",
        "column_A",
        "column_B",
        "row_condition",
        "condition_parser",
        "ignore_row_if",
    )
    condition_value_keys = tuple()
    function_value_keys = tuple()

    @classmethod
    def _get_evaluation_dependencies(
        cls,
        metric: MetricConfiguration,
        configuration: Optional[ExpectationConfiguration] = None,
        execution_engine: Optional[ExecutionEngine] = None,
        runtime_configuration: Optional[dict] = None,
    ):
        import inspect

        __frame = inspect.currentframe()
        __file = __frame.f_code.co_filename
        __func = __frame.f_code.co_name
        for (k, v) in __frame.f_locals.items():
            if any((var in k) for var in ("__frame", "__file", "__func")):
                continue
            print(f"<INTROSPECT> {__file}:{__func} - {k}:{v.__class__.__name__}")
        dependencies: dict = super()._get_evaluation_dependencies(
            metric=metric,
            configuration=configuration,
            execution_engine=execution_engine,
            runtime_configuration=runtime_configuration,
        )
        table_domain_kwargs: dict = {
            k: v
            for (k, v) in metric.metric_domain_kwargs.items()
            if (k not in ["column_A", "column_B", "ignore_row_if"])
        }
        dependencies["table.column_types"] = MetricConfiguration(
            metric_name="table.column_types",
            metric_domain_kwargs=table_domain_kwargs,
            metric_value_kwargs={"include_nested": True},
            metric_dependencies=None,
        )
        dependencies["table.columns"] = MetricConfiguration(
            metric_name="table.columns",
            metric_domain_kwargs=table_domain_kwargs,
            metric_value_kwargs=None,
            metric_dependencies=None,
        )
        dependencies["table.row_count"] = MetricConfiguration(
            metric_name="table.row_count",
            metric_domain_kwargs=table_domain_kwargs,
            metric_value_kwargs=None,
            metric_dependencies=None,
        )
        return dependencies


class MulticolumnMapMetricProvider(MapMetricProvider):
    condition_domain_keys = (
        "batch_id",
        "table",
        "column_list",
        "row_condition",
        "condition_parser",
        "ignore_row_if",
    )
    function_domain_keys = (
        "batch_id",
        "table",
        "column_list",
        "row_condition",
        "condition_parser",
        "ignore_row_if",
    )
    condition_value_keys = tuple()
    function_value_keys = tuple()

    @classmethod
    def _get_evaluation_dependencies(
        cls,
        metric: MetricConfiguration,
        configuration: Optional[ExpectationConfiguration] = None,
        execution_engine: Optional[ExecutionEngine] = None,
        runtime_configuration: Optional[dict] = None,
    ):
        import inspect

        __frame = inspect.currentframe()
        __file = __frame.f_code.co_filename
        __func = __frame.f_code.co_name
        for (k, v) in __frame.f_locals.items():
            if any((var in k) for var in ("__frame", "__file", "__func")):
                continue
            print(f"<INTROSPECT> {__file}:{__func} - {k}:{v.__class__.__name__}")
        dependencies: dict = super()._get_evaluation_dependencies(
            metric=metric,
            configuration=configuration,
            execution_engine=execution_engine,
            runtime_configuration=runtime_configuration,
        )
        table_domain_kwargs: dict = {
            k: v
            for (k, v) in metric.metric_domain_kwargs.items()
            if (k not in ["column_list", "ignore_row_if"])
        }
        dependencies["table.column_types"] = MetricConfiguration(
            metric_name="table.column_types",
            metric_domain_kwargs=table_domain_kwargs,
            metric_value_kwargs={"include_nested": True},
            metric_dependencies=None,
        )
        dependencies["table.columns"] = MetricConfiguration(
            metric_name="table.columns",
            metric_domain_kwargs=table_domain_kwargs,
            metric_value_kwargs=None,
            metric_dependencies=None,
        )
        dependencies["table.row_count"] = MetricConfiguration(
            metric_name="table.row_count",
            metric_domain_kwargs=table_domain_kwargs,
            metric_value_kwargs=None,
            metric_dependencies=None,
        )
        return dependencies
