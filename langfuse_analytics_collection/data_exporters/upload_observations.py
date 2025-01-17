from os import path

from loguru import logger
from mage_ai.io.config import ConfigFileLoader
from mage_ai.io.postgres import Postgres
from mage_ai.settings.repo import get_repo_path

from langfuse_analytics_collection.utils import constants

if "data_exporter" not in globals():
    from mage_ai.data_preparation.decorators import data_exporter


@data_exporter
def export_data_to_postgres(data, **kwargs) -> None:
    """Template for exporting data to a PostgreSQL database.
    Specify your configuration settings in 'io_config.yaml'.

    Docs: https://docs.mage.ai/design/data-loading#postgresql
    """
    # Debugging prints
    logger.info(f"Type of data: {type(data)}")

    try:
        config_profile = constants.CONFIG_MAPPER["io_config_profile_name"]
        # Additional debugging prints to verify DataFrame and config_profile
        logger.info(f"Extracted DataFrame: {data}")
        logger.info(f"Extracted config_profile: {config_profile}")

        schema_name = "public"  # Specify the name of the schema to export data to
        table_name = '"LangfuseObservations"'  # Specify the name of the table to export data to

        logger.info(f"{data.shape=}")
        if data is not None and not data.empty:
            with Postgres.with_config(
                ConfigFileLoader(path.join(get_repo_path(), "io_config.yaml"), config_profile)
            ) as loader:
                loader.export(
                    data,
                    schema_name,
                    table_name,
                    index=False,  # Specifies whether to include index in exported table
                    unique_conflict_method="UPDATE",
                    unique_constraints=["Id"],
                    allow_reserved_words=True,
                    if_exists="append",  # Specify resolution policy if table name already exists
                    case_sensitive=True,
                )
    except Exception:
        logger.exception("An error occurred")


if __name__ == "__main__":
    logger.info("running __main__")
    import pandas as pd

    data = pd.read_pickle("observations.pkl")
    export_data_to_postgres(data)
