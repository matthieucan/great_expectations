import datetime
import hashlib
import logging
import pickle
import random
import warnings
from functools import partial
from io import BytesIO
from typing import Any, Callable, Iterable, Optional, Tuple, Union

import pandas as pd

import great_expectations.exceptions as ge_exceptions
from great_expectations.core.batch import BatchMarkers
from great_expectations.core.batch_spec import (
    AzureBatchSpec,
    BatchSpec,
    GCSBatchSpec,
    PathBatchSpec,
    RuntimeDataBatchSpec,
    S3BatchSpec,
)
from great_expectations.core.util import AzureUrl, GCSUrl, S3Url, sniff_s3_compression
from great_expectations.execution_engine import ExecutionEngine
from great_expectations.execution_engine.execution_engine import MetricDomainTypes
from great_expectations.execution_engine.pandas_batch_data import PandasBatchData
from great_expectations.execution_engine.split_and_sample.pandas_data_splitter import (
    PandasDataSplitter,
)

logger = logging.getLogger(__name__)
try:
    import boto3
    from botocore.exceptions import ClientError, ParamValidationError
except ImportError:
    boto3 = None
    ClientError = None
    ParamValidationError = None
    logger.debug(
        "Unable to load AWS connection object; install optional boto3 dependency for support"
    )
try:
    from azure.storage.blob import BlobServiceClient
except ImportError:
    BlobServiceClient = None
    logger.debug(
        "Unable to load Azure connection object; install optional azure dependency for support"
    )
try:
    from google.api_core.exceptions import GoogleAPIError
    from google.auth.exceptions import DefaultCredentialsError
    from google.cloud import storage
    from google.oauth2 import service_account
except ImportError:
    storage = None
    service_account = None
    DefaultCredentialsError = None
    logger.debug(
        "Unable to load GCS connection object; install optional google dependency for support"
    )
HASH_THRESHOLD = 1000000000.0


