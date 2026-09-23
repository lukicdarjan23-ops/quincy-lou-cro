"""Loads credentials from lead_research/.env. Values are never printed."""
import os

from dotenv import load_dotenv

_ENV = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env")
load_dotenv(_ENV)


def settings():
    return {
        "ICYPEAS_API_KEY": os.getenv("ICYPEAS_API_KEY", ""),
        "ICYPEAS_API_SECRET": os.getenv("ICYPEAS_API_SECRET", ""),
        "ICYPEAS_USER_ID": os.getenv("ICYPEAS_USER_ID", ""),
    }
