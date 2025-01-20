from loguru import logger

from lodgify.utils.ai_assistant import utils_postgres

if "data_exporter" not in globals():
    from mage_ai.data_preparation.decorators import data_exporter


@data_exporter
def export_data_to_postgres(data, **kwargs) -> None:
    utils_postgres.export_data(data, schema_name="public", table_name="LangfuseObservations")


if __name__ == "__main__":
    logger.debug("running __main__")
    import pandas as pd

    data = pd.read_pickle("observations.pkl")
    export_data_to_postgres(data)
