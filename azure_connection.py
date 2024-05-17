import os
import streamlit as st
from azure.data.tables import TableServiceClient
import time
import glob
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Define the single table name
table_name = "envVariables"


# Azure connection---------------------------------------------------------------
# Azure connection setup using environment variable
connection_string = os.getenv("AZURE_STORAGE_CONNECTION_STRING")
try:
    table_service = TableServiceClient.from_connection_string(conn_str=connection_string)
except Exception as e:
    st.error(f"Error connecting to Azure Table Storage: {e}")

def get_env_variables():
    connection_string = os.getenv("AZURE_STORAGE_CONNECTION_STRING")
    table_service_client = TableServiceClient.from_connection_string(connection_string)
    table_client = table_service_client.get_table_client(table_name)
    try:
        entity = table_client.get_entity(partition_key="enviroment", row_key="variables")
        return entity['Flag'], entity.get('current_label', 'default_label'), entity.get('data_count', 0)
    except Exception as e:
        print("Error reading state:", e)
        return None, None  # return None if there is an error

def update_env_variables(record_state=None, label=None, data_count=None, action=None, object=None):
    connection_string = os.getenv("AZURE_STORAGE_CONNECTION_STRING")
    table_service_client = TableServiceClient.from_connection_string(connection_string)
    table_client = table_service_client.get_table_client(table_name)
    # entity = {
    #     "PartitionKey": "EnvironmentVariable",
    #     "RowKey": "variables",
    #     "Flag": record_state,
    #     "current_label": label,
    #     "data_count": data_count,
    #     "Object": object,
    #     "Action": action
    # }
    
    # 获取现有实体
    entity = table_client.get_entity(partition_key="enviroment", row_key="variables")
    
    # 更新实体字段，如果相应的输入参数不为 None
    if record_state is not None:
        entity["Flag"] = record_state
    if label is not None:
        entity["current_label"] = label
    if data_count is not None:
        entity["data_count"] = data_count
    if action is not None:
        entity["Action"] = action
    if object is not None:
        entity["Object"] = object
    
    table_client.upsert_entity(entity)    


def create_table(table_name):
    """Create a new table in Azure Table Storage if it does not exist."""
    try:
        table_service.create_table_if_not_exists(table_name=table_name)
        st.success(f"Table {table_name} created successfully!")
        return True
    except Exception as e:
        st.error(f"Error creating table: {e}")
        return False

def get_or_create_entity(partition_key, row_key):
    """Get an existing entity or create a new one if it doesn't exist."""
    try:
        table_client = table_service.get_table_client(table_name=table_name)
        entity = table_client.get_entity(partition_key=partition_key, row_key=row_key)
    except Exception:
        entity = {
            "PartitionKey": partition_key,
            "RowKey": row_key,
            "Timestamp": time.strftime("%y-%m-%d-%H-%M-%S"),
            "Flag": "False",
            "current_label": '',
            "data_count": 0 if partition_key == "EnvironmentVariable" else 'null',
            "Object": 'null',
            "Action": 'null'
        }
    return entity


def increment_data_count(entity, partition_key):
    """Increment the DataCount of an existing entity only for `EnvironmentVariable` partition."""
    if partition_key == "EnvironmentVariable":
        entity['DataCount'] = entity.get('DataCount', 0) + 1
    return entity

def upsert_entity(entity):
    """Insert or merge an entity into the given table."""
    try:
        table_client = table_service.get_table_client(table_name=table_name)
        table_client.upsert_entity(entity)
        return True
    except Exception as e:
        st.error(f"Failed to upsert entity: {e}")
        return False

def toggle_state(entity):
    """Toggle the state between 'True' and 'False'."""
    current_state = entity.get("State", "False")
    entity["State"] = "True" if current_state == "False" else "False"
    return entity

def get_fixed_row_key(partition_key):
    """Generate a fixed RowKey for the `Environment Variable` partition."""
    if partition_key == "EnvironmentVariable":
        return "variables"
    else:
        return f"Unknown{1}"

def get_map_row_key_by_gesture(gesture_label):
    """Generate a RowKey for the Map partition based on the gesture label."""
    return f"{gesture_label}"

def get_or_create_map_entity(gesture_label):
    """Get an existing entity or create a new one if it doesn't exist in the `Map` partition."""
    row_key = get_map_row_key_by_gesture(gesture_label)
    return get_or_create_entity("Map", row_key)

# Simulate data collection from files
def collect_gesture_data(gesture):
    """Simulate collecting gesture data from files."""
    count = 0
    for file in glob.glob(f"data/combined_new/{gesture}/*.txt"):
        count += 1
    return count

# Function to call the training model function
def call_train_model_function():
    """Call the train_model function and return the result."""
    url = "https://omnisurface.azurewebsites.net/api/train_model?"

    # Setup a retry mechanism for HTTP requests
    session = requests.Session()
    retry = Retry(total=3, backoff_factor=1, status_forcelist=[502, 503, 504])
    adapter = HTTPAdapter(max_retries=retry)
    session.mount("http://", adapter)

    try:
        response = session.post(url)
        if response.status_code == 200:
            return f"Training successful! Accuracy: {response.text}"
        else:
            return f"Training failed: {response.status_code} {response.text}"
    except requests.exceptions.RequestException as e:
        return f"Training failed: {e}"
# Azure connection---------------------------------------------------------------
