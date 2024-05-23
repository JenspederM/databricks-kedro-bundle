"""
This is a boilerplate pipeline 'irisunity'
generated using Kedro 0.19.5
"""

import logging
from typing import Dict, Tuple

import numpy as np
import pandas as pd
from kedro_datasets.spark.spark_dataset import _get_spark
from pyspark.sql import DataFrame


def split_data(data: DataFrame, parameters: Dict) -> Tuple:
    """Splits data into features and targets training and test sets.

    Args:
        data: Data containing features and target.
        parameters: Parameters defined in parameters.yml.
    Returns:
        Tuple: X_train, X_test, y_train, y_test
    """

    # Split to training and testing data
    data_train, data_test = data.randomSplit(
        weights=[parameters["train_fraction"], 1 - parameters["train_fraction"]]
    )

    X_train = data_train.drop(parameters["target_column"])
    X_test = data_test.drop(parameters["target_column"])
    y_train = data_train.select(parameters["target_column"])
    y_test = data_test.select(parameters["target_column"])

    return X_train, X_test, y_train, y_test


def make_predictions(
    X_train: pd.DataFrame, X_test: pd.DataFrame, y_train: pd.DataFrame
) -> DataFrame:
    """Uses 1-nearest neighbour classifier to create predictions.

    Args:
        X_train: Training data of features.
        y_train: Training data for target.
        X_test: Test data for features.

    Returns:
        y_pred: Prediction of the target variable.
    """
    spark = _get_spark()

    X_train_pd = pd.DataFrame(X_train.collect(), columns=X_train.columns)
    X_test_pd = pd.DataFrame(X_test.collect(), columns=X_test.columns)
    y_train_pd = pd.DataFrame(y_train.collect(), columns=y_train.columns)
    X_train_numpy = X_train_pd.to_numpy()
    X_test_numpy = X_test_pd.to_numpy()

    squared_distances = np.sum(
        (X_train_numpy[:, None, :] - X_test_numpy[None, :, :]) ** 2, axis=-1
    )
    nearest_neighbour = squared_distances.argmin(axis=0)
    y_pred = y_train_pd.iloc[nearest_neighbour]
    y_pred.index = X_test_pd.index

    return spark.createDataFrame(y_pred)


def report_accuracy(y_pred: pd.Series, y_test: pd.Series, parameters: Dict):
    """Calculates and logs the accuracy.

    Args:
        y_pred: Predicted target.
        y_test: True target.
        parameters: Parameters defined in parameters.yml.
    """

    y_pred = pd.DataFrame(y_pred.collect(), columns=y_pred.columns)[
        parameters["target_column"]
    ]
    y_test = pd.DataFrame(y_test.collect(), columns=y_test.columns)[
        parameters["target_column"]
    ]
    accuracy = (y_pred == y_test).sum() / len(y_test)
    logger = logging.getLogger(__name__)
    logger.info("Model has an accuracy of %.3f on test data.", accuracy)
