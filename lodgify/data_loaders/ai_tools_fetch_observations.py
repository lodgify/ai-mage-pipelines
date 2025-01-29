import json
from concurrent.futures import ThreadPoolExecutor, as_completed

import pandas as pd

from lodgify.utils.ai_tools import constants, utils_langfuse
from lodgify.utils.ai_tools.logger import logger

if "data_loader" not in globals():
    from mage_ai.data_preparation.decorators import data_loader
if "test" not in globals():
    from mage_ai.data_preparation.decorators import test


def fetch_observations_for_trace(trace_id, start_from_date: str, end_date: str):
    params = {
        "traceId": trace_id,
    }
    observations_data = utils_langfuse.fetch_all_pages("observations", start_from_date, end_date, params)

    return [
        {
            "Id": observation["id"],
            "TraceId": trace_id,
            "Type": observation["type"],
            "Name": observation.get("name"),
            "StartTime": observation["startTime"],
            "EndTime": observation.get("endTime"),
            "CompletionStartTime": observation.get("completionStartTime"),
            "Model": observation.get("model"),
            "ModelParameters": json.dumps(observation["modelParameters"]) if observation["modelParameters"] else None,
            "Input": json.dumps(observation.get("input")) if observation.get("input") else None,
            "Version": observation.get("version"),
            "Metadata": json.dumps(observation.get("metadata")) if observation.get("metadata") else None,
            "Output": json.dumps(observation.get("output")) if observation.get("output") else None,
            "Usage": json.dumps(observation.get("usage")) if observation.get("usage") else None,
            "Level": observation["level"],
            "StatusMessage": observation.get("statusMessage"),
            "ParentObservationId": observation.get("parentObservationId"),
            "PromptId": observation.get("promptId"),
            "ModelId": observation.get("modelId"),
            "InputPrice": observation.get("inputPrice"),
            "OutputPrice": observation.get("outputPrice"),
            "TotalPrice": observation.get("totalPrice"),
            "CalculatedInputCost": observation.get("calculatedInputCost"),
            "CalculatedOutputCost": observation.get("calculatedOutputCost"),
            "CalculatedTotalCost": observation.get("calculatedTotalCost"),
            "Latency": observation.get("latency"),
            "TotalToken": observation.get("totalToken"),
        }
        for observation in observations_data
    ]


@data_loader
def load_observations(data: pd.DataFrame, *args, **kwargs):
    if data.empty:
        logger.warning("Not loading observations, no traces found.")
        return pd.DataFrame()

    observations = []
    logger.info(f"Run params {args=}, {kwargs=}")
    start_from_date, end_date = utils_langfuse.calculate_start_and_end_dates(constants.DAYS_BACK, **kwargs)
    logger.info(f"Fetching data {start_from_date=}, {end_date=}")
    trace_ids = data["Id"].tolist()
    # we need to parallelize fetching so that it is not too slow. The reason is that
    # we can only fetch observations for a trace at a time (ie, not all the observations for all the traces at once)
    # not too high to respect API limits: https://langfuse.com/faq/all/api-limits
    processed_count = 0
    with ThreadPoolExecutor(max_workers=8) as executor:
        future_to_trace = {
            executor.submit(fetch_observations_for_trace, trace_id, start_from_date, end_date): trace_id
            for trace_id in trace_ids
        }
        nth_trace = 100
        logger.info(f"Will be logging completion of every {nth_trace=}")

        for future in as_completed(future_to_trace):
            try:
                processed_count += 1
                if processed_count % nth_trace == 0:
                    trace_id = future_to_trace[future]
                    logger.debug(f"Processing {processed_count}th trace (out of {len(trace_ids)})")
                trace_obs_dicts = future.result()
                if trace_obs_dicts:
                    observations.extend(trace_obs_dicts)
            except Exception:
                trace_id = future_to_trace[future]
                logger.exception(f"Error processing trace {trace_id}")
                raise  # Re-raise the exception after logging

    return pd.DataFrame(observations) if observations else pd.DataFrame()


@test
def test_output(output, *args) -> None:
    """Template code for testing the output of the block."""
    assert output is not None, "The output is undefined"


if __name__ == "__main__":
    # this is only for testing as a script locally, mage uses decorators to run the code
    logger.debug("running __main__")
    traces_df = pd.read_pickle("traces.pkl")
    observations_df = load_observations(traces_df)
    observations_df.to_pickle("observations.pkl")
    logger.debug(observations_df)
