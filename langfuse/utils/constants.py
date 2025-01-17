from mage_ai.settings.repo import get_repo_path
from os import path
import os
import dotenv

dotenv.load_dotenv()

days_back = 1

# getting local_project_name for local script testing
repo_path = path.join(get_repo_path(), os.environ.get("local_project_name", ""))

config_mapper = {
    #"ai_assistant_internal_platform_live"
    #    "secret_name":"langfuse_ai_assistant_live_credentials",
    #    "io_config_profile_name":"ai_assistant_internal_platform_live_readwrite",
    # "ai_assistant_internal_platform_integration"
    "secret_name":"langfuse_ai_assistant_live_credentials",
    "io_config_profile_name":"ai_assistant_internal_platform_integration_readwrite",
    #"ai_tools_platform_live"
    #    "secret_name":"langfuse_ai_tools_live_credentials",
    #    "io_config_profile_name":"ai_tools_platform_live_readwrite",
    # "ai_tools_platform_integration"
    #     "secret_name":"langfuse_ai_tools_integration_credentials",
    #     "io_config_profile_name":"ai_tools_platform_integration_readwrite",
}