class PandasExecutionEngine(ExecutionEngine):
    "\nPandasExecutionEngine instantiates the great_expectations Expectations API as a subclass of a pandas.DataFrame.\n\nFor the full API reference, please see :func:`Dataset <great_expectations.data_asset.dataset.Dataset>`\n\nNotes:\n    1. Samples and Subsets of PandaDataSet have ALL the expectations of the original        data frame unless the user specifies the ``discard_subset_failing_expectations = True``        property on the original data frame.\n    2. Concatenations, joins, and merges of PandaDataSets contain NO expectations (since no autoinspection\n       is performed by default).\n\n--ge-feature-maturity-info--\n\n    id: validation_engine_pandas\n    title: Validation Engine - Pandas\n    icon:\n    short_description: Use Pandas DataFrame to validate data\n    description: Use Pandas DataFrame to validate data\n    how_to_guide_url:\n    maturity: Production\n    maturity_details:\n        api_stability: Stable\n        implementation_completeness: Complete\n        unit_test_coverage: Complete\n        integration_infrastructure_test_coverage: N/A -> see relevant Datasource evaluation\n        documentation_completeness: Complete\n        bug_risk: Low\n        expectation_completeness: Complete\n\n--ge-feature-maturity-info--\n"
    recognized_batch_spec_defaults = {"reader_method", "reader_options"}

    def __init__(self, *args, **kwargs) -> None:
        import inspect

        __frame = inspect.currentframe()
        __file = __frame.f_code.co_filename
        __func = __frame.f_code.co_name
        for (k, v) in __frame.f_locals.items():
            if any((var in k) for var in ("__frame", "__file", "__func")):
                continue
            print(f"<INTROSPECT> {__file}:{__func} - {k}:{v.__class__.__name__}")
        self.discard_subset_failing_expectations = kwargs.pop(
            "discard_subset_failing_expectations", False
        )
        boto3_options: dict = kwargs.pop("boto3_options", {})
        azure_options: dict = kwargs.pop("azure_options", {})
        gcs_options: dict = kwargs.pop("gcs_options", {})
        self._s3 = None
        self._azure = None
        self._gcs = None
        super().__init__(*args, **kwargs)
        self._config.update(
            {
                "discard_subset_failing_expectations": self.discard_subset_failing_expectations,
                "boto3_options": boto3_options,
                "azure_options": azure_options,
                "gcs_options": gcs_options,
            }
        )
        self._data_splitter = PandasDataSplitter()

    def _instantiate_azure_client(self) -> None:
        import inspect

        __frame = inspect.currentframe()
        __file = __frame.f_code.co_filename
        __func = __frame.f_code.co_name
        for (k, v) in __frame.f_locals.items():
            if any((var in k) for var in ("__frame", "__file", "__func")):
                continue
            print(f"<INTROSPECT> {__file}:{__func} - {k}:{v.__class__.__name__}")
        azure_options = self.config.get("azure_options", {})
        try:
            if "conn_str" in azure_options:
                self._azure = BlobServiceClient.from_connection_string(**azure_options)
            else:
                self._azure = BlobServiceClient(**azure_options)
        except (TypeError, AttributeError):
            self._azure = None

    def _instantiate_s3_client(self) -> None:
        import inspect

        __frame = inspect.currentframe()
        __file = __frame.f_code.co_filename
        __func = __frame.f_code.co_name
        for (k, v) in __frame.f_locals.items():
            if any((var in k) for var in ("__frame", "__file", "__func")):
                continue
            print(f"<INTROSPECT> {__file}:{__func} - {k}:{v.__class__.__name__}")
        boto3_options = self.config.get("boto3_options", {})
        try:
            self._s3 = boto3.client("s3", **boto3_options)
        except (TypeError, AttributeError):
            self._s3 = None

    def _instantiate_gcs_client(self) -> None:
        import inspect

        __frame = inspect.currentframe()
        __file = __frame.f_code.co_filename
        __func = __frame.f_code.co_name
        for (k, v) in __frame.f_locals.items():
            if any((var in k) for var in ("__frame", "__file", "__func")):
                continue
            print(f"<INTROSPECT> {__file}:{__func} - {k}:{v.__class__.__name__}")
        "\n        Helper method for instantiating GCS client when GCSBatchSpec is passed in.\n\n        The method accounts for 3 ways that a GCS connection can be configured:\n            1. setting an environment variable, which is typically GOOGLE_APPLICATION_CREDENTIALS\n            2. passing in explicit credentials via gcs_options\n            3. running Great Expectations from within a GCP container, at which you would be able to create a Client\n                without passing in an additional environment variable or explicit credentials\n        "
        gcs_options = self.config.get("gcs_options", {})
        try:
            credentials = None
            if "filename" in gcs_options:
                filename = gcs_options.pop("filename")
                credentials = service_account.Credentials.from_service_account_file(
                    filename=filename
                )
            elif "info" in gcs_options:
                info = gcs_options.pop("info")
                credentials = service_account.Credentials.from_service_account_info(
                    info=info
                )
            self._gcs = storage.Client(credentials=credentials, **gcs_options)
        except (TypeError, AttributeError, DefaultCredentialsError):
            self._gcs = None

    def configure_validator(self, validator) -> None:
        import inspect

        __frame = inspect.currentframe()
        __file = __frame.f_code.co_filename
        __func = __frame.f_code.co_name
        for (k, v) in __frame.f_locals.items():
            if any((var in k) for var in ("__frame", "__file", "__func")):
                continue
            print(f"<INTROSPECT> {__file}:{__func} - {k}:{v.__class__.__name__}")
        super().configure_validator(validator)
        validator.expose_dataframe_methods = True

    def load_batch_data(self, batch_id: str, batch_data: Any) -> None:
        import inspect

        __frame = inspect.currentframe()
        __file = __frame.f_code.co_filename
        __func = __frame.f_code.co_name
        for (k, v) in __frame.f_locals.items():
            if any((var in k) for var in ("__frame", "__file", "__func")):
                continue
            print(f"<INTROSPECT> {__file}:{__func} - {k}:{v.__class__.__name__}")
        if isinstance(batch_data, pd.DataFrame):
            batch_data = PandasBatchData(self, batch_data)
        elif isinstance(batch_data, PandasBatchData):
            pass
        else:
            raise ge_exceptions.GreatExpectationsError(
                "PandasExecutionEngine requires batch data that is either a DataFrame or a PandasBatchData object"
            )
        super().load_batch_data(batch_id=batch_id, batch_data=batch_data)

    def get_batch_data_and_markers(
        self, batch_spec: BatchSpec
    ) -> Tuple[(Any, BatchMarkers)]:
        import inspect

        __frame = inspect.currentframe()
        __file = __frame.f_code.co_filename
        __func = __frame.f_code.co_name
        for (k, v) in __frame.f_locals.items():
            if any((var in k) for var in ("__frame", "__file", "__func")):
                continue
            print(f"<INTROSPECT> {__file}:{__func} - {k}:{v.__class__.__name__}")
        batch_markers: BatchMarkers = BatchMarkers(
            {
                "ge_load_time": datetime.datetime.now(datetime.timezone.utc).strftime(
                    "%Y%m%dT%H%M%S.%fZ"
                )
            }
        )
        batch_data: Any
        if isinstance(batch_spec, RuntimeDataBatchSpec):
            batch_data = batch_spec.batch_data
            if isinstance(batch_data, str):
                raise ge_exceptions.ExecutionEngineError(
                    f"""PandasExecutionEngine has been passed a string type batch_data, "{batch_data}", which is illegal.
Please check your config."""
                )
            if isinstance(batch_spec.batch_data, pd.DataFrame):
                df = batch_spec.batch_data
            elif isinstance(batch_spec.batch_data, PandasBatchData):
                df = batch_spec.batch_data.dataframe
            else:
                raise ValueError(
                    "RuntimeDataBatchSpec must provide a Pandas DataFrame or PandasBatchData object."
                )
            batch_spec.batch_data = "PandasDataFrame"
        elif isinstance(batch_spec, S3BatchSpec):
            if self._s3 is None:
                self._instantiate_s3_client()
            if self._s3 is None:
                raise ge_exceptions.ExecutionEngineError(
                    "PandasExecutionEngine has been passed a S3BatchSpec,\n                        but the ExecutionEngine does not have a boto3 client configured. Please check your config."
                )
            s3_engine = self._s3
            try:
                reader_method: str = batch_spec.reader_method
                reader_options: dict = batch_spec.reader_options or {}
                path: str = batch_spec.path
                s3_url = S3Url(path)
                if "compression" not in reader_options.keys():
                    inferred_compression_param = sniff_s3_compression(s3_url)
                    if inferred_compression_param is not None:
                        reader_options["compression"] = inferred_compression_param
                s3_object = s3_engine.get_object(Bucket=s3_url.bucket, Key=s3_url.key)
            except (ParamValidationError, ClientError) as error:
                raise ge_exceptions.ExecutionEngineError(
                    f"PandasExecutionEngine encountered the following error while trying to read data from S3 Bucket: {error}"
                )
            logger.debug(
                f"Fetching s3 object. Bucket: {s3_url.bucket} Key: {s3_url.key}"
            )
            reader_fn = self._get_reader_fn(reader_method, s3_url.key)
            buf = BytesIO(s3_object["Body"].read())
            buf.seek(0)
            df = reader_fn(buf, **reader_options)
        elif isinstance(batch_spec, AzureBatchSpec):
            if self._azure is None:
                self._instantiate_azure_client()
            if self._azure is None:
                raise ge_exceptions.ExecutionEngineError(
                    "PandasExecutionEngine has been passed a AzureBatchSpec,\n                        but the ExecutionEngine does not have an Azure client configured. Please check your config."
                )
            azure_engine = self._azure
            reader_method: str = batch_spec.reader_method
            reader_options: dict = batch_spec.reader_options or {}
            path: str = batch_spec.path
            azure_url = AzureUrl(path)
            blob_client = azure_engine.get_blob_client(
                container=azure_url.container, blob=azure_url.blob
            )
            azure_object = blob_client.download_blob()
            logger.debug(
                f"Fetching Azure blob. Container: {azure_url.container} Blob: {azure_url.blob}"
            )
            reader_fn = self._get_reader_fn(reader_method, azure_url.blob)
            buf = BytesIO(azure_object.readall())
            buf.seek(0)
            df = reader_fn(buf, **reader_options)
        elif isinstance(batch_spec, GCSBatchSpec):
            if self._gcs is None:
                self._instantiate_gcs_client()
            if self._gcs is None:
                raise ge_exceptions.ExecutionEngineError(
                    "PandasExecutionEngine has been passed a GCSBatchSpec,\n                        but the ExecutionEngine does not have an GCS client configured. Please check your config."
                )
            gcs_engine = self._gcs
            gcs_url = GCSUrl(batch_spec.path)
            reader_method: str = batch_spec.reader_method
            reader_options: dict = batch_spec.reader_options or {}
            try:
                gcs_bucket = gcs_engine.get_bucket(gcs_url.bucket)
                gcs_blob = gcs_bucket.blob(gcs_url.blob)
                logger.debug(
                    f"Fetching GCS blob. Bucket: {gcs_url.bucket} Blob: {gcs_url.blob}"
                )
            except GoogleAPIError as error:
                raise ge_exceptions.ExecutionEngineError(
                    f"PandasExecutionEngine encountered the following error while trying to read data from GCS Bucket: {error}"
                )
            reader_fn = self._get_reader_fn(reader_method, gcs_url.blob)
            buf = BytesIO(gcs_blob.download_as_bytes())
            buf.seek(0)
            df = reader_fn(buf, **reader_options)
        elif isinstance(batch_spec, PathBatchSpec):
            reader_method: str = batch_spec.reader_method
            reader_options: dict = batch_spec.reader_options
            path: str = batch_spec.path
            reader_fn: Callable = self._get_reader_fn(reader_method, path)
            df = reader_fn(path, **reader_options)
        else:
            raise ge_exceptions.BatchSpecError(
                f"batch_spec must be of type RuntimeDataBatchSpec, PathBatchSpec, S3BatchSpec, or AzureBatchSpec, not {batch_spec.__class__.__name__}"
            )
        df = self._apply_splitting_and_sampling_methods(batch_spec, df)
        if df.memory_usage().sum() < HASH_THRESHOLD:
            batch_markers["pandas_data_fingerprint"] = hash_pandas_dataframe(df)
        typed_batch_data = PandasBatchData(execution_engine=self, dataframe=df)
        return (typed_batch_data, batch_markers)

    def _apply_splitting_and_sampling_methods(self, batch_spec, batch_data):
        import inspect

        __frame = inspect.currentframe()
        __file = __frame.f_code.co_filename
        __func = __frame.f_code.co_name
        for (k, v) in __frame.f_locals.items():
            if any((var in k) for var in ("__frame", "__file", "__func")):
                continue
            print(f"<INTROSPECT> {__file}:{__func} - {k}:{v.__class__.__name__}")
        splitter_method_name: Optional[str] = batch_spec.get("splitter_method")
        if splitter_method_name:
            splitter_fn: Callable = self._data_splitter.get_splitter_method(
                splitter_method_name
            )
            splitter_kwargs: dict = batch_spec.get("splitter_kwargs") or {}
            batch_data = splitter_fn(batch_data, **splitter_kwargs)
        if batch_spec.get("sampling_method"):
            sampling_fn = getattr(self, batch_spec.get("sampling_method"))
            sampling_kwargs: dict = batch_spec.get("sampling_kwargs") or {}
            batch_data = sampling_fn(batch_data, **sampling_kwargs)
        return batch_data

    @property
    def dataframe(self):
        import inspect

        __frame = inspect.currentframe()
        __file = __frame.f_code.co_filename
        __func = __frame.f_code.co_name
        for (k, v) in __frame.f_locals.items():
            if any((var in k) for var in ("__frame", "__file", "__func")):
                continue
            print(f"<INTROSPECT> {__file}:{__func} - {k}:{v.__class__.__name__}")
        "Tests whether or not a Batch has been loaded. If the loaded batch does not exist, raises a\n        ValueError Exception\n        "
        if self.active_batch_data is None:
            raise ValueError(
                "Batch has not been loaded - please run load_batch_data() to load a batch."
            )
        return self.active_batch_data.dataframe

    @staticmethod
    def guess_reader_method_from_path(path):
        import inspect

        __frame = inspect.currentframe()
        __file = __frame.f_code.co_filename
        __func = __frame.f_code.co_name
        for (k, v) in __frame.f_locals.items():
            if any((var in k) for var in ("__frame", "__file", "__func")):
                continue
            print(f"<INTROSPECT> {__file}:{__func} - {k}:{v.__class__.__name__}")
        "Helper method for deciding which reader to use to read in a certain path.\n\n        Args:\n            path (str): the to use to guess\n\n        Returns:\n            ReaderMethod to use for the filepath\n\n        "
        if path.endswith(".csv") or path.endswith(".tsv"):
            return {"reader_method": "read_csv"}
        elif path.endswith(".parquet"):
            return {"reader_method": "read_parquet"}
        elif path.endswith(".xlsx") or path.endswith(".xls"):
            return {"reader_method": "read_excel"}
        elif path.endswith(".json"):
            return {"reader_method": "read_json"}
        elif path.endswith(".pkl"):
            return {"reader_method": "read_pickle"}
        elif path.endswith(".feather"):
            return {"reader_method": "read_feather"}
        elif path.endswith(".csv.gz") or path.endswith(".tsv.gz"):
            return {
                "reader_method": "read_csv",
                "reader_options": {"compression": "gzip"},
            }
        elif path.endswith(".sas7bdat") or path.endswith(".xpt"):
            return {"reader_method": "read_sas"}
        else:
            raise ge_exceptions.ExecutionEngineError(
                f'Unable to determine reader method from path: "{path}".'
            )

    def _get_reader_fn(self, reader_method=None, path=None):
        import inspect

        __frame = inspect.currentframe()
        __file = __frame.f_code.co_filename
        __func = __frame.f_code.co_name
        for (k, v) in __frame.f_locals.items():
            if any((var in k) for var in ("__frame", "__file", "__func")):
                continue
            print(f"<INTROSPECT> {__file}:{__func} - {k}:{v.__class__.__name__}")
        "Static helper for parsing reader types. If reader_method is not provided, path will be used to guess the\n        correct reader_method.\n\n        Args:\n            reader_method (str): the name of the reader method to use, if available.\n            path (str): the path used to guess\n\n        Returns:\n            ReaderMethod to use for the filepath\n\n        "
        if (reader_method is None) and (path is None):
            raise ge_exceptions.ExecutionEngineError(
                "Unable to determine pandas reader function without reader_method or path."
            )
        reader_options = {}
        if reader_method is None:
            path_guess = self.guess_reader_method_from_path(path)
            reader_method = path_guess["reader_method"]
            reader_options = path_guess.get("reader_options")
        try:
            reader_fn = getattr(pd, reader_method)
            if reader_options:
                reader_fn = partial(reader_fn, **reader_options)
            return reader_fn
        except AttributeError:
            raise ge_exceptions.ExecutionEngineError(
                f'Unable to find reader_method "{reader_method}" in pandas.'
            )

    def get_domain_records(self, domain_kwargs: dict) -> pd.DataFrame:
        import inspect

        __frame = inspect.currentframe()
        __file = __frame.f_code.co_filename
        __func = __frame.f_code.co_name
        for (k, v) in __frame.f_locals.items():
            if any((var in k) for var in ("__frame", "__file", "__func")):
                continue
            print(f"<INTROSPECT> {__file}:{__func} - {k}:{v.__class__.__name__}")
        "\n        Uses the given domain kwargs (which include row_condition, condition_parser, and ignore_row_if directives) to\n        obtain and/or query a batch. Returns in the format of a Pandas DataFrame.\n\n        Args:\n            domain_kwargs (dict) - A dictionary consisting of the domain kwargs specifying which data to obtain\n\n        Returns:\n            A DataFrame (the data on which to compute)\n        "
        table = domain_kwargs.get("table", None)
        if table:
            raise ValueError(
                "PandasExecutionEngine does not currently support multiple named tables."
            )
        batch_id = domain_kwargs.get("batch_id")
        if batch_id is None:
            if self.active_batch_data_id is not None:
                data = self.active_batch_data.dataframe
            else:
                raise ge_exceptions.ValidationError(
                    "No batch is specified, but could not identify a loaded batch."
                )
        elif batch_id in self.loaded_batch_data_dict:
            data = self.loaded_batch_data_dict[batch_id].dataframe
        else:
            raise ge_exceptions.ValidationError(
                f"Unable to find batch with batch_id {batch_id}"
            )
        row_condition = domain_kwargs.get("row_condition", None)
        if row_condition:
            condition_parser = domain_kwargs.get("condition_parser", None)
            if condition_parser not in ["python", "pandas"]:
                raise ValueError(
                    "condition_parser is required when setting a row_condition, and must be 'python' or 'pandas'"
                )
            else:
                data = data.query(row_condition, parser=condition_parser)
        if "column" in domain_kwargs:
            return data
        if (
            ("column_A" in domain_kwargs)
            and ("column_B" in domain_kwargs)
            and ("ignore_row_if" in domain_kwargs)
        ):
            column_A_name = domain_kwargs["column_A"]
            column_B_name = domain_kwargs["column_B"]
            ignore_row_if = domain_kwargs["ignore_row_if"]
            if ignore_row_if == "both_values_are_missing":
                data = data.dropna(
                    axis=0, how="all", subset=[column_A_name, column_B_name]
                )
            elif ignore_row_if == "either_value_is_missing":
                data = data.dropna(
                    axis=0, how="any", subset=[column_A_name, column_B_name]
                )
            else:
                if ignore_row_if not in ["neither", "never"]:
                    raise ValueError(
                        f'Unrecognized value of ignore_row_if ("{ignore_row_if}").'
                    )
                if ignore_row_if == "never":
                    warnings.warn(
                        f"""The correct "no-action" value of the "ignore_row_if" directive for the column pair case is "neither" (the use of "{ignore_row_if}" is deprecated as of v0.13.29 and will be removed in v0.16).  Please use "neither" instead.
""",
                        DeprecationWarning,
                    )
            return data
        if ("column_list" in domain_kwargs) and ("ignore_row_if" in domain_kwargs):
            column_list = domain_kwargs["column_list"]
            ignore_row_if = domain_kwargs["ignore_row_if"]
            if ignore_row_if == "all_values_are_missing":
                data = data.dropna(axis=0, how="all", subset=column_list)
            elif ignore_row_if == "any_value_is_missing":
                data = data.dropna(axis=0, how="any", subset=column_list)
            elif ignore_row_if != "never":
                raise ValueError(
                    f'Unrecognized value of ignore_row_if ("{ignore_row_if}").'
                )
            return data
        return data

    def get_compute_domain(
        self,
        domain_kwargs: dict,
        domain_type: Union[(str, MetricDomainTypes)],
        accessor_keys: Optional[Iterable[str]] = None,
    ) -> Tuple[(pd.DataFrame, dict, dict)]:
        import inspect

        __frame = inspect.currentframe()
        __file = __frame.f_code.co_filename
        __func = __frame.f_code.co_name
        for (k, v) in __frame.f_locals.items():
            if any((var in k) for var in ("__frame", "__file", "__func")):
                continue
            print(f"<INTROSPECT> {__file}:{__func} - {k}:{v.__class__.__name__}")
        '\n        Uses the given domain kwargs (which include row_condition, condition_parser, and ignore_row_if directives) to\n        obtain and/or query a batch.  Returns in the format of a Pandas DataFrame. If the domain is a single column,\n        this is added to \'accessor domain kwargs\' and used for later access\n\n        Args:\n            domain_kwargs (dict) - A dictionary consisting of the domain kwargs specifying which data to obtain\n            domain_type (str or MetricDomainTypes) - an Enum value indicating which metric domain the user would\n            like to be using, or a corresponding string value representing it. String types include "column",\n            "column_pair", "table", and "other".  Enum types include capitalized versions of these from the\n            class MetricDomainTypes.\n            accessor_keys (str iterable) - keys that are part of the compute domain but should be ignored when\n            describing the domain and simply transferred with their associated values into accessor_domain_kwargs.\n\n        Returns:\n            A tuple including:\n              - a DataFrame (the data on which to compute)\n              - a dictionary of compute_domain_kwargs, describing the DataFrame\n              - a dictionary of accessor_domain_kwargs, describing any accessors needed to\n                identify the domain within the compute domain\n        '
        data = self.get_domain_records(domain_kwargs)
        table = domain_kwargs.get("table", None)
        if table:
            raise ValueError(
                "PandasExecutionEngine does not currently support multiple named tables."
            )
        split_domain_kwargs = self._split_domain_kwargs(
            domain_kwargs, domain_type, accessor_keys
        )
        return (data, split_domain_kwargs.compute, split_domain_kwargs.accessor)

    @staticmethod
    def _sample_using_random(df, p: float = 0.1):
        import inspect

        __frame = inspect.currentframe()
        __file = __frame.f_code.co_filename
        __func = __frame.f_code.co_name
        for (k, v) in __frame.f_locals.items():
            if any((var in k) for var in ("__frame", "__file", "__func")):
                continue
            print(f"<INTROSPECT> {__file}:{__func} - {k}:{v.__class__.__name__}")
        "Take a random sample of rows, retaining proportion p"
        return df[df.index.map(lambda x: (random.random() < p))]

    @staticmethod
    def _sample_using_mod(df, column_name: str, mod: int, value: int):
        import inspect

        __frame = inspect.currentframe()
        __file = __frame.f_code.co_filename
        __func = __frame.f_code.co_name
        for (k, v) in __frame.f_locals.items():
            if any((var in k) for var in ("__frame", "__file", "__func")):
                continue
            print(f"<INTROSPECT> {__file}:{__func} - {k}:{v.__class__.__name__}")
        "Take the mod of named column, and only keep rows that match the given value"
        return df[df[column_name].map(lambda x: ((x % mod) == value))]

    @staticmethod
    def _sample_using_a_list(df, column_name: str, value_list: list):
        import inspect

        __frame = inspect.currentframe()
        __file = __frame.f_code.co_filename
        __func = __frame.f_code.co_name
        for (k, v) in __frame.f_locals.items():
            if any((var in k) for var in ("__frame", "__file", "__func")):
                continue
            print(f"<INTROSPECT> {__file}:{__func} - {k}:{v.__class__.__name__}")
        "Match the values in the named column against value_list, and only keep the matches"
        return df[df[column_name].isin(value_list)]

    @staticmethod
    def _sample_using_hash(
        df,
        column_name: str,
        hash_digits: int = 1,
        hash_value: str = "f",
        hash_function_name: str = "md5",
    ):
        import inspect

        __frame = inspect.currentframe()
        __file = __frame.f_code.co_filename
        __func = __frame.f_code.co_name
        for (k, v) in __frame.f_locals.items():
            if any((var in k) for var in ("__frame", "__file", "__func")):
                continue
            print(f"<INTROSPECT> {__file}:{__func} - {k}:{v.__class__.__name__}")
        "Hash the values in the named column, and only keep rows that match the given hash_value"
        try:
            hash_func = getattr(hashlib, hash_function_name)
        except (TypeError, AttributeError):
            raise ge_exceptions.ExecutionEngineError(
                f"""The sampling method used with PandasExecutionEngine has a reference to an invalid hash_function_name.
                    Reference to {hash_function_name} cannot be found."""
            )
        matches = df[column_name].map(
            lambda x: (
                hash_func(str(x).encode()).hexdigest()[((-1) * hash_digits) :]
                == hash_value
            )
        )
        return df[matches]


def hash_pandas_dataframe(df):
    import inspect

    __frame = inspect.currentframe()
    __file = __frame.f_code.co_filename
    __func = __frame.f_code.co_name
    for (k, v) in __frame.f_locals.items():
        if any((var in k) for var in ("__frame", "__file", "__func")):
            continue
        print(f"<INTROSPECT> {__file}:{__func} - {k}:{v.__class__.__name__}")
    try:
        obj = pd.util.hash_pandas_object(df, index=True).values
    except TypeError:
        obj = pickle.dumps(df, pickle.HIGHEST_PROTOCOL)
    return hashlib.md5(obj).hexdigest()
