# Databricks Asset Bundles Meets Kedro

This repository demonstrates how to use [Databricks Asset Bundles](https://docs.databricks.com/en/dev-tools/bundles/index.html) with [Kedro](https://www.kedro.org).

## Overview

Databricks Asset Bundles is a feature that allows you to package and distribute code and data assets in a single file. This is useful for sharing code and data assets across different Databricks workspaces, or for sharing code and data assets with others. 

This repository provides a starter template for using Databricks Asset Bundles with Kedro. The template includes a Kedro project that uses Databricks Asset Bundles to package and distribute code and data assets.

## Prerequisites

- [Databricks CLI](https://docs.databricks.com/dev-tools/cli/index.html)

## Getting Started

```bash
databricks bundle init https://github.com/JenspederM/databricks-kedro-bundle.git # --output-dir <output-dir>
```
