# # from fastapi import FastAPI, Form
# # import boto3
# # import os
# # import uuid
# # import shutil
# # from llm_agent.agents.rag_agent import run_content_generation
# # from dotenv import load_dotenv

# # load_dotenv()

# # app = FastAPI()

# # def download_pdf_from_s3(bucket_name, object_key, destination_path):
# #     s3 = boto3.client("s3", region_name=os.getenv("AWS_REGION_DEFAULT"))
# #     s3.download_file(bucket_name, object_key, destination_path)

# # @app.post("/generate_small")
# # async def generate_document(
# #     bucket_name: str = Form(...),
# #     object_key: str = Form(...),
# #     document_type: str = Form(...),
# #     user_query: str = Form(...),
# #     additional_info: str = Form("")
# # ):
# #     session_id = uuid.uuid4().hex
# #     temp_dir = f"temp_uploads/{session_id}"
# #     os.makedirs(temp_dir, exist_ok=True)

# #     file_name = object_key.split("/")[-1]
# #     file_path = os.path.join(temp_dir, file_name)

# #     try:
# #         download_pdf_from_s3(bucket_name, object_key, file_path)

# #         response = run_content_generation(
# #             file_path=file_path,
# #             document_type=document_type,
# #             user_query=user_query,
# #             additional_info=additional_info,
# #             session_id=session_id
# #         )

# #         return response

# #     finally:
# #         if os.path.exists(temp_dir):
# #             shutil.rmtree(temp_dir, ignore_errors=True)

# from fastapi import FastAPI, Form
# import boto3
# import os
# import uuid
# import shutil
# import json
# from collections import defaultdict
# from llm_agent.agents.rag_agent import run_content_generation
# from dotenv import load_dotenv

# load_dotenv()

# app = FastAPI()

# DATA_FILE = "doc_type_counts.json"

# def download_pdf_from_s3(bucket_name, object_key, destination_path):
#     s3 = boto3.client("s3", region_name=os.getenv("AWS_REGION_DEFAULT"))
#     s3.download_file(bucket_name, object_key, destination_path)

# def update_doc_type_count(document_type: str):
#     """Increment count of document_type in a persistent JSON file."""
#     try:
#         if os.path.exists(DATA_FILE):
#             with open(DATA_FILE, "r") as f:
#                 counts = defaultdict(int, json.load(f))
#         else:
#             counts = defaultdict(int)

#         counts[document_type] += 1

#         with open(DATA_FILE, "w") as f:
#             json.dump(counts, f)
#     except Exception as e:
#         print(f"Warning: Failed to update document type count: {e}")

# @app.post("/generate_small")
# async def generate_document(
#     bucket_name: str = Form(...),
#     object_key: str = Form(...),
#     document_type: str = Form(...),
#     user_query: str = Form(...),
#     additional_info: str = Form("")
# ):
#     session_id = uuid.uuid4().hex
#     temp_dir = f"temp_uploads/{session_id}"
#     os.makedirs(temp_dir, exist_ok=True)

#     file_name = object_key.split("/")[-1]
#     file_path = os.path.join(temp_dir, file_name)

#     try:
#         # ✅ Track document type
#         update_doc_type_count(document_type)

#         # Download and process
#         download_pdf_from_s3(bucket_name, object_key, file_path)

#         response = run_content_generation(
#             file_path=file_path,
#             document_type=document_type,
#             user_query=user_query,
#             additional_info=additional_info,
#             session_id=session_id
#         )

#         return response

#     finally:
#         if os.path.exists(temp_dir):
#             shutil.rmtree(temp_dir, ignore_errors=True)


from fastapi import FastAPI, Form
import boto3
import os
import uuid
import shutil
from botocore.exceptions import ClientError
from llm_agent.agents.rag_agent import run_content_generation
from dotenv import load_dotenv

load_dotenv()

app = FastAPI()

# Constants
DDB_TABLE_NAME = "DocumentTypeCounts"
AWS_REGION = os.getenv("AWS_REGION_DEFAULT")
BUCKET_NAME = os.getenv("BUCKET_NAME")

# Clients
dynamodb = boto3.resource("dynamodb", region_name=AWS_REGION)
ddb_client = boto3.client("dynamodb", region_name=AWS_REGION)

def ensure_ddb_table_exists():
    """Create the DynamoDB table if it doesn't exist."""
    try:
        ddb_client.describe_table(TableName=DDB_TABLE_NAME)
    except ddb_client.exceptions.ResourceNotFoundException:
        print(f"Table {DDB_TABLE_NAME} not found. Creating...")
        dynamodb.create_table(
            TableName=DDB_TABLE_NAME,
            KeySchema=[
                {"AttributeName": "document_type", "KeyType": "HASH"}
            ],
            AttributeDefinitions=[
                {"AttributeName": "document_type", "AttributeType": "S"}
            ],
            BillingMode="PAY_PER_REQUEST"
        )
        # Wait for the table to be active
        waiter = ddb_client.get_waiter("table_exists")
        waiter.wait(TableName=DDB_TABLE_NAME)
        print(f"Table {DDB_TABLE_NAME} created.")

def update_doc_type_count(document_type: str):
    """Increment document type count in DynamoDB."""
    ensure_ddb_table_exists()
    table = dynamodb.Table(DDB_TABLE_NAME)
    try:
        table.update_item(
            Key={"document_type": document_type},
            UpdateExpression="ADD #c :inc",
            ExpressionAttributeNames={"#c": "count"},
            ExpressionAttributeValues={":inc": 1}
        )
    except ClientError as e:
        print(f"Error updating document count: {e}")

def download_pdf_from_s3(bucket_name, object_key, destination_path):
    s3 = boto3.client("s3", region_name=AWS_REGION)
    s3.download_file(bucket_name, object_key, destination_path)

@app.post("/generate_small")
async def generate_document(
    bucket_name: str = Form(...),
    object_key: str = Form(...),
    document_type: str = Form(...),
    user_query: str = Form(...),
    additional_info: str = Form("")
):
    session_id = uuid.uuid4().hex
    temp_dir = f"temp_uploads/{session_id}"
    os.makedirs(temp_dir, exist_ok=True)

    file_name = object_key.split("/")[-1]
    file_path = os.path.join(temp_dir, file_name)

    try:
        # ✅ Track document type in DynamoDB
        update_doc_type_count(document_type)

        # Download and process
        download_pdf_from_s3(bucket_name, object_key, file_path)

        response = run_content_generation(
            file_path=file_path,
            document_type=document_type,
            user_query=user_query,
            additional_info=additional_info,
            session_id=session_id
        )

        return response

    finally:
        if os.path.exists(temp_dir):
            shutil.rmtree(temp_dir, ignore_errors=True)
