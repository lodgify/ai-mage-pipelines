import os

DAYS_BACK = 1


_CONFIG_MAPPER = {
    "live": {
        "secret_name": "langfuse_ai_assistant_live_credentials",
        "io_config_profile_name": "ai_assistant_internal_platform_live_readwrite",
    },
    "integration": {
        "secret_name": "langfuse_ai_assistant_live_credentials",
        "io_config_profile_name": "ai_assistant_internal_platform_integration_readwrite",
    },
}


def get_config_mapper() -> dict[str, str]:
    if os.getenv("ENV") == "live":
        return _CONFIG_MAPPER["live"]
    return _CONFIG_MAPPER["integration"]
