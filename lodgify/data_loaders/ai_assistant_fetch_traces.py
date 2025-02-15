import json

import pandas as pd

from lodgify.utils.ai_assistant import constants, utils_langfuse
from lodgify.utils.ai_assistant.logger import logger

if "data_loader" not in globals():
    from mage_ai.data_preparation.decorators import data_loader
if "test" not in globals():
    from mage_ai.data_preparation.decorators import test


@data_loader
def load_traces(*args, **kwargs):
    logger.info(f"Run params {args=}, {kwargs=}")
    start_from_date, end_date = utils_langfuse.calculate_start_and_end_dates(constants.DAYS_BACK, **kwargs)
    logger.info(f"Fetching data {start_from_date=}, {end_date=}")
    traces_data = utils_langfuse.fetch_all_pages("traces", start_from_date, end_date)

    traces_dicts = [
        {
            "Id": trace["id"],
            "Timestamp": trace["timestamp"],
            "Name": trace.get("name"),
            "Input": json.dumps(trace.get("input")),
            "Output": json.dumps(trace.get("output")),
            "SessionId": trace.get("sessionId"),
            "Release": trace.get("release"),
            "Version": trace.get("version"),
            "UserId": trace.get("userId"),
            "Metadata": json.dumps(trace.get("metadata")),
            "Tags": json.dumps(trace.get("tags")),
            "Public": trace.get("public"),
            "HtmlPath": trace["htmlPath"],
            "TotalCost": trace["totalCost"],
        }
        for trace in traces_data
    ]

    return pd.DataFrame(traces_dicts) if traces_dicts else pd.DataFrame()


@test
def test_output(output, *args) -> None:
    """Template code for testing the output of the block."""
    assert output is not None, "The output is undefined"


if __name__ == "__main__":
    # this is only for testing as a script locally, mage uses decorators to run the code
    logger.debug("running __main__")
    traces_df = load_traces()
    traces_df.to_pickle("traces.pkl")
    logger.debug(traces_df)
