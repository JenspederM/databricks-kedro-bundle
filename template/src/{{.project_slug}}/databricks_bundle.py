import logging

import yaml
import yamldiff

from pathlib import Path
from typing import Any

from kedro.framework.project import PACKAGE_NAME, find_pipelines
from kedro.pipeline import Pipeline
from rich import print
from databricks.sdk.service.jobs import (
    JobSettings,
    JobCluster,
    QueueSettings,
    Task,
    PythonWheelTask,
    TaskDependency,
    Format,
)
from databricks.sdk.service.compute import ClusterSpec, Library

logging.basicConfig(level=logging.INFO)
_PACKAGE = Path(__file__).parent
assert _PACKAGE.parent.stem == "src", "This file must be located in the package root."

if PACKAGE_NAME is None:
    from kedro.framework.project import configure_project

    package = _PACKAGE.stem
    configure_project(package)

    from kedro.framework.project import PACKAGE_NAME

assert PACKAGE_NAME is not None, "PACKAGE_NAME is None"

log = logging.getLogger(__name__)

_task_key_order = [
    "task_key",
    "job_cluster_key",
    "new_cluster",
    "depends_on",
    "spark_python_task",
    "python_wheel_task",
]

_workflow_key_order = [
    "name",
    "tags",
    "access_control_list",
    "email_notifications",
    "schedule",
    "max_concurrent_runs",
    "job_clusters",
    "tasks",
]


def _sort_dict(d: dict[Any, Any], key_order: list[str]) -> dict[Any, Any]:
    """Recursively sort the keys of a dictionary.

    Args:
        d (Dict[Any, Any]): dictionary to sort
        key_order (List[str]): list of keys to sort by

    Returns:
        Dict[Any, Any]: dictionary with ordered values
    """
    other_keys = [k for k in d.keys() if k not in key_order]
    order = key_order + other_keys

    return dict(sorted(d.items(), key=lambda x: order.index(x[0])))


def _remove_nulls_from_dict(d: dict[str, Any]) -> dict[str, float | int | str | bool]:
    """Remove None values from a dictionary.

    Args:
        d (Dict[str, Any]): dictionary to remove None values from

    Returns:
        Dict[str, float | int | str | bool]: dictionary with None values removed
    """
    for k, v in list(d.items()):
        if isinstance(v, dict):
            _remove_nulls_from_dict(v)
        elif isinstance(v, list):
            for item in v:
                if isinstance(item, dict):
                    _remove_nulls_from_dict(item)

        if v is None:
            del d[k]

    return d


def _load_existing_resources(resource_dir: Path):
    existing = {}

    for f in resource_dir.glob("*.yaml"):
        name = f.stem.removesuffix("_resources")
        with open(f, "r") as f:
            _existing = yaml.safe_load(f)
            existing[name] = _existing
        print(f"Resource for pipeline '{name}':")

    return existing


def _get_diff(existing, resources, resource_dir: Path):
    diff = yamldiff.dict_diff(existing, resources)

    if (
        len(diff.different_vals) > 0
        or len(diff.first_only) > 0
        or len(diff.second_only) > 0
    ):
        print("Changes detected in Databricks resources:")
        yamldiff.dictdiff.print_diff(diff)
        input("Press Enter to recreate resources...")

    else:
        print("No changes detected in Databricks resources.")
        return

    for f in resource_dir.glob("*.yaml"):
        f.unlink()

    return diff


def _create_task(name, depends_on=None, job_cluster_id=None):
    """Create a Databricks task for a given node.

    Args:
        name (str): name of the node
        depends_on (List[Node]): list of nodes that the task depends on
        job_cluster_id (str): ID of the job cluster to run the task on

    Returns:
        Dict[str, Any]: a Databricks task
    """
    task = Task(
        task_key=name,
        python_wheel_task=PythonWheelTask(
            package_name=PACKAGE_NAME,
            entry_point="databricks_run",
            parameters=[
                "--nodes",
                name,
                "--conf-source",
                f"/dbfs/FileStore/{PACKAGE_NAME}/conf",
                "--package-name",
                PACKAGE_NAME,
            ],
        ),
        job_cluster_key=job_cluster_id,
        depends_on=[TaskDependency(task_key=dep.name) for dep in depends_on],
        libraries=[Library(whl="../dist/*.whl")],
    )

    return task


def _create_workflow(name: str, pipeline: Pipeline):
    """Create a Databricks workflow for a given pipeline.

    Args:
        name (str): name of the pipeline
        pipeline (Pipeline): Kedro pipeline object

    Returns:
        Dict[str, Any]: a Databricks workflow
    """
    settings = JobSettings(
        name=name,
        tasks=[
            _create_task(node.name, depends_on=deps, job_cluster_id="default")
            for node, deps in pipeline.node_dependencies.items()
        ],
        job_clusters=[
            JobCluster(
                "default",
                new_cluster=ClusterSpec(
                    spark_version="14.3.x-scala2.12",
                    node_type_id="Standard_D4ds_v4",
                    num_workers=1,
                    spark_env_vars={
                        "KEDRO_LOGGING_CONFIG": f"/dbfs/FileStore/{PACKAGE_NAME}/conf/logging.yml",
                    },
                ),
            )
        ],
        max_concurrent_runs=1,
        queue=QueueSettings(enabled=True),
        format=Format.MULTI_TASK,
    )

    workflow = _sort_dict(settings.as_dict(), _workflow_key_order)
    workflow["tasks"] = [_sort_dict(t, _task_key_order) for t in workflow["tasks"]]
    return _remove_nulls_from_dict(workflow)


def generate_resources(pipelines: dict[str, Pipeline]) -> dict[str, dict[str, Any]]:
    """Generate Databricks resources for the given pipelines.

    Finds all pipelines in the project and generates Databricks asset bundle resources
    for each according to the Databricks REST API.

    Args:
        pipelines (dict[str, Pipeline]): A dictionary of pipeline names and their Kedro pipelines

    Returns:
        dict[str, dict[str, Any]]: A dictionary of pipeline names and their Databricks resources
    """

    jobs = {}

    for name, pipeline in pipelines.items():
        if len(pipeline.nodes) > 0:
            wf_name = f"{PACKAGE_NAME}_{name}"
            wf = _create_workflow(wf_name, pipeline)
            jobs[wf_name] = wf

    resources = {name: {"resources": {"jobs": jobs}}}
    log.info("Databricks resources generated successfully.")
    log.debug(resources)
    return resources


def main():
    """Generate Databricks resources for all pipelines in the project.

    This function generates Databricks asset bundle resources for all pipelines in the project
    and writes them to the `resources` directory in the project root.
    """
    root = _PACKAGE.parent.parent
    resource_dir = root / "resources"
    resource_dir.mkdir(parents=True, exist_ok=True)
    pipelines = find_pipelines()
    resources = generate_resources(pipelines)
    existing = _load_existing_resources(resource_dir)
    diff = _get_diff(existing, resources, resource_dir)

    if diff is None:
        print("No changes detected. Exiting...")
        return

    for name, resource in resources.items():
        print(f"Resource for pipeline '{name}':")
        print(resource)

        with open(f"{resource_dir}/{name}_resources.yaml", "w+") as f:
            yaml.dump(resource, f, default_flow_style=False, sort_keys=False, indent=2)


if __name__ == "__main__":
    main()
