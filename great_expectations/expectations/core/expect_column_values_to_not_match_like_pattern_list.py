from typing import Optional

from great_expectations.core.expectation_configuration import ExpectationConfiguration
from great_expectations.expectations.expectation import (
    ColumnMapExpectation,
    InvalidExpectationConfigurationError,
)
from great_expectations.expectations.util import render_evaluation_parameter_string
from great_expectations.render.renderer.renderer import renderer
from great_expectations.render.util import substitute_none_for_missing


class ExpectColumnValuesToNotMatchLikePatternList(ColumnMapExpectation):
    'Expect column entries to be strings that do NOT match any of a provided list of like patterns expressions.\n\n    expect_column_values_to_not_match_like_pattern_list is a     :func:`column_map_expectation <great_expectations.execution_engine.execution_engine.MetaExecutionEngine\n    .column_map_expectation>`.\n\n    Args:\n        column (str):             The column name.\n        like_pattern_list (List[str]):             The list of like pattern expressions the column entries should NOT match.\n\n    Keyword Args:\n        mostly (None or a float between 0 and 1):             Return `"success": True` if at least mostly fraction of values match the expectation.             For more detail, see :ref:`mostly`.\n\n    Other Parameters:\n        result_format (str or None):             Which output mode to use: `BOOLEAN_ONLY`, `BASIC`, `COMPLETE`, or `SUMMARY`.\n            For more detail, see :ref:`result_format <result_format>`.\n        include_config (boolean):             If True, then include the expectation config as part of the result object.             For more detail, see :ref:`include_config`.\n        catch_exceptions (boolean or None):             If True, then catch exceptions and include them as part of the result object.             For more detail, see :ref:`catch_exceptions`.\n        meta (dict or None):             A JSON-serializable dictionary (nesting allowed) that will be included in the output without             modification. For more detail, see :ref:`meta`.\n\n    Returns:\n        An ExpectationSuiteValidationResult\n\n        Exact fields vary depending on the values passed to :ref:`result_format <result_format>` and\n        :ref:`include_config`, :ref:`catch_exceptions`, and :ref:`meta`.\n\n    See Also:\n        :func:`expect_column_values_to_match_regex         <great_expectations.execution_engine.execution_engine.ExecutionEngine.expect_column_values_to_match_regex>`\n\n        :func:`expect_column_values_to_match_regex_list         <great_expectations.execution_engine.execution_engine.ExecutionEngine\n        .expect_column_values_to_match_regex_list>`\n'
    library_metadata = {
        "maturity": "production",
        "tags": ["core expectation", "column map expectation"],
        "contributors": ["@great_expectations"],
        "requirements": [],
        "has_full_test_suite": True,
        "manually_reviewed_code": True,
    }
    map_metric = "column_values.not_match_like_pattern_list"
    success_keys = ("like_pattern_list", "mostly")
    default_kwarg_values = {
        "like_pattern_list": None,
        "row_condition": None,
        "condition_parser": None,
        "mostly": 1,
        "result_format": "BASIC",
        "include_config": True,
        "catch_exceptions": True,
    }
    args_keys = ("column", "like_pattern_list")

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
        super().validate_configuration(configuration)
        try:
            assert (
                "like_pattern_list" in configuration.kwargs
            ), "Must provide like_pattern_list"
            assert isinstance(
                configuration.kwargs.get("like_pattern_list"), (list, dict)
            ), "like_pattern_list must be a list"
            assert isinstance(configuration.kwargs.get("like_pattern_list"), dict) or (
                len(configuration.kwargs.get("like_pattern_list")) > 0
            ), "At least one like_pattern must be supplied in the like_pattern_list."
            if isinstance(configuration.kwargs.get("like_pattern_list"), dict):
                assert "$PARAMETER" in configuration.kwargs.get(
                    "like_pattern_list"
                ), 'Evaluation Parameter dict for like_pattern_list kwarg must have "$PARAMETER" key.'
        except AssertionError as e:
            raise InvalidExpectationConfigurationError(str(e))

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
    ) -> None:
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
            ["column", "mostly", "row_condition", "condition_parser"],
        )
