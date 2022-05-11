from typing import Any, Dict

import pandas as pd

from great_expectations.execution_engine import (
    PandasExecutionEngine,
    SparkDFExecutionEngine,
    SqlAlchemyExecutionEngine,
)
from great_expectations.execution_engine.execution_engine import MetricDomainTypes
from great_expectations.expectations.metrics.import_manager import sa
from great_expectations.expectations.metrics.metric_provider import metric_value
from great_expectations.expectations.metrics.table_metric_provider import (
    TableMetricProvider,
)
from great_expectations.validator.metric_configuration import MetricConfiguration
from great_expectations.validator.validator import Validator


class TableHead(TableMetricProvider):
    metric_name = "table.head"
    value_keys = ("n_rows", "fetch_all")
    default_kwarg_values = {"n_rows": 5, "fetch_all": False}

    @metric_value(engine=PandasExecutionEngine)
    def _pandas(
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
            print(f"<INTROSPECT> {__file}:{__func} - {k}:{v.__class__.__name__}")
        (df, _, _) = execution_engine.get_compute_domain(
            metric_domain_kwargs, domain_type=MetricDomainTypes.TABLE
        )
        if metric_value_kwargs.get("fetch_all", cls.default_kwarg_values["fetch_all"]):
            return df
        return df.head(metric_value_kwargs["n_rows"])

    @metric_value(engine=SqlAlchemyExecutionEngine)
    def _sqlalchemy(
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
            print(f"<INTROSPECT> {__file}:{__func} - {k}:{v.__class__.__name__}")
        (selectable, _, _) = execution_engine.get_compute_domain(
            metric_domain_kwargs, domain_type=MetricDomainTypes.TABLE
        )
        df = None
        table_name = getattr(selectable, "name", None)
        if table_name is None:
            try:
                if metric_value_kwargs["fetch_all"]:
                    df = pd.read_sql_query(sql=selectable, con=execution_engine.engine)
                else:
                    df = next(
                        pd.read_sql_query(
                            sql=selectable,
                            con=execution_engine.engine,
                            chunksize=metric_value_kwargs["n_rows"],
                        )
                    )
            except (ValueError, NotImplementedError):
                df = None
            except StopIteration:
                validator = Validator(execution_engine=execution_engine)
                columns = validator.get_metric(
                    MetricConfiguration("table.columns", metric_domain_kwargs)
                )
                df = pd.DataFrame(columns=columns)
        else:
            try:
                if metric_value_kwargs["fetch_all"]:
                    df = pd.read_sql_table(
                        table_name=getattr(selectable, "name", None),
                        schema=getattr(selectable, "schema", None),
                        con=execution_engine.engine,
                    )
                else:
                    df = next(
                        pd.read_sql_table(
                            table_name=getattr(selectable, "name", None),
                            schema=getattr(selectable, "schema", None),
                            con=execution_engine.engine,
                            chunksize=metric_value_kwargs["n_rows"],
                        )
                    )
            except (ValueError, NotImplementedError):
                df = None
            except StopIteration:
                validator = Validator(execution_engine=execution_engine)
                columns = validator.get_metric(
                    MetricConfiguration("table.columns", metric_domain_kwargs)
                )
                df = pd.DataFrame(columns=columns)
        if df is None:
            stmt = sa.select(["*"]).select_from(selectable)
            if metric_value_kwargs["fetch_all"]:
                sql = stmt.compile(
                    dialect=execution_engine.engine.dialect,
                    compile_kwargs={"literal_binds": True},
                )
            elif execution_engine.engine.dialect.name.lower() == "mssql":
                sql = str(
                    stmt.compile(
                        dialect=execution_engine.engine.dialect,
                        compile_kwargs={"literal_binds": True},
                    )
                )
                sql = f"SELECT TOP {metric_value_kwargs['n_rows']}{sql[6:]}"
            else:
                stmt = stmt.limit(metric_value_kwargs["n_rows"])
                sql = stmt.compile(
                    dialect=execution_engine.engine.dialect,
                    compile_kwargs={"literal_binds": True},
                )
            df = pd.read_sql(sql, con=execution_engine.engine)
        return df

    @metric_value(engine=SparkDFExecutionEngine)
    def _spark(
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
            print(f"<INTROSPECT> {__file}:{__func} - {k}:{v.__class__.__name__}")
        (df, _, _) = execution_engine.get_compute_domain(
            metric_domain_kwargs, domain_type=MetricDomainTypes.TABLE
        )
        if metric_value_kwargs["fetch_all"]:
            return df.collect()
        return df.head(metric_value_kwargs["n_rows"])
