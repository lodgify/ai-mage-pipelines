from mage_ai.settings.repo import get_repo_path
from mage_ai.io.config import ConfigFileLoader
from mage_ai.io.postgres import Postgres
from pandas import DataFrame
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
    
    df = None
    config_profile = None

    try:
        if isinstance(data, list):
            # If data is a nested list
            if len(data) > 0 and isinstance(data[0], list):
                print("Nested list format detected.")
                nested_data = data[0]
                if len(nested_data) > 0 and isinstance(nested_data[0], dict):
                    df = DataFrame(nested_data[0].get('traces_df', []))
                    config_profile = nested_data[0].get('io_config_profile_name')
            # If data is a list of dictionaries
            elif len(data) > 0 and isinstance(data[0], dict):
                print("List of dictionaries format detected.")
                df = DataFrame(data[0].get('traces_df', []))
                config_profile = data[0].get('io_config_profile_name')
        elif isinstance(data, dict):
            print("Dictionary format detected.")
            df = DataFrame(data.get('traces_df', []))
            config_profile = data.get('io_config_profile_name')
        else:
            print("Unexpected data format.")
            return  # Exit function if data format is not as expected

        # Additional debugging prints to verify DataFrame and config_profile
        #print("Extracted DataFrame:", df)
        print("Extracted config_profile:", config_profile)

        schema_name = 'public'  # Specify the name of the schema to export data to
        table_name = '"LangfuseTraces"'  # Specify the name of the table to export data to
        config_path = path.join(get_repo_path(), 'io_config.yaml')
        
        if df is not None and not df.empty:
            with Postgres.with_config(ConfigFileLoader(config_path, config_profile)) as loader:
                loader.export(
                    df,
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
