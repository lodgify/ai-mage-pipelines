from langfuse.utils import constants
from mage_ai.settings.repo import get_repo_path
from mage_ai.io.config import ConfigFileLoader
from mage_ai.io.postgres import Postgres
from os import path

if 'data_exporter' not in globals():
    from mage_ai.data_preparation.decorators import data_exporter


@data_exporter
def export_data_to_postgres(data, **kwargs) -> None:
    """
    Template for exporting data to a PostgreSQL database.
    Specify your configuration settings in 'io_config.yaml'.

    Docs: https://docs.mage.ai/design/data-loading#postgresql
    """
    # Debugging prints
    #print("Received data:", data)
    print("Type of data:", type(data))
    
    try:
        config_profile = constants.config_mapper["io_config_profile_name"]
        # Additional debugging prints to verify DataFrame and config_profile
        print("Extracted DataFrame:", data)
        print("Extracted config_profile:", config_profile)

        schema_name = 'public'  # Specify the name of the schema to export data to
        table_name = '"LangfuseScores"'  # Specify the name of the table to export data to
        config_path = path.join(get_repo_path(), 'io_config.yaml')
        
        print(f"{data.shape=}")
        if data is not None and not data.empty:
            with Postgres.with_config(ConfigFileLoader(config_path, config_profile)) as loader:
                loader.export(
                    data,
                    schema_name,
                    table_name,
                    index=False,  # Specifies whether to include index in exported table
                    unique_conflict_method='UPDATE',
                    unique_constraints=["Id"],
                    allow_reserved_words=True,
                    if_exists='append',  # Specify resolution policy if table name already exists
                    case_sensitive=True,
                )
    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    import pandas as pd
    data = pd.read_pickle('scores.pkl')
    export_data_to_postgres(data)