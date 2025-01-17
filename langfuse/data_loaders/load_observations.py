import json
import pandas as pd

from langfuse.utils import utils, constants
if 'data_loader' not in globals():
    from mage_ai.data_preparation.decorators import data_loader
if 'test' not in globals():
    from mage_ai.data_preparation.decorators import test


@data_loader
def load_observations(data: pd.DataFrame, *args, **kwargs):
    if data.empty:
        print("Not loading observations, no traces found.")
        return pd.DataFrame()
    
    observations_dfs = []
    
    for trace_id in data['Id'].tolist():
        params = {
            'traceId': trace_id,
        }
        observations_data = utils.fetch_all_pages("observations", constants.days_back, params)
        
        trace_obs_dicts = [{
            'Id': observation['id'],
            'TraceId': trace_id,  # Use trace_id from the outer loop
            'Type': observation['type'],
            'Name': observation.get('name'),
            'StartTime': observation['startTime'],
            'EndTime': observation.get('endTime'),
            'CompletionStartTime': observation.get('completionStartTime'),
            'Model': observation.get('model'),
            'ModelParameters': json.dumps(observation.get('modelParameters')),
            'Input': json.dumps(observation.get('input')),
            'Version': observation.get('version'),
            'Metadata': json.dumps(observation.get('metadata')),
            'Output': json.dumps(observation.get('output')),
            'Usage': json.dumps(observation.get('usage')),
            'Level': observation['level'],
            'StatusMessage': observation.get('statusMessage'),
            'ParentObservationId': observation.get('parentObservationId'),
            'PromptId': observation.get('promptId'),
            'ModelId': observation.get('modelId'),
            'InputPrice': observation.get('inputPrice'),
            'OutputPrice': observation.get('outputPrice'),
            'TotalPrice': observation.get('totalPrice'),
            'CalculatedInputCost': observation.get('calculatedInputCost'),
            'CalculatedOutputCost': observation.get('calculatedOutputCost'),
            'CalculatedTotalCost': observation.get('calculatedTotalCost'),
            'Latency': observation.get('latency')
        } for observation in observations_data]

        observations_dfs.append(pd.DataFrame(trace_obs_dicts))

    return pd.concat(observations_dfs) if observations_dfs else pd.DataFrame()   


@test
def test_output(output, *args) -> None:
    """
    Template code for testing the output of the block.
    """
    assert output is not None, 'The output is undefined'

if __name__ == "__main__":
    traces_df = pd.read_pickle('traces.pkl')
    observations_df = load_observations(traces_df)
    observations_df.to_pickle('observations.pkl')
    print(observations_df)