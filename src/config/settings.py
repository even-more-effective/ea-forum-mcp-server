import os
from typing import Optional
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


class Settings:
    # Server settings
    MCP_SERVER_NAME: str = os.getenv("MCP_SERVER_NAME", "ea-forum-mcp")
    MCP_SERVER_VERSION: str = os.getenv("MCP_SERVER_VERSION", "0.1.0")

    # API settings
    EA_FORUM_API_BASE_URL: str = os.getenv(
        "EA_FORUM_API_BASE_URL", "https://forum.effectivealtruism.org"
    )
    EA_FORUM_GRAPHQL_ENDPOINT: str = os.getenv(
        "EA_FORUM_GRAPHQL_ENDPOINT", "https://forum.effectivealtruism.org/graphql"
    )
    EA_FORUM_SEARCH_ENDPOINT: str = os.getenv(
        "EA_FORUM_SEARCH_ENDPOINT", "https://forum.effectivealtruism.org/api/search"
    )

    # Cache settings
    CACHE_TTL_SECONDS: int = int(os.getenv("CACHE_TTL_SECONDS", "3600"))
    CACHE_MAX_SIZE: int = int(os.getenv("CACHE_MAX_SIZE", "100"))

    # Request settings
    REQUEST_TIMEOUT_SECONDS: int = int(os.getenv("REQUEST_TIMEOUT_SECONDS", "30"))
    MAX_RETRIES: int = int(os.getenv("MAX_RETRIES", "3"))
    RETRY_DELAY_SECONDS: float = float(os.getenv("RETRY_DELAY_SECONDS", "1.0"))

    # Logging settings
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")

    # Known tag IDs for common topics
    KNOWN_TAGS = {
        "ai_safety": {"id": "oNiQsBHA3i837sySD", "name": "AI safety"},
        "community": {"id": "ZCihBFp5P64JCvQY6", "name": "Community"},
        "global_health": {
            "id": "sWcuTyTB5dP3nas2t",
            "name": "Global health & development",
        },
        "biosecurity": {"id": "H43gvLzBCacxxamPe", "name": "Biosecurity"},
        "career_choice": {"id": "4CH9vsvzyk4mSKwyZ", "name": "Career choice"},
        "policy": {"id": "of9xBvR3wpbp6qsZC", "name": "Policy"},
        "funding": {"id": "be4pBryMKxLhkmgvE", "name": "Funding opportunities"},
        "malaria": {"id": "cgjMFtsn3AKLDWCWq", "name": "Malaria"},
        "research": {"id": "hxRMaKvwGqPb43TWB", "name": "Research"},
        "vaccines": {"id": "rSF94ws2yqcpecHNn", "name": "Vaccines"},
    }


settings = Settings()