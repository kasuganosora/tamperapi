import os

DB_HOST = os.environ.get("DB_HOST", "")
DB_PORT = os.environ.get("DB_PORT", "10123")
DB_USER = os.environ.get("DB_USER", "root")
DB_PASSWORD = os.environ.get("DB_PASSWORD", "")
DB_NAME = os.environ.get("DB_NAME", "")
API_PASSWORD = os.environ.get("API_PASSWORD", "")
COS_SECRET_ID = os.environ.get("COS_SECRET_ID", "")
COS_SECRET_KEY = os.environ.get('COS_SECRET_KEY',"")
COS_REGION = os.environ.get("COS_REGION", "ap-guangzhou")
COS_BUCKET = os.environ.get("COS_BUCKET", "")