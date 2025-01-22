import os

import pandas as pd
from mage_ai.io.config import ConfigFileLoader
from mage_ai.io.postgres import Postgres
from mage_ai.settings.repo import get_repo_path

from lodgify.utils.ai_assistant import constants
from lodgify.utils.ai_assistant.logger import logger


def export_data(data: pd.DataFrame, schema_name: str, table_name: str):
    if not isinstance(data, pd.DataFrame):
        logger.warning("Data is not a pandas DataFrame, skipping saving to postgres")
        return
    if data.empty:
        logger.warning("Data is empty, skipping saving to postgres")
        return

    try:
        config_profile = constants.get_config_mapper()["io_config_profile_name"]
        # Additional debugging prints to verify DataFrame and config_profile
        logger.debug(f"Size of data: {data.shape=}")
        logger.debug(f"Extracted DataFrame: {data}")
        logger.debug(f"Extracted config_profile: {config_profile}")
        config_path = os.path.join(get_repo_path(), "io_config.yaml")

        with Postgres.with_config(ConfigFileLoader(config_path, config_profile)) as loader:
            loader.export(
                data,
                schema_name,
                f'"{table_name}"',
                index=False,  # Specifies whether to include index in exported table
                unique_conflict_method="UPDATE",
                unique_constraints=["Id"],
                allow_reserved_words=True,
                if_exists="append",  # Specify resolution policy if table name already exists
                case_sensitive=True,
            )
    except Exception:
        logger.exception("An error occurred")
