# Databricks Asset Bundles Meets Kedro

This repository demonstrates how to use [Databricks Asset Bundles](https://docs.databricks.com/en/dev-tools/bundles/index.html) with [Kedro](https://www.kedro.org).

## Overview

`Databricks Asset Bundles` is a feature that allows you develop databricks assets locally and then synchronize them with through the Databricks CLI. This is useful for developing and testing code locally before deploying it to a Databricks workspace. Additionally, it promotes best practices for software development such as version control, code review, and testing.

`Kedro` is a workflow development tool that helps you build reproducible, maintainable, and modular data pipelines. It is designed to work with a variety of data science and machine learning tools, and it provides a flexible and extensible framework for developing data pipelines.

The main reason for this template is that it allows you to use `Kedro`'s data pipeline development capabilities with `Databricks Asset Bundles`. This means that you would develop your data pipeline using `Kedro` and then package and distribute it using `Databricks Asset Bundles`, providing a seamless workflow for developing and deploying data pipelines on Databricks.

## Prerequisites

- [Databricks CLI](https://docs.databricks.com/dev-tools/cli/index.html)

## Getting Started

To use this template, you can use the `databricks bundle init` command as shown below:
```bash
databricks bundle init https://github.com/JenspederM/databricks-kedro-bundle.git # --output-dir <output-dir>
```

This will create a custom Kedro project in the current directory. If you want to specify a different output directory, you can use the `--output-dir` option.