import io
import json
import pandas as pd
import requests
from base64 import b64encode
from typing import Dict, List
from datetime import datetime, timedelta
from mage_ai.data_preparation.shared.secrets import get_secret_value
if 'data_loader' not in globals():
    from mage_ai.data_preparation.decorators import data_loader
if 'test' not in globals():
    from mage_ai.data_preparation.decorators import test


@data_loader
def load_data_from_api(*args, **kwargs):
    """
    Template for loading data from API
    """
    # username = get_secret_value('langfuse_ai_assistant_live_public_key')
    # password = get_secret_value('langfuse_ai_assistant_live_secret_key')
    # credentials = f"{username}:{password}"

    credentials = ("pk-lf-0e0c56ec-6257-4ce6-a442-e353b2ee34fc", "sk-lf-c1dea310-ecdf-4e2b-9068-7c7e2491e048") # production

    BASE_URL = "https://cloud.langfuse.com/api/public"

    headers = {
        "Content-Type": "application/json"
    }

    def fetch_all_pages(url, headers, params):
        all_data = []
        params.update({
            'limit': 100  # to be safe
        })
        page = 1
        while True:
            params['page'] = page
            print(f"Fetching page {page}")
            response = requests.get(url, headers=headers, params=params, auth=credentials)
            if response.status_code == 200:
                data = response.json()
                extracted_data = data['data']
                if not extracted_data:
                    break
                all_data.extend(extracted_data)
                page += 1
            else:
                response.raise_for_status()
                break
        print(f"Total pages: {page}")
        return all_data



    def get_scores(days_back=1):
        yesterday_date = datetime.now() - timedelta(days=days_back)
        date_str = yesterday_date.strftime('%Y-%m-%d')
        start_date = f"{date_str}T00:00:00Z"
        
        params = {
            'fromTimestamp': start_date, 
        }
        
        scores_data = fetch_all_pages(f"{BASE_URL}/scores", headers, params)
        scores_dicts = [{
            'Id': score['id'],
            'TraceId': score['traceId'],
            'Name': score['name'],
            'Value': score['value'],
            'Source': score.get('source'),
            'ObservationId': score.get('observationId'),
            'Timestamp': score['timestamp'],
            'Comment': score.get('comment')
        } for score in scores_data]

        return pd.DataFrame(scores_dicts)

    def get_traces(days_back=1):
        yesterday_date = datetime.now() - timedelta(days=days_back)
        
        date_str = yesterday_date.strftime('%Y-%m-%d')
        start_date = f"{date_str}T00:00:00Z"
        
        params = {
            'fromTimestamp': start_date, 
        }
        
        traces_data = fetch_all_pages(f"{BASE_URL}/traces", headers, params)
        traces_dicts = [{
            'Id': trace['id'],
            'Timestamp': trace['timestamp'],
            'Name': trace.get('name'),
            'Input': json.dumps(trace.get('input')),
            'Output': json.dumps(trace.get('output')),
            'SessionId': trace.get('sessionId'),
            'Release': trace.get('release'),
            'Version': trace.get('version'),
            'UserId': trace.get('userId'),
            'Metadata': json.dumps(trace.get('metadata')),
            'Tags': json.dumps(trace.get('tags')),
            'Public': trace.get('public'),
            'HtmlPath': trace['htmlPath'],
            'TotalCost': trace['totalCost']
        } for trace in traces_data]

        return pd.DataFrame(traces_dicts) if traces_dicts else pd.DataFrame()


    def get_observations_for_trace_ids(trace_ids):
        observations_dfs = []
        
        for trace_id in trace_ids:
            params = {
                'traceId': trace_id,
            }
            observations_data = fetch_all_pages(f"{BASE_URL}/observations", headers, params)
            
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


    traces_df = get_traces(days_back=1)
    if False:
        scores_df = get_scores(days_back=1)

        if not traces_df.empty:
            trace_ids = traces_df['Id'].tolist()
            observations_df = get_observations_for_trace_ids(trace_ids)
        else:
            print("No traces found for yesterday.")
            observations_df = pd.DataFrame()  # Ensure observations_df is initialized

        res = {
            "scores_df":scores_df,
            "traces_df":traces_df,
            "observations_df":observations_df,
            #"io_config_profile_name":data['io_config_profile_name']
        }

        return res

@test
def test_output(output, *args) -> None:
    """
    Template code for testing the output of the block.
    """
    assert output is not None, 'The output is undefined'