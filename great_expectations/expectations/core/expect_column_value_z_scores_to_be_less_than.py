from typing import Optional

from great_expectations.core.expectation_configuration import ExpectationConfiguration
from great_expectations.expectations.expectation import (
    ColumnMapExpectation,
    InvalidExpectationConfigurationError,
)


class ExpectColumnValueZScoresToBeLessThan(ColumnMapExpectation):
    "\n    Expect the Z-scores of a columns values to be less than a given threshold\n\n            expect_column_values_to_be_of_type is a :func:`column_map_expectation             <great_expectations.execution_engine.execution_engine.MetaExecutionEngine.column_map_expectation>` for\n            typed-column backends,\n            and also for PandasExecutionEngine where the column dtype and provided type_ are unambiguous constraints\n            (any dtype except 'object' or dtype of 'object' with type_ specified as 'object').\n\n            Args:\n                column (str):                     The column name of a numerical column.\n                threshold (number):                     A maximum Z-score threshold. All column Z-scores that are lower than this threshold will evaluate\n                    successfully.\n\n            Keyword Args:\n                mostly (None or a float between 0 and 1):                     Return `\"success\": True` if at least mostly fraction of values match the expectation.                     For more detail, see :ref:`mostly`.\n                double_sided (boolean):                     A True of False value indicating whether to evaluate double sidedly.\n                    Example:\n                    double_sided = True, threshold = 2 -> Z scores in non-inclusive interval(-2,2)\n                    double_sided = False, threshold = 2 -> Z scores in non-inclusive interval (-infinity,2)\n\n            Other Parameters:\n                result_format (str or None):                     Which output mode to use: `BOOLEAN_ONLY`, `BASIC`, `COMPLETE`, or `SUMMARY`.\n                    For more detail, see :ref:`result_format <result_format>`.\n                include_config (boolean):                     If True, then include the Expectation config as part of the result object.                     For more detail, see :ref:`include_config`.\n                catch_exceptions (boolean or None):                     If True, then catch exceptions and include them as part of the result object.                     For more detail, see :ref:`catch_exceptions`.\n                meta (dict or None):                     A JSON-serializable dictionary (nesting allowed) that will be included in the output without                     modification. For more detail, see :ref:`meta`.\n\n            Returns:\n                An ExpectationSuiteValidationResult\n\n                Exact fields vary depending on the values passed to :ref:`result_format <result_format>` and\n                :ref:`include_config`, :ref:`catch_exceptions`, and :ref:`meta`.\n"
    library_metadata = {
        "maturity": "production",
        "tags": ["core expectation", "column map expectation"],
        "contributors": ["@great_expectations"],
        "requirements": [],
    }
    map_metric = "column_values.z_score.under_threshold"
    success_keys = ("threshold", "double_sided", "mostly")
    default_kwarg_values = {
        "row_condition": None,
        "condition_parser": None,
        "threshold": None,
        "double_sided": True,
        "mostly": 1,
        "result_format": "BASIC",
        "include_config": True,
        "catch_exceptions": False,
    }
    args_keys = ("column", "threshold")

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
        if configuration is None:
            configuration = self.configuration
        try:
            assert (
                "threshold" in configuration.kwargs
            ), "A Z-score threshold must be provided"
            assert isinstance(
                configuration.kwargs["threshold"], (float, int, dict)
            ), "Provided threshold must be a number"
            if isinstance(configuration.kwargs["threshold"], dict):
                assert (
                    "$PARAMETER" in configuration.kwargs["threshold"]
                ), 'Evaluation Parameter dict for threshold kwarg must have "$PARAMETER" key.'
            assert isinstance(
                configuration.kwargs["double_sided"], (bool, dict)
            ), "Double sided parameter must be a boolean value"
            if isinstance(configuration.kwargs["double_sided"], dict):
                assert (
                    "$PARAMETER" in configuration.kwargs["double_sided"]
                ), 'Evaluation Parameter dict for double_sided kwarg must have "$PARAMETER" key.'
        except AssertionError as e:
            raise InvalidExpectationConfigurationError(str(e))
