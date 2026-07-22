"""API Key authentication module.

Provides FastAPI dependency for validating X-API-Key headers
against a list of valid keys stored in environment variables.
"""

import logging
import os
from typing import Optional

from fastapi import Header, HTTPException, status
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)


def get_valid_api_keys() -> set[str]:
    """Load valid API keys from environment variable.
    
    Reads API_KEYS environment variable (comma-separated) and returns
    a set of valid keys for O(1) lookup.
    
    Returns:
        Set of valid API key strings
    """
    api_keys_env = os.getenv("API_KEYS", "")
    if not api_keys_env:
        logger.warning("[API_KEY] No API_KEYS environment variable set")
        return set()
    
    # Split by comma and strip whitespace, filter out empty strings
    keys = {key.strip() for key in api_keys_env.split(",") if key.strip()}
    return keys


def require_api_key(x_api_key: Optional[str] = Header(None)) -> str:
    """FastAPI dependency to validate API key.
    
    Validates the X-API-Key HTTP header against configured valid keys.
    Returns the API key if valid, raises HTTPException otherwise.
    
    Args:
        x_api_key: The API key from X-API-Key header
        
    Returns:
        The validated API key string
        
    Raises:
        HTTPException: 401 if API key is missing or invalid
    """
    valid_keys = get_valid_api_keys()
    
    # Check if API key is provided
    if not x_api_key:
        logger.warning("[API_KEY] Request without API key")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="API key required",
            headers={"WWW-Authenticate": "ApiKey"},
        )
    
    # Validate API key
    if x_api_key not in valid_keys:
        # Log a truncated version for debugging (security best practice)
        truncated_key = x_api_key[:10] + "..." if len(x_api_key) > 8 else x_api_key
        logger.warning(f"[API_KEY] Invalid API key: {truncated_key}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key",
            headers={"WWW-Authenticate": "ApiKey"},
        )
    
    logger.debug(f"[API_KEY] Valid API key authenticated")
    return x_api_key
