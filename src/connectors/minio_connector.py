import os
from pathlib import Path

import boto3
from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parents[2]
ENV_PATH = PROJECT_ROOT / ".env"

load_dotenv(ENV_PATH)


def get_minio_client():
    conn = boto3.client(
        "s3",
        endpoint_url=os.getenv("MINIO_ENDPOINT"),
        aws_access_key_id=os.getenv("MINIO_ACCESS_KEY"),
        aws_secret_access_key=os.getenv("MINIO_SECRET_KEY"),
        region_name="us-east-1",
    )

    return conn

def ensure_bucket_exists():
    client = get_minio_client()
    bucket_name = os.getenv("MINIO_BUCKET")

    existing_buckets = {
        bucket["Name"]
        for bucket in client.list_buckets()["Buckets"]
    }

    if bucket_name not in existing_buckets:
        client.create_bucket(Bucket=bucket_name)
        print(f"MinIO bucket created: {bucket_name}")
    else:
        print(f"MinIO bucket already exists: {bucket_name}")

    return bucket_name

def upload_file_to_minio(local_path, object_key):
    client = get_minio_client()
    bucket_name = os.getenv("MINIO_BUCKET")

    client.upload_file(
        local_path,
        bucket_name,
        object_key
    )

    return object_key

def object_exists(object_key):
    client = get_minio_client()
    bucket_name = os.getenv("MINIO_BUCKET")

    client.head_object(
        Bucket=bucket_name,
        Key=object_key,
    )

    return True

def download_file_from_minio(object_key, local_path):
    client = get_minio_client()
    bucket_name = os.getenv("MINIO_BUCKET")

    client.download_file(
        bucket_name,
        object_key,
        local_path,
    )

    return local_path