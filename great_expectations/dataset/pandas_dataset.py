import inspect
import json
import logging
import warnings
from datetime import datetime
from functools import wraps
from operator import ge, gt, le, lt
from typing import List

import jsonschema
import numpy as np
import pandas as pd
from dateutil.parser import parse
from scipy import stats

from great_expectations.core.expectation_configuration import ExpectationConfiguration
from great_expectations.data_asset import DataAsset
from great_expectations.data_asset.util import DocInherit, parse_result_format
from great_expectations.dataset.dataset import Dataset
from great_expectations.dataset.util import (
    _scipy_distribution_positional_args_from_dict,
    is_valid_continuous_partition_object,
    validate_distribution_parameters,
)

logger = logging.getLogger(__name__)


class MetaPandasDataset(Dataset):
    "MetaPandasDataset is a thin layer between Dataset and PandasDataset.\n\n    This two-layer inheritance is required to make @classmethod decorators work.\n\n    Practically speaking, that means that MetaPandasDataset implements     expectation decorators, like `column_map_expectation` and `column_aggregate_expectation`,     and PandasDataset implements the expectation methods themselves.\n"

    def __init__(self, *args, **kwargs) -> None:
        import inspect

        __frame = inspect.currentframe()
        __file = __frame.f_code.co_filename
        __func = __frame.f_code.co_name
        for (k, v) in __frame.f_locals.items():
            if any((var in k) for var in ("__frame", "__file", "__func")):
                continue
            print(f"<INTROSPECT> {__file}:{__func} - {k}:{v.__class__.__name__}")
        super().__init__(*args, **kwargs)

    @classmethod
    def column_map_expectation(cls, func):
        import inspect

        __frame = inspect.currentframe()
        __file = __frame.f_code.co_filename
        __func = __frame.f_code.co_name
        for (k, v) in __frame.f_locals.items():
            if any((var in k) for var in ("__frame", "__file", "__func")):
                continue
            print(f"<INTROSPECT> {__file}:{__func} - {k}:{v.__class__.__name__}")
        'Constructs an expectation using column-map semantics.\n\n\n        The MetaPandasDataset implementation replaces the "column" parameter supplied by the user with a pandas Series\n        object containing the actual column from the relevant pandas dataframe. This simplifies the implementing expectation\n        logic while preserving the standard Dataset signature and expected behavior.\n\n        See :func:`column_map_expectation <great_expectations.data_asset.dataset.Dataset.column_map_expectation>`         for full documentation of this function.\n        '
        argspec = inspect.getfullargspec(func)[0][1:]

        @cls.expectation(argspec)
        @wraps(func)
        def inner_wrapper(
            self,
            column,
            mostly=None,
            result_format=None,
            row_condition=None,
            condition_parser=None,
            *args,
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
            if result_format is None:
                result_format = self.default_expectation_args["result_format"]
            result_format = parse_result_format(result_format)
            if row_condition and self._supports_row_condition:
                data = self._apply_row_condition(
                    row_condition=row_condition, condition_parser=condition_parser
                )
            else:
                data = self
            series = data[column]
            func_args = inspect.getfullargspec(func)[0][1:]
            if (
                "parse_strings_as_datetimes" in func_args
            ) and pd.api.types.is_datetime64_any_dtype(series):
                kwargs["parse_strings_as_datetimes"] = True
            if func.__name__ in [
                "expect_column_values_to_not_be_null",
                "expect_column_values_to_be_null",
            ]:
                boolean_mapped_null_values = np.full(series.shape, False)
                result_format["partial_unexpected_count"] = 0
            else:
                boolean_mapped_null_values = series.isnull().values
            element_count = int(len(series))
            nonnull_values = series[(boolean_mapped_null_values == False)]
            nonnull_count = int((boolean_mapped_null_values == False).sum())
            boolean_mapped_success_values = func(self, nonnull_values, *args, **kwargs)
            success_count = np.count_nonzero(boolean_mapped_success_values)
            unexpected_list = list(
                nonnull_values[(boolean_mapped_success_values == False)]
            )
            unexpected_index_list = list(
                nonnull_values[(boolean_mapped_success_values == False)].index
            )
            if "output_strftime_format" in kwargs:
                output_strftime_format = kwargs["output_strftime_format"]
                parsed_unexpected_list = []
                for val in unexpected_list:
                    if val is None:
                        parsed_unexpected_list.append(val)
                    else:
                        if isinstance(val, str):
                            val = parse(val)
                        parsed_unexpected_list.append(
                            datetime.strftime(val, output_strftime_format)
                        )
                unexpected_list = parsed_unexpected_list
            (success, percent_success) = self._calc_map_expectation_success(
                success_count, nonnull_count, mostly
            )
            return_obj = self._format_map_output(
                result_format,
                success,
                element_count,
                nonnull_count,
                len(unexpected_list),
                unexpected_list,
                unexpected_index_list,
            )
            if func.__name__ in [
                "expect_column_values_to_not_be_null",
                "expect_column_values_to_be_null",
            ]:
                del return_obj["result"]["unexpected_percent_nonmissing"]
                del return_obj["result"]["missing_count"]
                del return_obj["result"]["missing_percent"]
                try:
                    del return_obj["result"]["partial_unexpected_counts"]
                    del return_obj["result"]["partial_unexpected_list"]
                except KeyError:
                    pass
            return return_obj

        inner_wrapper.__name__ = func.__name__
        inner_wrapper.__doc__ = func.__doc__
        return inner_wrapper

    @classmethod
    def column_pair_map_expectation(cls, func):
        import inspect

        __frame = inspect.currentframe()
        __file = __frame.f_code.co_filename
        __func = __frame.f_code.co_name
        for (k, v) in __frame.f_locals.items():
            if any((var in k) for var in ("__frame", "__file", "__func")):
                continue
            print(f"<INTROSPECT> {__file}:{__func} - {k}:{v.__class__.__name__}")
        "\n        The column_pair_map_expectation decorator handles boilerplate issues surrounding the common pattern of evaluating\n        truthiness of some condition on a per row basis across a pair of columns.\n        "
        argspec = inspect.getfullargspec(func)[0][1:]

        @cls.expectation(argspec)
        @wraps(func)
        def inner_wrapper(
            self,
            column_A,
            column_B,
            mostly=None,
            ignore_row_if="both_values_are_missing",
            result_format=None,
            row_condition=None,
            condition_parser=None,
            *args,
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
            if result_format is None:
                result_format = self.default_expectation_args["result_format"]
            if row_condition:
                self = self.query(row_condition)
            series_A = self[column_A]
            series_B = self[column_B]
            if ignore_row_if == "both_values_are_missing":
                boolean_mapped_null_values = series_A.isnull() & series_B.isnull()
            elif ignore_row_if == "either_value_is_missing":
                boolean_mapped_null_values = series_A.isnull() | series_B.isnull()
            elif ignore_row_if == "never":
                '\n                TODO: <Alex>Note: The value of the "ignore_row_if" directive in the commented out line above is correct.\n                However, fixing the error would constitute a breaking change.  Hence, the documentation is updated now\n                (8/16/2021), while the implementation is corrected as part of the Expectations V3 API release.\n                </Alex>\n'
                boolean_mapped_null_values = series_A.map(lambda x: False)
            else:
                raise ValueError("Unknown value of ignore_row_if: %s", (ignore_row_if,))
            assert len(series_A) == len(
                series_B
            ), "Series A and B must be the same length"
            element_count = int(len(series_A))
            nonnull_count = (boolean_mapped_null_values == False).sum()
            nonnull_values_A = series_A[(boolean_mapped_null_values == False)]
            nonnull_values_B = series_B[(boolean_mapped_null_values == False)]
            nonnull_values = [
                value_pair
                for value_pair in zip(list(nonnull_values_A), list(nonnull_values_B))
            ]
            boolean_mapped_success_values = func(
                self, nonnull_values_A, nonnull_values_B, *args, **kwargs
            )
            success_count = boolean_mapped_success_values.sum()
            unexpected_list = [
                value_pair
                for value_pair in zip(
                    list(
                        series_A[
                            (
                                (boolean_mapped_success_values == False)
                                & (boolean_mapped_null_values == False)
                            )
                        ]
                    ),
                    list(
                        series_B[
                            (
                                (boolean_mapped_success_values == False)
                                & (boolean_mapped_null_values == False)
                            )
                        ]
                    ),
                )
            ]
            unexpected_index_list = list(
                series_A[
                    (
                        (boolean_mapped_success_values == False)
                        & (boolean_mapped_null_values == False)
                    )
                ].index
            )
            (success, percent_success) = self._calc_map_expectation_success(
                success_count, nonnull_count, mostly
            )
            return_obj = self._format_map_output(
                result_format,
                success,
                element_count,
                nonnull_count,
                len(unexpected_list),
                unexpected_list,
                unexpected_index_list,
            )
            return return_obj

        inner_wrapper.__name__ = func.__name__
        inner_wrapper.__doc__ = func.__doc__
        return inner_wrapper

    @classmethod
    def multicolumn_map_expectation(cls, func):
        import inspect

        __frame = inspect.currentframe()
        __file = __frame.f_code.co_filename
        __func = __frame.f_code.co_name
        for (k, v) in __frame.f_locals.items():
            if any((var in k) for var in ("__frame", "__file", "__func")):
                continue
            print(f"<INTROSPECT> {__file}:{__func} - {k}:{v.__class__.__name__}")
        "\n        The multicolumn_map_expectation decorator handles boilerplate issues surrounding the common pattern of\n        evaluating truthiness of some condition on a per row basis across a set of columns.\n        "
        argspec = inspect.getfullargspec(func)[0][1:]

        @cls.expectation(argspec)
        @wraps(func)
        def inner_wrapper(
            self,
            column_list,
            mostly=None,
            ignore_row_if="all_values_are_missing",
            result_format=None,
            row_condition=None,
            condition_parser=None,
            *args,
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
            if result_format is None:
                result_format = self.default_expectation_args["result_format"]
            if row_condition:
                self = self.query(row_condition)
            test_df = self[column_list]
            if ignore_row_if == "all_values_are_missing":
                boolean_mapped_skip_values = test_df.isnull().all(axis=1)
            elif ignore_row_if == "any_value_is_missing":
                boolean_mapped_skip_values = test_df.isnull().any(axis=1)
            elif ignore_row_if == "never":
                boolean_mapped_skip_values = pd.Series([False] * len(test_df))
            else:
                raise ValueError("Unknown value of ignore_row_if: %s", (ignore_row_if,))
            boolean_mapped_success_values = func(
                self, test_df[(boolean_mapped_skip_values == False)], *args, **kwargs
            )
            success_count = boolean_mapped_success_values.sum()
            nonnull_count = (~boolean_mapped_skip_values).sum()
            element_count = len(test_df)
            unexpected_list = test_df[
                (
                    (boolean_mapped_skip_values == False)
                    & (boolean_mapped_success_values == False)
                )
            ]
            unexpected_index_list = list(unexpected_list.index)
            (success, percent_success) = self._calc_map_expectation_success(
                success_count, nonnull_count, mostly
            )
            return_obj = self._format_map_output(
                result_format,
                success,
                element_count,
                nonnull_count,
                len(unexpected_list),
                unexpected_list.to_dict(orient="records"),
                unexpected_index_list,
            )
            return return_obj

        inner_wrapper.__name__ = func.__name__
        inner_wrapper.__doc__ = func.__doc__
        return inner_wrapper


class PandasDataset(MetaPandasDataset, pd.DataFrame):
    "\nPandasDataset instantiates the great_expectations Expectations API as a subclass of a pandas.DataFrame.\n\nFor the full API reference, please see :func:`Dataset <great_expectations.data_asset.dataset.Dataset>`\n\nNotes:\n    1. Samples and Subsets of PandaDataSet have ALL the expectations of the original        data frame unless the user specifies the ``discard_subset_failing_expectations = True``        property on the original data frame.\n    2. Concatenations, joins, and merges of PandaDataSets contain NO expectations (since no autoinspection\n       is performed by default).\n\n--ge-feature-maturity-info--\n\n    id: validation_engine_pandas\n    title: Validation Engine - Pandas\n    icon:\n    short_description: Use Pandas DataFrame to validate data\n    description: Use Pandas DataFrame to validate data\n    how_to_guide_url:\n    maturity: Production\n    maturity_details:\n        api_stability: Stable\n        implementation_completeness: Complete\n        unit_test_coverage: Complete\n        integration_infrastructure_test_coverage: N/A -> see relevant Datasource evaluation\n        documentation_completeness: Complete\n        bug_risk: Low\n        expectation_completeness: Complete\n\n--ge-feature-maturity-info--\n"
    _internal_names = pd.DataFrame._internal_names + [
        "_batch_kwargs",
        "_batch_markers",
        "_batch_parameters",
        "_batch_id",
        "_expectation_suite",
        "_config",
        "caching",
        "default_expectation_args",
        "discard_subset_failing_expectations",
    ]
    _internal_names_set = set(_internal_names)
    _supports_row_condition = True

    def __init__(self, *args, **kwargs) -> None:
        import inspect

        __frame = inspect.currentframe()
        __file = __frame.f_code.co_filename
        __func = __frame.f_code.co_name
        for (k, v) in __frame.f_locals.items():
            if any((var in k) for var in ("__frame", "__file", "__func")):
                continue
            print(f"<INTROSPECT> {__file}:{__func} - {k}:{v.__class__.__name__}")
        super().__init__(*args, **kwargs)
        self.discard_subset_failing_expectations = kwargs.get(
            "discard_subset_failing_expectations", False
        )

    @property
    def _constructor(self):
        import inspect

        __frame = inspect.currentframe()
        __file = __frame.f_code.co_filename
        __func = __frame.f_code.co_name
        for (k, v) in __frame.f_locals.items():
            if any((var in k) for var in ("__frame", "__file", "__func")):
                continue
            print(f"<INTROSPECT> {__file}:{__func} - {k}:{v.__class__.__name__}")
        return self.__class__

    def __finalize__(self, other, method=None, **kwargs):
        import inspect

        __frame = inspect.currentframe()
        __file = __frame.f_code.co_filename
        __func = __frame.f_code.co_name
        for (k, v) in __frame.f_locals.items():
            if any((var in k) for var in ("__frame", "__file", "__func")):
                continue
            print(f"<INTROSPECT> {__file}:{__func} - {k}:{v.__class__.__name__}")
        if isinstance(other, PandasDataset):
            self._initialize_expectations(other._expectation_suite)
            self.discard_subset_failing_expectations = getattr(
                other,
                "discard_subset_failing_expectations",
                self.discard_subset_failing_expectations,
            )
            if self.discard_subset_failing_expectations:
                self.discard_failing_expectations()
        super().__finalize__(other, method, **kwargs)
        return self

    def _apply_row_condition(self, row_condition, condition_parser):
        import inspect

        __frame = inspect.currentframe()
        __file = __frame.f_code.co_filename
        __func = __frame.f_code.co_name
        for (k, v) in __frame.f_locals.items():
            if any((var in k) for var in ("__frame", "__file", "__func")):
                continue
            print(f"<INTROSPECT> {__file}:{__func} - {k}:{v.__class__.__name__}")
        if condition_parser not in ["python", "pandas"]:
            raise ValueError(
                "condition_parser is required when setting a row_condition, and must be 'python' or 'pandas'"
            )
        else:
            return self.query(row_condition, parser=condition_parser)

    def get_row_count(self):
        import inspect

        __frame = inspect.currentframe()
        __file = __frame.f_code.co_filename
        __func = __frame.f_code.co_name
        for (k, v) in __frame.f_locals.items():
            if any((var in k) for var in ("__frame", "__file", "__func")):
                continue
            print(f"<INTROSPECT> {__file}:{__func} - {k}:{v.__class__.__name__}")
        return self.shape[0]

    def get_column_count(self):
        import inspect

        __frame = inspect.currentframe()
        __file = __frame.f_code.co_filename
        __func = __frame.f_code.co_name
        for (k, v) in __frame.f_locals.items():
            if any((var in k) for var in ("__frame", "__file", "__func")):
                continue
            print(f"<INTROSPECT> {__file}:{__func} - {k}:{v.__class__.__name__}")
        return self.shape[1]

    def get_table_columns(self) -> List[str]:
        import inspect

        __frame = inspect.currentframe()
        __file = __frame.f_code.co_filename
        __func = __frame.f_code.co_name
        for (k, v) in __frame.f_locals.items():
            if any((var in k) for var in ("__frame", "__file", "__func")):
                continue
            print(f"<INTROSPECT> {__file}:{__func} - {k}:{v.__class__.__name__}")
        return list(self.columns)

    def get_column_sum(self, column):
        import inspect

        __frame = inspect.currentframe()
        __file = __frame.f_code.co_filename
        __func = __frame.f_code.co_name
        for (k, v) in __frame.f_locals.items():
            if any((var in k) for var in ("__frame", "__file", "__func")):
                continue
            print(f"<INTROSPECT> {__file}:{__func} - {k}:{v.__class__.__name__}")
        return self[column].sum()

    def get_column_max(self, column, parse_strings_as_datetimes=False):
        import inspect

        __frame = inspect.currentframe()
        __file = __frame.f_code.co_filename
        __func = __frame.f_code.co_name
        for (k, v) in __frame.f_locals.items():
            if any((var in k) for var in ("__frame", "__file", "__func")):
                continue
            print(f"<INTROSPECT> {__file}:{__func} - {k}:{v.__class__.__name__}")
        temp_column = self[column].dropna()
        if parse_strings_as_datetimes:
            temp_column = temp_column.map(parse)
        return temp_column.max()

    def get_column_min(self, column, parse_strings_as_datetimes=False):
        import inspect

        __frame = inspect.currentframe()
        __file = __frame.f_code.co_filename
        __func = __frame.f_code.co_name
        for (k, v) in __frame.f_locals.items():
            if any((var in k) for var in ("__frame", "__file", "__func")):
                continue
            print(f"<INTROSPECT> {__file}:{__func} - {k}:{v.__class__.__name__}")
        temp_column = self[column].dropna()
        if parse_strings_as_datetimes:
            temp_column = temp_column.map(parse)
        return temp_column.min()

    def get_column_mean(self, column):
        import inspect

        __frame = inspect.currentframe()
        __file = __frame.f_code.co_filename
        __func = __frame.f_code.co_name
        for (k, v) in __frame.f_locals.items():
            if any((var in k) for var in ("__frame", "__file", "__func")):
                continue
            print(f"<INTROSPECT> {__file}:{__func} - {k}:{v.__class__.__name__}")
        return self[column].mean()

    def get_column_nonnull_count(self, column):
        import inspect

        __frame = inspect.currentframe()
        __file = __frame.f_code.co_filename
        __func = __frame.f_code.co_name
        for (k, v) in __frame.f_locals.items():
            if any((var in k) for var in ("__frame", "__file", "__func")):
                continue
            print(f"<INTROSPECT> {__file}:{__func} - {k}:{v.__class__.__name__}")
        series = self[column]
        null_indexes = series.isnull()
        nonnull_values = series[(null_indexes == False)]
        return len(nonnull_values)

    def get_column_value_counts(self, column, sort="value", collate=None):
        import inspect

        __frame = inspect.currentframe()
        __file = __frame.f_code.co_filename
        __func = __frame.f_code.co_name
        for (k, v) in __frame.f_locals.items():
            if any((var in k) for var in ("__frame", "__file", "__func")):
                continue
            print(f"<INTROSPECT> {__file}:{__func} - {k}:{v.__class__.__name__}")
        if sort not in ["value", "count", "none"]:
            raise ValueError("sort must be either 'value', 'count', or 'none'")
        if collate is not None:
            raise ValueError("collate parameter is not supported in PandasDataset")
        counts = self[column].value_counts()
        if sort == "value":
            try:
                counts.sort_index(inplace=True)
            except TypeError:
                if self[column].dtype == object:
                    counts.index = counts.index.astype(str)
                    counts.sort_index(inplace=True)
        elif sort == "counts":
            counts.sort_values(inplace=True)
        counts.name = "count"
        counts.index.name = "value"
        return counts

    def get_column_unique_count(self, column):
        import inspect

        __frame = inspect.currentframe()
        __file = __frame.f_code.co_filename
        __func = __frame.f_code.co_name
        for (k, v) in __frame.f_locals.items():
            if any((var in k) for var in ("__frame", "__file", "__func")):
                continue
            print(f"<INTROSPECT> {__file}:{__func} - {k}:{v.__class__.__name__}")
        return self.get_column_value_counts(column).shape[0]

    def get_column_modes(self, column):
        import inspect

        __frame = inspect.currentframe()
        __file = __frame.f_code.co_filename
        __func = __frame.f_code.co_name
        for (k, v) in __frame.f_locals.items():
            if any((var in k) for var in ("__frame", "__file", "__func")):
                continue
            print(f"<INTROSPECT> {__file}:{__func} - {k}:{v.__class__.__name__}")
        return list(self[column].mode().values)

    def get_column_median(self, column):
        import inspect

        __frame = inspect.currentframe()
        __file = __frame.f_code.co_filename
        __func = __frame.f_code.co_name
        for (k, v) in __frame.f_locals.items():
            if any((var in k) for var in ("__frame", "__file", "__func")):
                continue
            print(f"<INTROSPECT> {__file}:{__func} - {k}:{v.__class__.__name__}")
        return self[column].median()

    def get_column_quantiles(self, column, quantiles, allow_relative_error=False):
        import inspect

        __frame = inspect.currentframe()
        __file = __frame.f_code.co_filename
        __func = __frame.f_code.co_name
        for (k, v) in __frame.f_locals.items():
            if any((var in k) for var in ("__frame", "__file", "__func")):
                continue
            print(f"<INTROSPECT> {__file}:{__func} - {k}:{v.__class__.__name__}")
        interpolation_options = ("linear", "lower", "higher", "midpoint", "nearest")
        if not allow_relative_error:
            allow_relative_error = "nearest"
        if allow_relative_error not in interpolation_options:
            raise ValueError(
                f"If specified for pandas, allow_relative_error must be one an allowed value for the 'interpolation'parameter of .quantile() (one of {interpolation_options})"
            )
        return (
            self[column]
            .quantile(quantiles, interpolation=allow_relative_error)
            .tolist()
        )

    def get_column_stdev(self, column):
        import inspect

        __frame = inspect.currentframe()
        __file = __frame.f_code.co_filename
        __func = __frame.f_code.co_name
        for (k, v) in __frame.f_locals.items():
            if any((var in k) for var in ("__frame", "__file", "__func")):
                continue
            print(f"<INTROSPECT> {__file}:{__func} - {k}:{v.__class__.__name__}")
        return self[column].std()

    def get_column_hist(self, column, bins):
        import inspect

        __frame = inspect.currentframe()
        __file = __frame.f_code.co_filename
        __func = __frame.f_code.co_name
        for (k, v) in __frame.f_locals.items():
            if any((var in k) for var in ("__frame", "__file", "__func")):
                continue
            print(f"<INTROSPECT> {__file}:{__func} - {k}:{v.__class__.__name__}")
        (hist, bin_edges) = np.histogram(self[column], bins, density=False)
        return list(hist)

    def get_column_count_in_range(
        self, column, min_val=None, max_val=None, strict_min=False, strict_max=True
    ):
        import inspect

        __frame = inspect.currentframe()
        __file = __frame.f_code.co_filename
        __func = __frame.f_code.co_name
        for (k, v) in __frame.f_locals.items():
            if any((var in k) for var in ("__frame", "__file", "__func")):
                continue
            print(f"<INTROSPECT> {__file}:{__func} - {k}:{v.__class__.__name__}")
        if (min_val is None) and (max_val is None):
            raise ValueError("Must specify either min or max value")
        if (min_val is not None) and (max_val is not None) and (min_val > max_val):
            raise ValueError("Min value must be <= to max value")
        result = self[column]
        if min_val is not None:
            if strict_min:
                result = result[(result > min_val)]
            else:
                result = result[(result >= min_val)]
        if max_val is not None:
            if strict_max:
                result = result[(result < max_val)]
            else:
                result = result[(result <= max_val)]
        return len(result)

    def get_crosstab(
        self, column_A, column_B, bins_A=None, bins_B=None, n_bins_A=None, n_bins_B=None
    ):
        import inspect

        __frame = inspect.currentframe()
        __file = __frame.f_code.co_filename
        __func = __frame.f_code.co_name
        for (k, v) in __frame.f_locals.items():
            if any((var in k) for var in ("__frame", "__file", "__func")):
                continue
            print(f"<INTROSPECT> {__file}:{__func} - {k}:{v.__class__.__name__}")
        "Get crosstab of column_A and column_B, binning values if necessary"
        series_A = self.get_binned_values(self[column_A], bins_A, n_bins_A)
        series_B = self.get_binned_values(self[column_B], bins_B, n_bins_B)
        return pd.crosstab(series_A, columns=series_B)

    def get_binned_values(self, series, bins, n_bins):
        import inspect

        __frame = inspect.currentframe()
        __file = __frame.f_code.co_filename
        __func = __frame.f_code.co_name
        for (k, v) in __frame.f_locals.items():
            if any((var in k) for var in ("__frame", "__file", "__func")):
                continue
            print(f"<INTROSPECT> {__file}:{__func} - {k}:{v.__class__.__name__}")
        "\n        Get binned values of series.\n\n        Args:\n            Series (pd.Series): Input series\n            bins (list):\n                Bins for the series. List of numeric if series is numeric or list of list\n                of series values else.\n            n_bins (int): Number of bins. Ignored if bins is not None.\n        "
        if n_bins is None:
            n_bins = 10
        if series.dtype in ["int", "float"]:
            if bins is not None:
                bins = sorted(np.unique(bins))
                if np.min(series) < bins[0]:
                    bins = [np.min(series)] + bins
                if np.max(series) > bins[(-1)]:
                    bins = bins + [np.max(series)]
            if bins is None:
                bins = np.histogram_bin_edges(series[series.notnull()], bins=n_bins)
            bins[(-1)] = np.nextafter(bins[(-1)], (bins[(-1)] + 1))
            precision = int(np.log10(min(bins[1:] - bins[:(-1)]))) + 2
            labels = [
                f"[{round(lower, precision)}, {round(upper, precision)})"
                for (lower, upper) in zip(bins[:(-1)], bins[1:])
            ]
            if any(np.isnan(series)):
                labels += ["(missing)"]
            return pd.Categorical.from_codes(
                codes=(np.digitize(series, bins=bins) - 1),
                categories=labels,
                ordered=True,
            )
        else:
            if bins is None:
                value_counts = series.value_counts(sort=True)
                if len(value_counts) < (n_bins + 1):
                    return series.fillna("(missing)")
                else:
                    other_values = sorted(value_counts.index[n_bins:])
                    replace = {value: "(other)" for value in other_values}
            else:
                replace = {}
                for x in bins:
                    replace.update({value: ", ".join(x) for value in x})
            return (
                series.replace(to_replace=replace)
                .fillna("(missing)")
                .astype("category")
            )

    @DocInherit
    @MetaPandasDataset.column_map_expectation
    def expect_column_values_to_be_unique(
        self,
        column,
        mostly=None,
        result_format=None,
        row_condition=None,
        condition_parser=None,
        include_config=True,
        catch_exceptions=None,
        meta=None,
    ):
        import inspect

        __frame = inspect.currentframe()
        __file = __frame.f_code.co_filename
        __func = __frame.f_code.co_name
        for (k, v) in __frame.f_locals.items():
            if any((var in k) for var in ("__frame", "__file", "__func")):
                continue
            print(f"<INTROSPECT> {__file}:{__func} - {k}:{v.__class__.__name__}")
        return ~column.duplicated(keep=False)

    @DocInherit
    @MetaPandasDataset.column_map_expectation
    def expect_column_values_to_not_be_null(
        self,
        column,
        mostly=None,
        result_format=None,
        row_condition=None,
        condition_parser=None,
        include_config=True,
        catch_exceptions=None,
        meta=None,
        include_nulls=True,
    ):
        import inspect

        __frame = inspect.currentframe()
        __file = __frame.f_code.co_filename
        __func = __frame.f_code.co_name
        for (k, v) in __frame.f_locals.items():
            if any((var in k) for var in ("__frame", "__file", "__func")):
                continue
            print(f"<INTROSPECT> {__file}:{__func} - {k}:{v.__class__.__name__}")
        return ~column.isnull()

    @DocInherit
    @MetaPandasDataset.column_map_expectation
    def expect_column_values_to_be_null(
        self,
        column,
        mostly=None,
        result_format=None,
        row_condition=None,
        condition_parser=None,
        include_config=True,
        catch_exceptions=None,
        meta=None,
    ):
        import inspect

        __frame = inspect.currentframe()
        __file = __frame.f_code.co_filename
        __func = __frame.f_code.co_name
        for (k, v) in __frame.f_locals.items():
            if any((var in k) for var in ("__frame", "__file", "__func")):
                continue
            print(f"<INTROSPECT> {__file}:{__func} - {k}:{v.__class__.__name__}")
        return column.isnull()

    @DocInherit
    def expect_column_values_to_be_of_type(self, column, type_, **kwargs):
        import inspect

        __frame = inspect.currentframe()
        __file = __frame.f_code.co_filename
        __func = __frame.f_code.co_name
        for (k, v) in __frame.f_locals.items():
            if any((var in k) for var in ("__frame", "__file", "__func")):
                continue
            print(f"<INTROSPECT> {__file}:{__func} - {k}:{v.__class__.__name__}")
        '\n        The pandas implementation of this expectation takes kwargs mostly, result_format, include_config,\n        catch_exceptions, and meta as other expectations, however it declares **kwargs because it needs to\n        be able to fork into either aggregate or map semantics depending on the column type (see below).\n\n        In Pandas, columns *may* be typed, or they may be of the generic "object" type which can include rows with\n        different storage types in the same column.\n\n        To respect that implementation, the expect_column_values_to_be_of_type expectations will first attempt to\n        use the column dtype information to determine whether the column is restricted to the provided type. If that\n        is possible, then expect_column_values_to_be_of_type will return aggregate information including an\n        observed_value, similarly to other backends.\n\n        If it is not possible (because the column dtype is "object" but a more specific type was specified), then\n        PandasDataset will use column map semantics: it will return map expectation results and\n        check each value individually, which can be substantially slower.\n\n        Unfortunately, the "object" type is also used to contain any string-type columns (including \'str\' and\n        numpy \'string_\' (bytes)); consequently, it is not possible to test for string columns using aggregate semantics.\n        '
        if (
            (self[column].dtype != "object")
            or (type_ is None)
            or (type_ in ["object", "object_", "O"])
        ):
            res = self._expect_column_values_to_be_of_type__aggregate(
                column, type_, **kwargs
            )
            if self._active_validation:
                return res
            existing_expectations = self._expectation_suite.find_expectation_indexes(
                ExpectationConfiguration(
                    expectation_type="expect_column_values_to_be_of_type",
                    kwargs={"column": column},
                )
            )
            if len(existing_expectations) == 1:
                self._expectation_suite.expectations.pop(existing_expectations[0])
            new_expectations = self._expectation_suite.find_expectation_indexes(
                ExpectationConfiguration(
                    expectation_type="_expect_column_values_to_be_of_type__aggregate",
                    kwargs={"column": column},
                )
            )
            assert len(new_expectations) == 1
            old_config = self._expectation_suite.expectations[new_expectations[0]]
            new_config = ExpectationConfiguration(
                expectation_type="expect_column_values_to_be_of_type",
                kwargs=old_config.kwargs,
                meta=old_config.meta,
                success_on_last_run=old_config.success_on_last_run,
            )
            self._expectation_suite.expectations[new_expectations[0]] = new_config
        else:
            res = self._expect_column_values_to_be_of_type__map(column, type_, **kwargs)
            if self._active_validation:
                return res
            existing_expectations = self._expectation_suite.find_expectation_indexes(
                ExpectationConfiguration(
                    expectation_type="expect_column_values_to_be_of_type",
                    kwargs={"column": column},
                )
            )
            if len(existing_expectations) == 1:
                self._expectation_suite.expectations.pop(existing_expectations[0])
            new_expectations = self._expectation_suite.find_expectation_indexes(
                ExpectationConfiguration(
                    expectation_type="_expect_column_values_to_be_of_type__map",
                    kwargs={"column": column},
                )
            )
            assert len(new_expectations) == 1
            old_config = self._expectation_suite.expectations[new_expectations[0]]
            new_config = ExpectationConfiguration(
                expectation_type="expect_column_values_to_be_of_type",
                kwargs=old_config.kwargs,
                meta=old_config.meta,
                success_on_last_run=old_config.success_on_last_run,
            )
            self._expectation_suite.expectations[new_expectations[0]] = new_config
        return res

    @DataAsset.expectation(["column", "type_", "mostly"])
    def _expect_column_values_to_be_of_type__aggregate(
        self,
        column,
        type_,
        mostly=None,
        result_format=None,
        row_condition=None,
        condition_parser=None,
        include_config=True,
        catch_exceptions=None,
        meta=None,
    ):
        import inspect

        __frame = inspect.currentframe()
        __file = __frame.f_code.co_filename
        __func = __frame.f_code.co_name
        for (k, v) in __frame.f_locals.items():
            if any((var in k) for var in ("__frame", "__file", "__func")):
                continue
            print(f"<INTROSPECT> {__file}:{__func} - {k}:{v.__class__.__name__}")
        if mostly is not None:
            raise ValueError(
                "PandasDataset cannot support mostly for a column with a non-object dtype."
            )
        if type_ is None:
            success = True
        else:
            comp_types = []
            try:
                comp_types.append(np.dtype(type_).type)
            except TypeError:
                try:
                    pd_type = getattr(pd, type_)
                    if isinstance(pd_type, type):
                        comp_types.append(pd_type)
                except AttributeError:
                    pass
                try:
                    pd_type = getattr(pd.core.dtypes.dtypes, type_)
                    if isinstance(pd_type, type):
                        comp_types.append(pd_type)
                except AttributeError:
                    pass
            native_type = self._native_type_type_map(type_)
            if native_type is not None:
                comp_types.extend(native_type)
            success = self[column].dtype.type in comp_types
        return {
            "success": success,
            "result": {"observed_value": self[column].dtype.type.__name__},
        }

    @staticmethod
    def _native_type_type_map(type_):
        import inspect

        __frame = inspect.currentframe()
        __file = __frame.f_code.co_filename
        __func = __frame.f_code.co_name
        for (k, v) in __frame.f_locals.items():
            if any((var in k) for var in ("__frame", "__file", "__func")):
                continue
            print(f"<INTROSPECT> {__file}:{__func} - {k}:{v.__class__.__name__}")
        if type_.lower() == "none":
            return (type(None),)
        elif type_.lower() == "bool":
            return (bool,)
        elif type_.lower() in ["int", "long"]:
            return (int,)
        elif type_.lower() == "float":
            return (float,)
        elif type_.lower() == "bytes":
            return (bytes,)
        elif type_.lower() == "complex":
            return (complex,)
        elif type_.lower() in ["str", "string_types"]:
            return (str,)
        elif type_.lower() == "list":
            return (list,)
        elif type_.lower() == "dict":
            return (dict,)
        elif type_.lower() == "unicode":
            return None

    @MetaPandasDataset.column_map_expectation
    def _expect_column_values_to_be_of_type__map(
        self,
        column,
        type_,
        mostly=None,
        result_format=None,
        row_condition=None,
        condition_parser=None,
        include_config=True,
        catch_exceptions=None,
        meta=None,
    ):
        import inspect

        __frame = inspect.currentframe()
        __file = __frame.f_code.co_filename
        __func = __frame.f_code.co_name
        for (k, v) in __frame.f_locals.items():
            if any((var in k) for var in ("__frame", "__file", "__func")):
                continue
            print(f"<INTROSPECT> {__file}:{__func} - {k}:{v.__class__.__name__}")
        comp_types = []
        try:
            comp_types.append(np.dtype(type_).type)
        except TypeError:
            try:
                pd_type = getattr(pd, type_)
                if isinstance(pd_type, type):
                    comp_types.append(pd_type)
            except AttributeError:
                pass
            try:
                pd_type = getattr(pd.core.dtypes.dtypes, type_)
                if isinstance(pd_type, type):
                    comp_types.append(pd_type)
            except AttributeError:
                pass
        native_type = self._native_type_type_map(type_)
        if native_type is not None:
            comp_types.extend(native_type)
        if len(comp_types) < 1:
            raise ValueError(f"Unrecognized numpy/python type: {type_}")
        return column.map(lambda x: isinstance(x, tuple(comp_types)))

    @DocInherit
    def expect_column_values_to_be_in_type_list(self, column, type_list, **kwargs):
        import inspect

        __frame = inspect.currentframe()
        __file = __frame.f_code.co_filename
        __func = __frame.f_code.co_name
        for (k, v) in __frame.f_locals.items():
            if any((var in k) for var in ("__frame", "__file", "__func")):
                continue
            print(f"<INTROSPECT> {__file}:{__func} - {k}:{v.__class__.__name__}")
        '\n        The pandas implementation of this expectation takes kwargs mostly, result_format, include_config,\n        catch_exceptions, and meta as other expectations, however it declares **kwargs because it needs to\n        be able to fork into either aggregate or map semantics depending on the column type (see below).\n\n        In Pandas, columns *may* be typed, or they may be of the generic "object" type which can include rows with\n        different storage types in the same column.\n\n        To respect that implementation, the expect_column_values_to_be_of_type expectations will first attempt to\n        use the column dtype information to determine whether the column is restricted to the provided type. If that\n        is possible, then expect_column_values_to_be_of_type will return aggregate information including an\n        observed_value, similarly to other backends.\n\n        If it is not possible (because the column dtype is "object" but a more specific type was specified), then\n        PandasDataset will use column map semantics: it will return map expectation results and\n        check each value individually, which can be substantially slower.\n\n        Unfortunately, the "object" type is also used to contain any string-type columns (including \'str\' and\n        numpy \'string_\' (bytes)); consequently, it is not possible to test for string columns using aggregate semantics.\n        '
        if (self[column].dtype != "object") or (type_list is None):
            res = self._expect_column_values_to_be_in_type_list__aggregate(
                column, type_list, **kwargs
            )
            if self._active_validation:
                return res
            existing_expectations = self._expectation_suite.find_expectation_indexes(
                ExpectationConfiguration(
                    expectation_type="expect_column_values_to_be_in_type_list",
                    kwargs={"column": column},
                )
            )
            if len(existing_expectations) == 1:
                self._expectation_suite.expectations.pop(existing_expectations[0])
            new_expectations = self._expectation_suite.find_expectation_indexes(
                ExpectationConfiguration(
                    expectation_type="_expect_column_values_to_be_in_type_list__aggregate",
                    kwargs={"column": column},
                )
            )
            assert len(new_expectations) == 1
            old_config = self._expectation_suite.expectations[new_expectations[0]]
            new_config = ExpectationConfiguration(
                expectation_type="expect_column_values_to_be_in_type_list",
                kwargs=old_config.kwargs,
                meta=old_config.meta,
                success_on_last_run=old_config.success_on_last_run,
            )
            self._expectation_suite.expectations[new_expectations[0]] = new_config
        else:
            res = self._expect_column_values_to_be_in_type_list__map(
                column, type_list, **kwargs
            )
            if self._active_validation:
                return res
            existing_expectations = self._expectation_suite.find_expectation_indexes(
                ExpectationConfiguration(
                    expectation_type="expect_column_values_to_be_in_type_list",
                    kwargs={"column": column},
                )
            )
            if len(existing_expectations) == 1:
                self._expectation_suite.expectations.pop(existing_expectations[0])
            new_expectations = self._expectation_suite.find_expectation_indexes(
                ExpectationConfiguration(
                    expectation_type="_expect_column_values_to_be_in_type_list__map",
                    kwargs={"column": column},
                )
            )
            assert len(new_expectations) == 1
            old_config = self._expectation_suite.expectations[new_expectations[0]]
            new_config = ExpectationConfiguration(
                expectation_type="expect_column_values_to_be_in_type_list",
                kwargs=old_config.kwargs,
                meta=old_config.meta,
                success_on_last_run=old_config.success_on_last_run,
            )
            self._expectation_suite.expectations[new_expectations[0]] = new_config
        return res

    @MetaPandasDataset.expectation(["column", "type_list", "mostly"])
    def _expect_column_values_to_be_in_type_list__aggregate(
        self,
        column,
        type_list,
        mostly=None,
        result_format=None,
        row_condition=None,
        condition_parser=None,
        include_config=True,
        catch_exceptions=None,
        meta=None,
    ):
        import inspect

        __frame = inspect.currentframe()
        __file = __frame.f_code.co_filename
        __func = __frame.f_code.co_name
        for (k, v) in __frame.f_locals.items():
            if any((var in k) for var in ("__frame", "__file", "__func")):
                continue
            print(f"<INTROSPECT> {__file}:{__func} - {k}:{v.__class__.__name__}")
        if mostly is not None:
            raise ValueError(
                "PandasDataset cannot support mostly for a column with a non-object dtype."
            )
        if type_list is None:
            success = True
        else:
            comp_types = []
            for type_ in type_list:
                try:
                    comp_types.append(np.dtype(type_).type)
                except TypeError:
                    try:
                        pd_type = getattr(pd, type_)
                        if isinstance(pd_type, type):
                            comp_types.append(pd_type)
                    except AttributeError:
                        pass
                    try:
                        pd_type = getattr(pd.core.dtypes.dtypes, type_)
                        if isinstance(pd_type, type):
                            comp_types.append(pd_type)
                    except AttributeError:
                        pass
                native_type = self._native_type_type_map(type_)
                if native_type is not None:
                    comp_types.extend(native_type)
            success = self[column].dtype.type in comp_types
        return {
            "success": success,
            "result": {"observed_value": self[column].dtype.type.__name__},
        }

    @MetaPandasDataset.column_map_expectation
    def _expect_column_values_to_be_in_type_list__map(
        self,
        column,
        type_list,
        mostly=None,
        result_format=None,
        row_condition=None,
        condition_parser=None,
        include_config=True,
        catch_exceptions=None,
        meta=None,
    ):
        import inspect

        __frame = inspect.currentframe()
        __file = __frame.f_code.co_filename
        __func = __frame.f_code.co_name
        for (k, v) in __frame.f_locals.items():
            if any((var in k) for var in ("__frame", "__file", "__func")):
                continue
            print(f"<INTROSPECT> {__file}:{__func} - {k}:{v.__class__.__name__}")
        comp_types = []
        for type_ in type_list:
            try:
                comp_types.append(np.dtype(type_).type)
            except TypeError:
                try:
                    pd_type = getattr(pd, type_)
                    if isinstance(pd_type, type):
                        comp_types.append(pd_type)
                except AttributeError:
                    pass
                try:
                    pd_type = getattr(pd.core.dtypes.dtypes, type_)
                    if isinstance(pd_type, type):
                        comp_types.append(pd_type)
                except AttributeError:
                    pass
            native_type = self._native_type_type_map(type_)
            if native_type is not None:
                comp_types.extend(native_type)
        if len(comp_types) < 1:
            raise ValueError(f"No recognized numpy/python type in list: {type_list}")
        return column.map(lambda x: isinstance(x, tuple(comp_types)))

    @DocInherit
    @MetaPandasDataset.column_map_expectation
    def expect_column_values_to_be_in_set(
        self,
        column,
        value_set,
        mostly=None,
        parse_strings_as_datetimes=None,
        result_format=None,
        row_condition=None,
        condition_parser=None,
        include_config=True,
        catch_exceptions=None,
        meta=None,
    ):
        import inspect

        __frame = inspect.currentframe()
        __file = __frame.f_code.co_filename
        __func = __frame.f_code.co_name
        for (k, v) in __frame.f_locals.items():
            if any((var in k) for var in ("__frame", "__file", "__func")):
                continue
            print(f"<INTROSPECT> {__file}:{__func} - {k}:{v.__class__.__name__}")
        if value_set is None:
            return np.ones(len(column), dtype=np.bool_)
        if parse_strings_as_datetimes:
            parsed_value_set = self._parse_value_set(value_set)
        else:
            parsed_value_set = value_set
        return column.isin(parsed_value_set)

    @DocInherit
    @MetaPandasDataset.column_map_expectation
    def expect_column_values_to_not_be_in_set(
        self,
        column,
        value_set,
        mostly=None,
        parse_strings_as_datetimes=None,
        result_format=None,
        row_condition=None,
        condition_parser=None,
        include_config=True,
        catch_exceptions=None,
        meta=None,
    ):
        import inspect

        __frame = inspect.currentframe()
        __file = __frame.f_code.co_filename
        __func = __frame.f_code.co_name
        for (k, v) in __frame.f_locals.items():
            if any((var in k) for var in ("__frame", "__file", "__func")):
                continue
            print(f"<INTROSPECT> {__file}:{__func} - {k}:{v.__class__.__name__}")
        if parse_strings_as_datetimes:
            parsed_value_set = self._parse_value_set(value_set)
        else:
            parsed_value_set = value_set
        return ~column.isin(parsed_value_set)

    @DocInherit
    @MetaPandasDataset.column_map_expectation
    def expect_column_values_to_be_between(
        self,
        column,
        min_value=None,
        max_value=None,
        strict_min=False,
        strict_max=False,
        parse_strings_as_datetimes=None,
        output_strftime_format=None,
        allow_cross_type_comparisons=None,
        mostly=None,
        row_condition=None,
        condition_parser=None,
        result_format=None,
        include_config=True,
        catch_exceptions=None,
        meta=None,
    ):
        import inspect

        __frame = inspect.currentframe()
        __file = __frame.f_code.co_filename
        __func = __frame.f_code.co_name
        for (k, v) in __frame.f_locals.items():
            if any((var in k) for var in ("__frame", "__file", "__func")):
                continue
            print(f"<INTROSPECT> {__file}:{__func} - {k}:{v.__class__.__name__}")
        if (min_value is None) and (max_value is None):
            raise ValueError("min_value and max_value cannot both be None")
        if parse_strings_as_datetimes:
            if min_value:
                min_value = parse(min_value)
            if max_value:
                max_value = parse(max_value)
            try:
                temp_column = column.map(parse)
            except TypeError:
                temp_column = column
        else:
            temp_column = column
        if (
            (min_value is not None)
            and (max_value is not None)
            and (min_value > max_value)
        ):
            raise ValueError("min_value cannot be greater than max_value")

        def comparator_factory(comparator, comparison_value):
            import inspect

            __frame = inspect.currentframe()
            __file = __frame.f_code.co_filename
            __func = __frame.f_code.co_name
            for (k, v) in __frame.f_locals.items():
                if any((var in k) for var in ("__frame", "__file", "__func")):
                    continue
                print(f"<INTROSPECT> {__file}:{__func} - {k}:{v.__class__.__name__}")

            def new_comparator(value):
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
                return comparator(value, comparison_value)

            def always_true(value):
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
                return True

            return always_true if (comparison_value is None) else new_comparator

        min_comparator = comparator_factory((gt if strict_min else ge), min_value)
        max_comparator = comparator_factory((lt if strict_max else le), max_value)

        def cross_type_comparator(val):
            import inspect

            __frame = inspect.currentframe()
            __file = __frame.f_code.co_filename
            __func = __frame.f_code.co_name
            for (k, v) in __frame.f_locals.items():
                if any((var in k) for var in ("__frame", "__file", "__func")):
                    continue
                print(f"<INTROSPECT> {__file}:{__func} - {k}:{v.__class__.__name__}")
            try:
                return min_comparator(val) & max_comparator(val)
            except TypeError:
                return False

        try:
            return min_comparator(temp_column) & max_comparator(temp_column)
        except TypeError:
            if allow_cross_type_comparisons:
                return pd.Series(cross_type_comparator(val) for val in temp_column)
            raise TypeError(
                "Column values, min_value, and max_value must either be None or of the same type."
            )

    @DocInherit
    @MetaPandasDataset.column_map_expectation
    def expect_column_values_to_be_increasing(
        self,
        column,
        strictly=None,
        parse_strings_as_datetimes=None,
        output_strftime_format=None,
        mostly=None,
        row_condition=None,
        condition_parser=None,
        result_format=None,
        include_config=True,
        catch_exceptions=None,
        meta=None,
    ):
        import inspect

        __frame = inspect.currentframe()
        __file = __frame.f_code.co_filename
        __func = __frame.f_code.co_name
        for (k, v) in __frame.f_locals.items():
            if any((var in k) for var in ("__frame", "__file", "__func")):
                continue
            print(f"<INTROSPECT> {__file}:{__func} - {k}:{v.__class__.__name__}")
        if parse_strings_as_datetimes:
            temp_column = column.map(parse)
            col_diff = temp_column.diff()
            col_diff[0] = pd.Timedelta(1)
            if strictly:
                return col_diff > pd.Timedelta(0)
            else:
                return col_diff >= pd.Timedelta(0)
        else:
            col_diff = column.diff()
            col_diff[col_diff.isnull()] = 1
            if strictly:
                return col_diff > 0
            else:
                return col_diff >= 0

    @DocInherit
    @MetaPandasDataset.column_map_expectation
    def expect_column_values_to_be_decreasing(
        self,
        column,
        strictly=None,
        parse_strings_as_datetimes=None,
        output_strftime_format=None,
        mostly=None,
        row_condition=None,
        condition_parser=None,
        result_format=None,
        include_config=True,
        catch_exceptions=None,
        meta=None,
    ):
        import inspect

        __frame = inspect.currentframe()
        __file = __frame.f_code.co_filename
        __func = __frame.f_code.co_name
        for (k, v) in __frame.f_locals.items():
            if any((var in k) for var in ("__frame", "__file", "__func")):
                continue
            print(f"<INTROSPECT> {__file}:{__func} - {k}:{v.__class__.__name__}")
        if parse_strings_as_datetimes:
            temp_column = column.map(parse)
            col_diff = temp_column.diff()
            col_diff[0] = pd.Timedelta(-1)
            if strictly:
                return col_diff < pd.Timedelta(0)
            else:
                return col_diff <= pd.Timedelta(0)
        else:
            col_diff = column.diff()
            col_diff[col_diff.isnull()] = -1
            if strictly:
                return col_diff < 0
            else:
                return col_diff <= 0

    @DocInherit
    @MetaPandasDataset.column_map_expectation
    def expect_column_value_lengths_to_be_between(
        self,
        column,
        min_value=None,
        max_value=None,
        mostly=None,
        row_condition=None,
        condition_parser=None,
        result_format=None,
        include_config=True,
        catch_exceptions=None,
        meta=None,
    ):
        import inspect

        __frame = inspect.currentframe()
        __file = __frame.f_code.co_filename
        __func = __frame.f_code.co_name
        for (k, v) in __frame.f_locals.items():
            if any((var in k) for var in ("__frame", "__file", "__func")):
                continue
            print(f"<INTROSPECT> {__file}:{__func} - {k}:{v.__class__.__name__}")
        if (min_value is None) and (max_value is None):
            raise ValueError("min_value and max_value cannot both be None")
        try:
            if (min_value is not None) and (not float(min_value).is_integer()):
                raise ValueError("min_value and max_value must be integers")
            if (max_value is not None) and (not float(max_value).is_integer()):
                raise ValueError("min_value and max_value must be integers")
        except ValueError:
            raise ValueError("min_value and max_value must be integers")
        column_lengths = column.astype(str).str.len()
        if (min_value is not None) and (max_value is not None):
            return column_lengths.between(min_value, max_value)
        elif (min_value is None) and (max_value is not None):
            return column_lengths <= max_value
        elif (min_value is not None) and (max_value is None):
            return column_lengths >= min_value
        else:
            return False

    @DocInherit
    @MetaPandasDataset.column_map_expectation
    def expect_column_value_lengths_to_equal(
        self,
        column,
        value,
        mostly=None,
        result_format=None,
        row_condition=None,
        condition_parser=None,
        include_config=True,
        catch_exceptions=None,
        meta=None,
    ):
        import inspect

        __frame = inspect.currentframe()
        __file = __frame.f_code.co_filename
        __func = __frame.f_code.co_name
        for (k, v) in __frame.f_locals.items():
            if any((var in k) for var in ("__frame", "__file", "__func")):
                continue
            print(f"<INTROSPECT> {__file}:{__func} - {k}:{v.__class__.__name__}")
        return column.str.len() == value

    @DocInherit
    @MetaPandasDataset.column_map_expectation
    def expect_column_values_to_match_regex(
        self,
        column,
        regex,
        mostly=None,
        result_format=None,
        row_condition=None,
        condition_parser=None,
        include_config=True,
        catch_exceptions=None,
        meta=None,
    ):
        import inspect

        __frame = inspect.currentframe()
        __file = __frame.f_code.co_filename
        __func = __frame.f_code.co_name
        for (k, v) in __frame.f_locals.items():
            if any((var in k) for var in ("__frame", "__file", "__func")):
                continue
            print(f"<INTROSPECT> {__file}:{__func} - {k}:{v.__class__.__name__}")
        return column.astype(str).str.contains(regex)

    @DocInherit
    @MetaPandasDataset.column_map_expectation
    def expect_column_values_to_not_match_regex(
        self,
        column,
        regex,
        mostly=None,
        result_format=None,
        row_condition=None,
        condition_parser=None,
        include_config=True,
        catch_exceptions=None,
        meta=None,
    ):
        import inspect

        __frame = inspect.currentframe()
        __file = __frame.f_code.co_filename
        __func = __frame.f_code.co_name
        for (k, v) in __frame.f_locals.items():
            if any((var in k) for var in ("__frame", "__file", "__func")):
                continue
            print(f"<INTROSPECT> {__file}:{__func} - {k}:{v.__class__.__name__}")
        return ~column.astype(str).str.contains(regex)

    @DocInherit
    @MetaPandasDataset.column_map_expectation
    def expect_column_values_to_match_regex_list(
        self,
        column,
        regex_list,
        match_on="any",
        mostly=None,
        result_format=None,
        row_condition=None,
        condition_parser=None,
        include_config=True,
        catch_exceptions=None,
        meta=None,
    ):
        import inspect

        __frame = inspect.currentframe()
        __file = __frame.f_code.co_filename
        __func = __frame.f_code.co_name
        for (k, v) in __frame.f_locals.items():
            if any((var in k) for var in ("__frame", "__file", "__func")):
                continue
            print(f"<INTROSPECT> {__file}:{__func} - {k}:{v.__class__.__name__}")
        regex_matches = []
        for regex in regex_list:
            regex_matches.append(column.astype(str).str.contains(regex))
        regex_match_df = pd.concat(regex_matches, axis=1, ignore_index=True)
        if match_on == "any":
            return regex_match_df.any(axis="columns")
        elif match_on == "all":
            return regex_match_df.all(axis="columns")
        else:
            raise ValueError("match_on must be either 'any' or 'all'")

    @DocInherit
    @MetaPandasDataset.column_map_expectation
    def expect_column_values_to_not_match_regex_list(
        self,
        column,
        regex_list,
        mostly=None,
        result_format=None,
        row_condition=None,
        condition_parser=None,
        include_config=True,
        catch_exceptions=None,
        meta=None,
    ):
        import inspect

        __frame = inspect.currentframe()
        __file = __frame.f_code.co_filename
        __func = __frame.f_code.co_name
        for (k, v) in __frame.f_locals.items():
            if any((var in k) for var in ("__frame", "__file", "__func")):
                continue
            print(f"<INTROSPECT> {__file}:{__func} - {k}:{v.__class__.__name__}")
        regex_matches = []
        for regex in regex_list:
            regex_matches.append(column.astype(str).str.contains(regex))
        regex_match_df = pd.concat(regex_matches, axis=1, ignore_index=True)
        return ~regex_match_df.any(axis="columns")

    @DocInherit
    @MetaPandasDataset.column_map_expectation
    def expect_column_values_to_match_strftime_format(
        self,
        column,
        strftime_format,
        mostly=None,
        result_format=None,
        row_condition=None,
        condition_parser=None,
        include_config=True,
        catch_exceptions=None,
        meta=None,
    ):
        import inspect

        __frame = inspect.currentframe()
        __file = __frame.f_code.co_filename
        __func = __frame.f_code.co_name
        for (k, v) in __frame.f_locals.items():
            if any((var in k) for var in ("__frame", "__file", "__func")):
                continue
            print(f"<INTROSPECT> {__file}:{__func} - {k}:{v.__class__.__name__}")
        try:
            datetime.strptime(
                datetime.strftime(datetime.now(), strftime_format), strftime_format
            )
        except ValueError as e:
            raise ValueError(f"Unable to use provided strftime_format. {str(e)}")

        def is_parseable_by_format(val):
            import inspect

            __frame = inspect.currentframe()
            __file = __frame.f_code.co_filename
            __func = __frame.f_code.co_name
            for (k, v) in __frame.f_locals.items():
                if any((var in k) for var in ("__frame", "__file", "__func")):
                    continue
                print(f"<INTROSPECT> {__file}:{__func} - {k}:{v.__class__.__name__}")
            try:
                datetime.strptime(val, strftime_format)
                return True
            except TypeError:
                raise TypeError(
                    "Values passed to expect_column_values_to_match_strftime_format must be of type string.\nIf you want to validate a column of dates or timestamps, please call the expectation before converting from string format."
                )
            except ValueError:
                return False

        return column.map(is_parseable_by_format)

    @DocInherit
    @MetaPandasDataset.column_map_expectation
    def expect_column_values_to_be_dateutil_parseable(
        self,
        column,
        mostly=None,
        result_format=None,
        row_condition=None,
        condition_parser=None,
        include_config=True,
        catch_exceptions=None,
        meta=None,
    ):
        import inspect

        __frame = inspect.currentframe()
        __file = __frame.f_code.co_filename
        __func = __frame.f_code.co_name
        for (k, v) in __frame.f_locals.items():
            if any((var in k) for var in ("__frame", "__file", "__func")):
                continue
            print(f"<INTROSPECT> {__file}:{__func} - {k}:{v.__class__.__name__}")

        def is_parseable(val):
            import inspect

            __frame = inspect.currentframe()
            __file = __frame.f_code.co_filename
            __func = __frame.f_code.co_name
            for (k, v) in __frame.f_locals.items():
                if any((var in k) for var in ("__frame", "__file", "__func")):
                    continue
                print(f"<INTROSPECT> {__file}:{__func} - {k}:{v.__class__.__name__}")
            try:
                if type(val) != str:
                    raise TypeError(
                        "Values passed to expect_column_values_to_be_dateutil_parseable must be of type string.\nIf you want to validate a column of dates or timestamps, please call the expectation before converting from string format."
                    )
                parse(val)
                return True
            except (ValueError, OverflowError):
                return False

        return column.map(is_parseable)

    @DocInherit
    @MetaPandasDataset.column_map_expectation
    def expect_column_values_to_be_json_parseable(
        self,
        column,
        mostly=None,
        result_format=None,
        row_condition=None,
        condition_parser=None,
        include_config=True,
        catch_exceptions=None,
        meta=None,
    ):
        import inspect

        __frame = inspect.currentframe()
        __file = __frame.f_code.co_filename
        __func = __frame.f_code.co_name
        for (k, v) in __frame.f_locals.items():
            if any((var in k) for var in ("__frame", "__file", "__func")):
                continue
            print(f"<INTROSPECT> {__file}:{__func} - {k}:{v.__class__.__name__}")

        def is_json(val):
            import inspect

            __frame = inspect.currentframe()
            __file = __frame.f_code.co_filename
            __func = __frame.f_code.co_name
            for (k, v) in __frame.f_locals.items():
                if any((var in k) for var in ("__frame", "__file", "__func")):
                    continue
                print(f"<INTROSPECT> {__file}:{__func} - {k}:{v.__class__.__name__}")
            try:
                json.loads(val)
                return True
            except:
                return False

        return column.map(is_json)

    @DocInherit
    @MetaPandasDataset.column_map_expectation
    def expect_column_values_to_match_json_schema(
        self,
        column,
        json_schema,
        mostly=None,
        result_format=None,
        row_condition=None,
        condition_parser=None,
        include_config=True,
        catch_exceptions=None,
        meta=None,
    ):
        import inspect

        __frame = inspect.currentframe()
        __file = __frame.f_code.co_filename
        __func = __frame.f_code.co_name
        for (k, v) in __frame.f_locals.items():
            if any((var in k) for var in ("__frame", "__file", "__func")):
                continue
            print(f"<INTROSPECT> {__file}:{__func} - {k}:{v.__class__.__name__}")

        def matches_json_schema(val):
            import inspect

            __frame = inspect.currentframe()
            __file = __frame.f_code.co_filename
            __func = __frame.f_code.co_name
            for (k, v) in __frame.f_locals.items():
                if any((var in k) for var in ("__frame", "__file", "__func")):
                    continue
                print(f"<INTROSPECT> {__file}:{__func} - {k}:{v.__class__.__name__}")
            try:
                val_json = json.loads(val)
                jsonschema.validate(val_json, json_schema)
                return True
            except jsonschema.ValidationError:
                return False
            except jsonschema.SchemaError:
                raise
            except:
                raise

        return column.map(matches_json_schema)

    @DocInherit
    @MetaPandasDataset.column_aggregate_expectation
    def expect_column_parameterized_distribution_ks_test_p_value_to_be_greater_than(
        self,
        column,
        distribution,
        p_value=0.05,
        params=None,
        result_format=None,
        row_condition=None,
        condition_parser=None,
        include_config=True,
        catch_exceptions=None,
        meta=None,
    ):
        import inspect

        __frame = inspect.currentframe()
        __file = __frame.f_code.co_filename
        __func = __frame.f_code.co_name
        for (k, v) in __frame.f_locals.items():
            if any((var in k) for var in ("__frame", "__file", "__func")):
                continue
            print(f"<INTROSPECT> {__file}:{__func} - {k}:{v.__class__.__name__}")
        column = self[column]
        if (p_value <= 0) or (p_value >= 1):
            raise ValueError("p_value must be between 0 and 1 exclusive")
        try:
            validate_distribution_parameters(distribution=distribution, params=params)
        except ValueError as e:
            raise e
        if isinstance(params, dict):
            positional_parameters = _scipy_distribution_positional_args_from_dict(
                distribution, params
            )
        else:
            positional_parameters = params
        ks_result = stats.kstest(column, distribution, args=positional_parameters)
        return {
            "success": (ks_result[1] >= p_value),
            "result": {
                "observed_value": ks_result[1],
                "details": {
                    "expected_params": positional_parameters,
                    "observed_ks_result": ks_result,
                },
            },
        }

    @DocInherit
    @MetaPandasDataset.column_aggregate_expectation
    def expect_column_bootstrapped_ks_test_p_value_to_be_greater_than(
        self,
        column,
        partition_object=None,
        p=0.05,
        bootstrap_samples=None,
        bootstrap_sample_size=None,
        result_format=None,
        row_condition=None,
        condition_parser=None,
        include_config=True,
        catch_exceptions=None,
        meta=None,
    ):
        import inspect

        __frame = inspect.currentframe()
        __file = __frame.f_code.co_filename
        __func = __frame.f_code.co_name
        for (k, v) in __frame.f_locals.items():
            if any((var in k) for var in ("__frame", "__file", "__func")):
                continue
            print(f"<INTROSPECT> {__file}:{__func} - {k}:{v.__class__.__name__}")
        column = self[column]
        if not is_valid_continuous_partition_object(partition_object):
            raise ValueError("Invalid continuous partition object.")
        if (partition_object["bins"][0] == (-np.inf)) or (
            partition_object["bins"][(-1)] == np.inf
        ):
            raise ValueError("Partition endpoints must be finite.")
        if ("tail_weights" in partition_object) and (
            np.sum(partition_object["tail_weights"]) > 0
        ):
            raise ValueError(
                "Partition cannot have tail weights -- endpoints must be finite."
            )
        test_cdf = np.append(np.array([0]), np.cumsum(partition_object["weights"]))

        def estimated_cdf(x):
            import inspect

            __frame = inspect.currentframe()
            __file = __frame.f_code.co_filename
            __func = __frame.f_code.co_name
            for (k, v) in __frame.f_locals.items():
                if any((var in k) for var in ("__frame", "__file", "__func")):
                    continue
                print(f"<INTROSPECT> {__file}:{__func} - {k}:{v.__class__.__name__}")
            return np.interp(x, partition_object["bins"], test_cdf)

        if bootstrap_samples is None:
            bootstrap_samples = 1000
        if bootstrap_sample_size is None:
            bootstrap_sample_size = len(partition_object["weights"]) * 2
        results = [
            stats.kstest(
                np.random.choice(column, size=bootstrap_sample_size), estimated_cdf
            )[1]
            for _ in range(bootstrap_samples)
        ]
        test_result = (1 + sum((x >= p) for x in results)) / (bootstrap_samples + 1)
        (hist, bin_edges) = np.histogram(column, partition_object["bins"])
        below_partition = len(np.where(column < partition_object["bins"][0])[0])
        above_partition = len(np.where(column > partition_object["bins"][(-1)])[0])
        if (below_partition > 0) and (above_partition > 0):
            observed_bins = ([np.min(column)] + partition_object["bins"]) + [
                np.max(column)
            ]
            observed_weights = np.concatenate(
                ([below_partition], hist, [above_partition])
            ) / len(column)
        elif below_partition > 0:
            observed_bins = [np.min(column)] + partition_object["bins"]
            observed_weights = np.concatenate(([below_partition], hist)) / len(column)
        elif above_partition > 0:
            observed_bins = partition_object["bins"] + [np.max(column)]
            observed_weights = np.concatenate((hist, [above_partition])) / len(column)
        else:
            observed_bins = partition_object["bins"]
            observed_weights = hist / len(column)
        observed_cdf_values = np.cumsum(observed_weights)
        return_obj = {
            "success": (test_result > p),
            "result": {
                "observed_value": test_result,
                "details": {
                    "bootstrap_samples": bootstrap_samples,
                    "bootstrap_sample_size": bootstrap_sample_size,
                    "observed_partition": {
                        "bins": observed_bins,
                        "weights": observed_weights.tolist(),
                    },
                    "expected_partition": {
                        "bins": partition_object["bins"],
                        "weights": partition_object["weights"],
                    },
                    "observed_cdf": {
                        "x": observed_bins,
                        "cdf_values": ([0] + observed_cdf_values.tolist()),
                    },
                    "expected_cdf": {
                        "x": partition_object["bins"],
                        "cdf_values": test_cdf.tolist(),
                    },
                },
            },
        }
        return return_obj

    @DocInherit
    @MetaPandasDataset.column_pair_map_expectation
    def expect_column_pair_values_to_be_equal(
        self,
        column_A,
        column_B,
        ignore_row_if="both_values_are_missing",
        result_format=None,
        row_condition=None,
        condition_parser=None,
        include_config=True,
        catch_exceptions=None,
        meta=None,
    ):
        import inspect

        __frame = inspect.currentframe()
        __file = __frame.f_code.co_filename
        __func = __frame.f_code.co_name
        for (k, v) in __frame.f_locals.items():
            if any((var in k) for var in ("__frame", "__file", "__func")):
                continue
            print(f"<INTROSPECT> {__file}:{__func} - {k}:{v.__class__.__name__}")
        return column_A == column_B

    @DocInherit
    @MetaPandasDataset.column_pair_map_expectation
    def expect_column_pair_values_A_to_be_greater_than_B(
        self,
        column_A,
        column_B,
        or_equal=None,
        parse_strings_as_datetimes=None,
        allow_cross_type_comparisons=None,
        ignore_row_if="both_values_are_missing",
        result_format=None,
        row_condition=None,
        condition_parser=None,
        include_config=True,
        catch_exceptions=None,
        meta=None,
    ):
        import inspect

        __frame = inspect.currentframe()
        __file = __frame.f_code.co_filename
        __func = __frame.f_code.co_name
        for (k, v) in __frame.f_locals.items():
            if any((var in k) for var in ("__frame", "__file", "__func")):
                continue
            print(f"<INTROSPECT> {__file}:{__func} - {k}:{v.__class__.__name__}")
        if allow_cross_type_comparisons == True:
            raise NotImplementedError
        if parse_strings_as_datetimes:
            temp_column_A = column_A.map(parse)
            temp_column_B = column_B.map(parse)
        else:
            temp_column_A = column_A
            temp_column_B = column_B
        if or_equal == True:
            return temp_column_A >= temp_column_B
        else:
            return temp_column_A > temp_column_B

    @DocInherit
    @MetaPandasDataset.column_pair_map_expectation
    def expect_column_pair_values_to_be_in_set(
        self,
        column_A,
        column_B,
        value_pairs_set,
        ignore_row_if="both_values_are_missing",
        result_format=None,
        row_condition=None,
        condition_parser=None,
        include_config=True,
        catch_exceptions=None,
        meta=None,
    ):
        import inspect

        __frame = inspect.currentframe()
        __file = __frame.f_code.co_filename
        __func = __frame.f_code.co_name
        for (k, v) in __frame.f_locals.items():
            if any((var in k) for var in ("__frame", "__file", "__func")):
                continue
            print(f"<INTROSPECT> {__file}:{__func} - {k}:{v.__class__.__name__}")
        if value_pairs_set is None:
            return np.ones(len(column_A), dtype=np.bool_)
        temp_df = pd.DataFrame({"A": column_A, "B": column_B})
        value_pairs_set = {(x, y) for (x, y) in value_pairs_set}
        results = []
        for (i, t) in temp_df.iterrows():
            if pd.isnull(t["A"]):
                a = None
            else:
                a = t["A"]
            if pd.isnull(t["B"]):
                b = None
            else:
                b = t["B"]
            results.append((a, b) in value_pairs_set)
        return pd.Series(results, temp_df.index)

    def expect_multicolumn_values_to_be_unique(
        self,
        column_list,
        mostly=None,
        ignore_row_if="all_values_are_missing",
        result_format=None,
        include_config=True,
        catch_exceptions=None,
        meta=None,
    ):
        import inspect

        __frame = inspect.currentframe()
        __file = __frame.f_code.co_filename
        __func = __frame.f_code.co_name
        for (k, v) in __frame.f_locals.items():
            if any((var in k) for var in ("__frame", "__file", "__func")):
                continue
            print(f"<INTROSPECT> {__file}:{__func} - {k}:{v.__class__.__name__}")
        deprecation_warning = "expect_multicolumn_values_to_be_unique is deprecated as of v0.13.4 and will be removed in v0.16. Please use expect_select_column_values_to_be_unique_within_record instead."
        warnings.warn(deprecation_warning, DeprecationWarning)
        return self.expect_select_column_values_to_be_unique_within_record(
            column_list=column_list,
            mostly=mostly,
            ignore_row_if=ignore_row_if,
            result_format=result_format,
            include_config=include_config,
            catch_exceptions=catch_exceptions,
            meta=meta,
        )

    @DocInherit
    @MetaPandasDataset.multicolumn_map_expectation
    def expect_select_column_values_to_be_unique_within_record(
        self,
        column_list,
        mostly=None,
        ignore_row_if="all_values_are_missing",
        result_format=None,
        include_config=True,
        catch_exceptions=None,
        meta=None,
    ):
        import inspect

        __frame = inspect.currentframe()
        __file = __frame.f_code.co_filename
        __func = __frame.f_code.co_name
        for (k, v) in __frame.f_locals.items():
            if any((var in k) for var in ("__frame", "__file", "__func")):
                continue
            print(f"<INTROSPECT> {__file}:{__func} - {k}:{v.__class__.__name__}")
        threshold = len(column_list.columns)
        return column_list.nunique(dropna=False, axis=1) >= threshold

    @DocInherit
    @MetaPandasDataset.multicolumn_map_expectation
    def expect_multicolumn_sum_to_equal(
        self,
        column_list,
        sum_total,
        result_format=None,
        include_config=True,
        catch_exceptions=None,
        meta=None,
    ):
        import inspect

        __frame = inspect.currentframe()
        __file = __frame.f_code.co_filename
        __func = __frame.f_code.co_name
        for (k, v) in __frame.f_locals.items():
            if any((var in k) for var in ("__frame", "__file", "__func")):
                continue
            print(f"<INTROSPECT> {__file}:{__func} - {k}:{v.__class__.__name__}")
        " Multi-Column Map Expectation\n\n        Expects that the sum of row values is the same for each row, summing only values in columns specified in\n        column_list, and equal to the specific value, sum_total.\n\n        Args:\n            column_list (List[str]):                 Set of columns to be checked\n            sum_total (int):                 expected sum of columns\n        "
        return column_list.sum(axis=1) == sum_total

    @DocInherit
    @MetaPandasDataset.multicolumn_map_expectation
    def expect_compound_columns_to_be_unique(
        self,
        column_list,
        mostly=None,
        ignore_row_if="all_values_are_missing",
        result_format=None,
        include_config=True,
        catch_exceptions=None,
        meta=None,
    ):
        import inspect

        __frame = inspect.currentframe()
        __file = __frame.f_code.co_filename
        __func = __frame.f_code.co_name
        for (k, v) in __frame.f_locals.items():
            if any((var in k) for var in ("__frame", "__file", "__func")):
                continue
            print(f"<INTROSPECT> {__file}:{__func} - {k}:{v.__class__.__name__}")
        return ~column_list.duplicated(keep=False)
