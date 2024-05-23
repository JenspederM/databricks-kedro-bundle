import logging
from pathlib import Path
import re
from typing import Any, Dict

from kedro.io import AbstractDataset
from kedro_datasets.spark.spark_dataset import _get_spark
from pyspark.sql import DataFrame, SparkSession

log = logging.getLogger(__name__)


def get_dbutils(
    spark: SparkSession,
):  # please note that this function is used in mocking by its name
    try:
        from pyspark.dbutils import DBUtils  # type: ignore

        if "dbutils" not in locals():
            utils = DBUtils(spark)
            return utils
        else:
            return locals().get("dbutils")
    except ImportError:
        return None


class UnityDataset(AbstractDataset[DataFrame, DataFrame]):
    """``UnityDataset`` loads / saves data from / to a Databricks cluster.

    Example:
    ::

        >>> from dabk.datasets import UnityDataset
        >>> dataset = UnityDataset(filepath="dbfs:/path/to/data")
    """

    def __init__(
        self,
        database: str,
        table: str,
        catalog: str = None,
        read_args: Dict[str, Any] = None,
        write_mode: str = "overwrite",
    ):
        """Creates a new instance of UnityDataset.

        Args:
            catalog: The catalog name.
            database: The database name.
            table: The table name.
        """

        self._catalog = catalog
        self._database = database
        self._table = table
        self._read_args = read_args or {}
        self._write_mode = write_mode

    def _get_table_path(self) -> str:
        table_path = f"{self._database}.{self._table}"
        if self._catalog:
            table_path = f"{self._catalog}.{self._database}.{self._table}"
        return table_path

    def _load(self) -> DataFrame:
        """Loads data from the image file.

        Returns:
            Data from the image file as a numpy array.
        """
        spark = _get_spark()
        return spark.read.options(**self._read_args).table(self._get_table_path())

    def _save(self, data: DataFrame) -> None:
        """Saves image data to the specified filepath"""
        log.info(
            f"Saving data to {self._get_table_path()} with mode {self._write_mode}"
        )
        spark = _get_spark()
        table = self._get_table_path()
        log.info(
            f"Saving data to {table} and it exists? {spark.catalog.tableExists(table)}"
        )
        try:
            data.write.mode("overwrite").saveAsTable(self._get_table_path())
        except Exception as e:
            log.warning(f"Problem saving data to {table}: {e}")
            estr = str(e)
            match = re.findall("'file:(.*?)'", estr)
            if match and len(match) == 1:
                existing_dir = Path(match[0])
                log.error(f"Removing existing directory: {existing_dir}")
                for f in existing_dir.glob("*"):
                    f.unlink()
                existing_dir.rmdir()
                data.write.mode("overwrite").saveAsTable(self._get_table_path())
            else:
                log.error(f"Could not find existing directory in error: {estr}")
                raise e

    def _describe(self) -> Dict[str, Any]:
        """Returns a dict that describes the attributes of the dataset"""
        return dict(
            catalog=self._catalog,
            schema=self._database,
            table=self._table,
        )
