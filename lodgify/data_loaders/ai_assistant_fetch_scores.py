import pandas as pd

from lodgify.utils.ai_assistant import constants, utils_langfuse
from lodgify.utils.ai_assistant.logger import logger

if "data_loader" not in globals():
    from mage_ai.data_preparation.decorators import data_loader
if "test" not in globals():
    from mage_ai.data_preparation.decorators import test


@data_loader
def load_scores(*args, **kwargs):
    logger.info(f"Run params {args=}, {kwargs=}")
    start_from_date, end_date = utils_langfuse.calculate_start_and_end_dates(constants.DAYS_BACK, **kwargs)
    logger.info(f"Fetching data {start_from_date=}, {end_date=}")
    scores_data = utils_langfuse.fetch_all_pages("scores", start_from_date, end_date)
    scores_dicts = [
        {
            "Id": score["id"],
            "TraceId": score["traceId"],
            "Name": score["name"],
            "Value": score["value"],
            "Source": score.get("source"),
            "ObservationId": score.get("observationId"),
            "Timestamp": score["timestamp"],
            "Comment": score.get("comment"),
        }
        for score in scores_data
    ]

    return pd.DataFrame(scores_dicts) if scores_dicts else pd.DataFrame()


@test
def test_output(output, *args) -> None:
    """Template code for testing the output of the block."""
    assert output is not None, "The output is undefined"


if __name__ == "__main__":
    # this is only for testing as a script locally, mage uses decorators to run the code
    logger.debug("running __main__")
    scores_df = load_scores()
    scores_df.to_pickle("scores.pkl")
    logger.debug(scores_df)
