from dotenv import load_dotenv

load_dotenv()
import os

from grist_api import GristDocAPI

api = GristDocAPI(
    os.getenv("GRIST_DOC_ID"),
    api_key=os.getenv("GRIST_API_KEY"),
    server=os.getenv("GRIST_SERVER"),
)
