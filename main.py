from fastapi import FastAPI, Form, HTTPException
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

# Document types handled as "small"
SMALL_DOC_TYPES = [
    "elevator pitch",
    "pitch deck",
    "sales pitch",
    "brochure",
    "one pager",
    "industry brochure"
]

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

async def handle_generation(bucket_name, object_key, document_type, user_query, additional_info, session_id):
    temp_dir = f"temp_uploads/{session_id}"
    os.makedirs(temp_dir, exist_ok=True)
    file_name = object_key.split("/")[-1]
    file_path = os.path.join(temp_dir, file_name)

    try:
        update_doc_type_count(document_type)
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

@app.post("/generate_small")
async def generate_small(
    bucket_name: str = Form(...),
    object_key: str = Form(...),
    document_type: str = Form(...),
    user_query: str = Form(...),
    additional_info: str = Form("")
):
    session_id = uuid.uuid4().hex
    print(f"Triggered /generate_small for: {document_type}")
    return await handle_generation(
        bucket_name, object_key, document_type, user_query, additional_info, session_id
    )

@app.post("/generate_big")
async def generate_big(
    bucket_name: str = Form(...),
    object_key: str = Form(...),
    document_type: str = Form(...),
    user_query: str = Form(...),
    additional_info: str = Form("")
):
    session_id = uuid.uuid4().hex
    print(f"Triggered /generate_big for: {document_type}")
    return await handle_generation(
        bucket_name, object_key, document_type, user_query, additional_info, session_id
    )

@app.post("/generate")
async def generate(
    bucket_name: str = Form(...),
    object_key: str = Form(...),
    document_type: str = Form(...),
    user_query: str = Form(...),
    additional_info: str = Form("")
):
    if document_type in SMALL_DOC_TYPES:
        return await generate_small(
            bucket_name=bucket_name,
            object_key=object_key,
            document_type=document_type,
            user_query=user_query,
            additional_info=additional_info
        )
    else:
        return await generate_big(
            bucket_name=bucket_name,
            object_key=object_key,
            document_type=document_type,
            user_query=user_query,
            additional_info=additional_info
        )
