import os

import pandas as pd
from loguru import logger
from mage_ai.io.config import ConfigFileLoader
from mage_ai.io.postgres import Postgres
from mage_ai.settings.repo import get_repo_path

from lodgify.utils.ai_assistant import constants


def export_data(data: pd.DataFrame, schema_name: str, table_name: str):
    logger.info(f"Type of data: {type(data)}")

    try:
        config_profile = constants.get_config_mapper()["io_config_profile_name"]
        # Additional debugging prints to verify DataFrame and config_profile
        logger.info(f"Extracted DataFrame: {data}")
        logger.info(f"Extracted config_profile: {config_profile}")

        config_path = os.path.join(get_repo_path(), "io_config.yaml")

        logger.info(f"{data.shape=}")
        if data is not None and not data.empty:
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
