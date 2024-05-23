"""
This is a boilerplate pipeline 'irisunity'
generated using Kedro 0.19.5
"""

from kedro.pipeline import Pipeline, node, pipeline

from .nodes import make_predictions, report_accuracy, split_data


def create_pipeline(**kwargs) -> Pipeline:
    return pipeline(
        [
            node(
                func=split_data,
                inputs=["example_iris_data", "parameters"],
                outputs=[
                    "X_train_unity",
                    "X_test_unity",
                    "y_train_unity",
                    "y_test_unity",
                ],
                name="unity_split",
            ),
            node(
                func=make_predictions,
                inputs=["X_train_unity", "X_test_unity", "y_train_unity"],
                outputs="y_pred_unity",
                name="unity_make_predictions",
            ),
            node(
                func=report_accuracy,
                inputs=["y_pred_unity", "y_test_unity", "parameters"],
                outputs=None,
                name="unity_report_accuracy",
            ),
        ]
    )
