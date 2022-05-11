from typing import Dict, List, Optional

from great_expectations.core import ExpectationConfiguration
from great_expectations.execution_engine import ExecutionEngine
from great_expectations.expectations.expectation import ColumnExpectation
from great_expectations.expectations.util import render_evaluation_parameter_string
from great_expectations.render.renderer.renderer import renderer
from great_expectations.render.types import RenderedStringTemplateContent
from great_expectations.render.util import (
    handle_strict_min_max,
    parse_row_condition_string_pandas_engine,
    substitute_none_for_missing,
)
from great_expectations.rule_based_profiler.config import (
    ParameterBuilderConfig,
    RuleBasedProfilerConfig,
)
from great_expectations.rule_based_profiler.types import (
    DOMAIN_KWARGS_PARAMETER_FULLY_QUALIFIED_NAME,
    FULLY_QUALIFIED_PARAMETER_NAME_METADATA_KEY,
    FULLY_QUALIFIED_PARAMETER_NAME_SEPARATOR_CHARACTER,
    FULLY_QUALIFIED_PARAMETER_NAME_VALUE_KEY,
    PARAMETER_KEY,
    VARIABLES_KEY,
)


class ExpectColumnStdevToBeBetween(ColumnExpectation):
    'Expect the column standard deviation to be between a minimum value and a maximum value.\n            Uses sample standard deviation (normalized by N-1).\n\n            expect_column_stdev_to_be_between is a             :func:`column_aggregate_expectation\n            <great_expectations.execution_engine.MetaExecutionEngine.column_aggregate_expectation>`.\n\n            Args:\n                column (str):                     The column name.\n                min_value (float or None):                     The minimum value for the column standard deviation.\n                max_value (float or None):                     The maximum value for the column standard deviation.\n                strict_min (boolean):\n                    If True, the column standard deviation must be strictly larger than min_value, default=False\n                strict_max (boolean):\n                    If True, the column standard deviation must be strictly smaller than max_value, default=False\n\n            Other Parameters:\n                result_format (str or None):                     Which output mode to use: `BOOLEAN_ONLY`, `BASIC`, `COMPLETE`, or `SUMMARY`.                     For more detail, see :ref:`result_format <result_format>`.\n                include_config (boolean):                     If True, then include the expectation config as part of the result object.                     For more detail, see :ref:`include_config`.\n                catch_exceptions (boolean or None):                     If True, then catch exceptions and include them as part of the result object.                     For more detail, see :ref:`catch_exceptions`.\n                meta (dict or None):                     A JSON-serializable dictionary (nesting allowed) that will be included in the output without                     modification. For more detail, see :ref:`meta`.\n\n            Returns:\n                An ExpectationSuiteValidationResult\n\n                Exact fields vary depending on the values passed to :ref:`result_format <result_format>` and\n                :ref:`include_config`, :ref:`catch_exceptions`, and :ref:`meta`.\n\n            Notes:\n                These fields in the result object are customized for this expectation:\n                ::\n\n                    {\n                        "observed_value": (float) The true standard deviation for the column\n                    }\n\n                * min_value and max_value are both inclusive unless strict_min or strict_max are set to True.\n                * If min_value is None, then max_value is treated as an upper bound\n                * If max_value is None, then min_value is treated as a lower bound\n\n            See Also:\n                :func:`expect_column_mean_to_be_between                 <great_expectations.execution_engine.execution_engine.ExecutionEngine.expect_column_mean_to_be_between>`\n\n                :func:`expect_column_median_to_be_between                 <great_expectations.execution_engine.execution_engine.ExecutionEngine.expect_column_median_to_be_between>`\n\n'
    library_metadata = {
        "maturity": "production",
        "tags": ["core expectation", "column aggregate expectation"],
        "contributors": ["@great_expectations"],
        "requirements": [],
    }
    metric_dependencies = ("column.standard_deviation",)
    success_keys = (
        "min_value",
        "strict_min",
        "max_value",
        "strict_max",
        "auto",
        "profiler_config",
    )
    stdev_range_estimator_parameter_builder_config: ParameterBuilderConfig = ParameterBuilderConfig(
        module_name="great_expectations.rule_based_profiler.parameter_builder",
        class_name="NumericMetricRangeMultiBatchParameterBuilder",
        name="stdev_range_estimator",
        metric_name="column.standard_deviation",
        metric_domain_kwargs=DOMAIN_KWARGS_PARAMETER_FULLY_QUALIFIED_NAME,
        metric_value_kwargs=None,
        enforce_numeric_metric=True,
        replace_nan_with_zero=True,
        reduce_scalar_metric=True,
        false_positive_rate=f"{VARIABLES_KEY}false_positive_rate",
        quantile_statistic_interpolation_method=f"{VARIABLES_KEY}quantile_statistic_interpolation_method",
        estimator=f"{VARIABLES_KEY}estimator",
        num_bootstrap_samples=f"{VARIABLES_KEY}num_bootstrap_samples",
        bootstrap_random_seed=f"{VARIABLES_KEY}bootstrap_random_seed",
        include_bootstrap_samples_histogram_in_details=f"{VARIABLES_KEY}include_bootstrap_samples_histogram_in_details",
        truncate_values=f"{VARIABLES_KEY}truncate_values",
        round_decimals=f"{VARIABLES_KEY}round_decimals",
        evaluation_parameter_builder_configs=None,
        json_serialize=True,
    )
    validation_parameter_builder_configs: List[ParameterBuilderConfig] = [
        stdev_range_estimator_parameter_builder_config
    ]
    default_profiler_config: RuleBasedProfilerConfig = RuleBasedProfilerConfig(
        name="expect_column_stdev_to_be_between",
        config_version=1.0,
        variables={},
        rules={
            "default_expect_column_stdev_to_be_between_rule": {
                "variables": {
                    "strict_min": False,
                    "strict_max": False,
                    "false_positive_rate": 0.05,
                    "quantile_statistic_interpolation_method": "auto",
                    "estimator": "bootstrap",
                    "num_bootstrap_samples": 9999,
                    "bootstrap_random_seed": None,
                    "include_bootstrap_samples_histogram_in_details": False,
                    "truncate_values": {"lower_bound": 0, "upper_bound": None},
                    "round_decimals": 2,
                },
                "domain_builder": {
                    "class_name": "ColumnDomainBuilder",
                    "module_name": "great_expectations.rule_based_profiler.domain_builder",
                },
                "expectation_configuration_builders": [
                    {
                        "expectation_type": "expect_column_stdev_to_be_between",
                        "class_name": "DefaultExpectationConfigurationBuilder",
                        "module_name": "great_expectations.rule_based_profiler.expectation_configuration_builder",
                        "validation_parameter_builder_configs": validation_parameter_builder_configs,
                        "column": f"{DOMAIN_KWARGS_PARAMETER_FULLY_QUALIFIED_NAME}{FULLY_QUALIFIED_PARAMETER_NAME_SEPARATOR_CHARACTER}column",
                        "min_value": f"{PARAMETER_KEY}{stdev_range_estimator_parameter_builder_config.name}{FULLY_QUALIFIED_PARAMETER_NAME_SEPARATOR_CHARACTER}{FULLY_QUALIFIED_PARAMETER_NAME_VALUE_KEY}[0]",
                        "max_value": f"{PARAMETER_KEY}{stdev_range_estimator_parameter_builder_config.name}{FULLY_QUALIFIED_PARAMETER_NAME_SEPARATOR_CHARACTER}{FULLY_QUALIFIED_PARAMETER_NAME_VALUE_KEY}[1]",
                        "strict_min": f"{VARIABLES_KEY}strict_min",
                        "strict_max": f"{VARIABLES_KEY}strict_max",
                        "meta": {
                            "profiler_details": f"{PARAMETER_KEY}{stdev_range_estimator_parameter_builder_config.name}{FULLY_QUALIFIED_PARAMETER_NAME_SEPARATOR_CHARACTER}{FULLY_QUALIFIED_PARAMETER_NAME_METADATA_KEY}"
                        },
                    }
                ],
            }
        },
    )
    default_kwarg_values = {
        "min_value": None,
        "strict_min": False,
        "max_value": None,
        "strict_max": False,
        "result_format": "BASIC",
        "include_config": True,
        "catch_exceptions": False,
        "auto": False,
        "profiler_config": default_profiler_config,
    }
    args_keys = ("column", "min_value", "max_value", "strict_min", "strict_max")

    def validate_configuration(
        self, configuration: Optional[ExpectationConfiguration]
    ) -> None:
        import inspect

        __frame = inspect.currentframe()
        __file = __frame.f_code.co_filename
        __func = __frame.f_code.co_name
        for (k, v) in __frame.f_locals.items():
            if any((var in k) for var in ("__frame", "__file", "__func")):
                continue
            print(f"<INTROSPECT> {__file}:{__func} - {k}:{v.__class__.__name__}")
        "\n        Validates that a configuration has been set, and sets a configuration if it has yet to be set. Ensures that\n        necessary configuration arguments have been provided for the validation of the expectation.\n\n        Args:\n            configuration (OPTIONAL[ExpectationConfiguration]):                 An optional Expectation Configuration entry that will be used to configure the expectation\n        Returns:\n            None. Raises InvalidExpectationConfigurationError if the config is not validated successfully\n        "
        super().validate_configuration(configuration)
        self.validate_metric_value_between_configuration(configuration=configuration)

    @classmethod
    def _atomic_prescriptive_template(
        cls,
        configuration=None,
        result=None,
        language=None,
        runtime_configuration=None,
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
        runtime_configuration = runtime_configuration or {}
        include_column_name = runtime_configuration.get("include_column_name", True)
        include_column_name = (
            include_column_name if (include_column_name is not None) else True
        )
        styling = runtime_configuration.get("styling")
        params = substitute_none_for_missing(
            configuration.kwargs,
            [
                "column",
                "min_value",
                "max_value",
                "row_condition",
                "condition_parser",
                "strict_min",
                "strict_max",
            ],
        )
        params_with_json_schema = {
            "column": {"schema": {"type": "string"}, "value": params.get("column")},
            "min_value": {
                "schema": {"type": "number"},
                "value": params.get("min_value"),
            },
            "max_value": {
                "schema": {"type": "number"},
                "value": params.get("max_value"),
            },
            "row_condition": {
                "schema": {"type": "string"},
                "value": params.get("row_condition"),
            },
            "condition_parser": {
                "schema": {"type": "string"},
                "value": params.get("condition_parser"),
            },
            "strict_min": {
                "schema": {"type": "boolean"},
                "value": params.get("strict_min"),
            },
            "strict_max": {
                "schema": {"type": "boolean"},
                "value": params.get("strict_max"),
            },
        }
        if (params["min_value"] is None) and (params["max_value"] is None):
            template_str = "standard deviation may have any numerical value."
        else:
            (at_least_str, at_most_str) = handle_strict_min_max(params)
            if (params["min_value"] is not None) and (params["max_value"] is not None):
                template_str = f"standard deviation must be {at_least_str} $min_value and {at_most_str} $max_value."
            elif params["min_value"] is None:
                template_str = f"standard deviation must be {at_most_str} $max_value."
            elif params["max_value"] is None:
                template_str = f"standard deviation must be {at_least_str} $min_value."
        if include_column_name:
            template_str = f"$column {template_str}"
        if params["row_condition"] is not None:
            (
                conditional_template_str,
                conditional_params,
            ) = parse_row_condition_string_pandas_engine(
                params["row_condition"], with_schema=True
            )
            template_str = f"{conditional_template_str}, then {template_str}"
            params_with_json_schema.update(conditional_params)
        return (template_str, params_with_json_schema, styling)

    @classmethod
    @renderer(renderer_type="renderer.prescriptive")
    @render_evaluation_parameter_string
    def _prescriptive_renderer(
        cls,
        configuration=None,
        result=None,
        language=None,
        runtime_configuration=None,
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
        runtime_configuration = runtime_configuration or {}
        include_column_name = runtime_configuration.get("include_column_name", True)
        include_column_name = (
            include_column_name if (include_column_name is not None) else True
        )
        styling = runtime_configuration.get("styling")
        params = substitute_none_for_missing(
            configuration.kwargs,
            [
                "column",
                "min_value",
                "max_value",
                "row_condition",
                "condition_parser",
                "strict_min",
                "strict_max",
            ],
        )
        if (params["min_value"] is None) and (params["max_value"] is None):
            template_str = "standard deviation may have any numerical value."
        else:
            (at_least_str, at_most_str) = handle_strict_min_max(params)
            if (params["min_value"] is not None) and (params["max_value"] is not None):
                template_str = f"standard deviation must be {at_least_str} $min_value and {at_most_str} $max_value."
            elif params["min_value"] is None:
                template_str = f"standard deviation must be {at_most_str} $max_value."
            elif params["max_value"] is None:
                template_str = f"standard deviation must be {at_least_str} $min_value."
        if include_column_name:
            template_str = f"$column {template_str}"
        if params["row_condition"] is not None:
            (
                conditional_template_str,
                conditional_params,
            ) = parse_row_condition_string_pandas_engine(params["row_condition"])
            template_str = f"{conditional_template_str}, then {template_str}"
            params.update(conditional_params)
        return [
            RenderedStringTemplateContent(
                **{
                    "content_block_type": "string_template",
                    "string_template": {
                        "template": template_str,
                        "params": params,
                        "styling": styling,
                    },
                }
            )
        ]

    def _validate(
        self,
        configuration: ExpectationConfiguration,
        metrics: Dict,
        runtime_configuration: dict = None,
        execution_engine: ExecutionEngine = None,
    ):
        import inspect

        __frame = inspect.currentframe()
        __file = __frame.f_code.co_filename
        __func = __frame.f_code.co_name
        for (k, v) in __frame.f_locals.items():
            if any((var in k) for var in ("__frame", "__file", "__func")):
                continue
            print(f"<INTROSPECT> {__file}:{__func} - {k}:{v.__class__.__name__}")
        return self._validate_metric_value_between(
            metric_name="column.standard_deviation",
            configuration=configuration,
            metrics=metrics,
            runtime_configuration=runtime_configuration,
            execution_engine=execution_engine,
        )
