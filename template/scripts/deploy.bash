#/usr/bin/env bash

PACKAGE_NAME="{{ .project_slug }}"

source .venv/bin/activate

echo "Removing dist folder..."
rm -rf dist

echo "Building project..."
kedro package

echo "Create bundle resources..."
python src/$PACKAGE_NAME/databricks_bundle.py

echo "Upload project configuration to Databricks..."
tar -xf dist/conf-$PACKAGE_NAME.tar.gz -C ./dist
databricks fs rm dbfs:/FileStore/$PACKAGE_NAME/conf --recursive || echo 'No configuration to remove'
databricks fs cp dist/conf dbfs:/FileStore/$PACKAGE_NAME/conf --recursive --overwrite

echo "Upload project data to Databricks..."
databricks fs rm dbfs:/FileStore/$PACKAGE_NAME/data --recursive || echo 'No data to remove'
databricks fs mkdirs dbfs:/FileStore/$PACKAGE_NAME/data
databricks fs mkdirs dbfs:/FileStore/$PACKAGE_NAME/data/01_raw
databricks fs mkdirs dbfs:/FileStore/$PACKAGE_NAME/data/02_intermediate
databricks fs mkdirs dbfs:/FileStore/$PACKAGE_NAME/data/03_primary
databricks fs mkdirs dbfs:/FileStore/$PACKAGE_NAME/data/04_feature
databricks fs mkdirs dbfs:/FileStore/$PACKAGE_NAME/data/05_model_input
databricks fs mkdirs dbfs:/FileStore/$PACKAGE_NAME/data/06_models
databricks fs mkdirs dbfs:/FileStore/$PACKAGE_NAME/data/07_model_output
databricks fs mkdirs dbfs:/FileStore/$PACKAGE_NAME/data/08_reporting
databricks fs cp ./data/01_raw dbfs:/FileStore/$PACKAGE_NAME/data/01_raw --recursive

echo "Deploying project to Databricks..."
databricks bundle deploy