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

# Azure connection setup using environment variable
connection_string = os.getenv("AZURE_CONNECTION_STRING")
try:
    table_service = TableServiceClient.from_connection_string(conn_str=connection_string)
except Exception as e:
    st.error(f"Error connecting to Azure Table Storage: {e}")

# Define the single table name
table_name = "Tablel"

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
            "State": "False",
            "GestureLabel": '',
            "DataCount": 0 if partition_key == "EnvironmentVariable" else 'null',
            "Object": 'null',
            "Action": 'null'
        }
    return entity

def update_env_variables(state, label, data_count):
    """Update environment variables."""
    row_key = get_fixed_row_key("EnvironmentVariable")
    entity = get_or_create_entity("EnvironmentVariable", row_key)
    entity['State'] = "True" if state else "False"
    entity['GestureLabel'] = label
    entity['DataCount'] = data_count
    upsert_entity(entity)
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

# Initialize the navigation state
if 'current_page' not in st.session_state:
    st.session_state['current_page'] = "Home"

if 'table_created' not in st.session_state:
    st.session_state['table_created'] = False

if 'show_train_model_button' not in st.session_state:
    st.session_state['show_train_model_button'] = False

if 'train_message' not in st.session_state:
    st.session_state['train_message'] = ""

# Function to change pages
def navigate_to(page):
    st.session_state['current_page'] = page
    st.rerun()

# Sidebar navigation for non-home pages
def sidebar_navigation():
    page = st.sidebar.radio(
        "Menu",
        ["Environment Variable", "Map"],
        index=["Environment Variable", "Map"].index(st.session_state['current_page']),
        key="sidebar_page"
    )
    if page != st.session_state['current_page']:
        navigate_to(page)

if st.session_state['current_page'] != "Home":
    sidebar_navigation()

# Check current page and render appropriate UI
if st.session_state['current_page'] == "Home":
    st.title("Welcome to Gesture Control Panel")
    st.write("Choose an option to start:")

    if st.button("Get to Start"):
        if not st.session_state['table_created']:
            if create_table(table_name):
                st.session_state['table_created'] = True
        navigate_to("Environment Variable")

    if st.button("Personal Command"):
        if not st.session_state['table_created']:
            if create_table(table_name):
                st.session_state['table_created'] = True
        navigate_to("Map")

elif st.session_state['current_page'] == "Environment Variable":
    st.title('Environment Variable')

    # Retrieve or create the entity
    row_key = get_fixed_row_key("EnvironmentVariable")
    entity = get_or_create_entity("EnvironmentVariable", row_key)

    # "New Data Collection" button
    if st.button("New Data Collection"):
        entity = update_env_variables(False, "", 0)
        st.session_state['show_train_model_button'] = False

    # Conditional fields
    gesture_label = st.selectbox("GestureLabel", ("", "fist", "single-finger", "tap"))
    entity['GestureLabel'] = gesture_label
    entity['Object'] = 'null'
    entity['Action'] = 'null'

    # Record Button
    if st.button("Record"):
        entity = update_env_variables(True, gesture_label, 0)

        # Simulate data collection and update the count
        collected_count = collect_gesture_data(gesture_label)
        entity = update_env_variables(True, gesture_label, collected_count)

        # Show success message with count
        st.success(f"Data collection successful! Collected {collected_count} gestures.")

    if st.button("Finish"):
        entity = update_env_variables(False, "", 0)  # Reset environment variables after collection
        st.session_state['show_train_model_button'] = True

    if st.session_state['show_train_model_button']:
        if st.button("Train Model"):
            st.session_state['train_message'] = call_train_model_function()
            st.write(st.session_state['train_message'])

    st.write(f"Current State: {entity['State']}")

    # Return to Home button
    if st.button('Return to Home'):
        navigate_to("Home")

elif st.session_state['current_page'] == "Map":
    st.title('Map')

    # Conditional fields
    gesture_label = st.selectbox("GestureLabel", ("", "fist", "single-finger", "tap"))
    object_value = st.selectbox("Object", ("Lamp", "Speaker", "TV", "Fan", "Other"))
    if object_value == "Other":
        object_value = st.text_input("Specify Other Object", key="map_object")
    action = st.selectbox("Action", ("Open", "Close", "TurnUp", "TurnDown", "Brighten", "Dark"))

    # Retrieve or create the map entity
    entity = get_or_create_map_entity(gesture_label)
    entity['GestureLabel'] = gesture_label
    entity['State'] = 'null'
    entity['Object'] = object_value if object_value is not None else entity.get('Object', 'null')
    entity['Action'] = action if action is not None else entity.get('Action', 'null')

    # Upsert entity button
    if st.button('Upsert Entity'):
        upsert_entity(entity)

    # Return to Home button
    if st.button('Return to Home'):
        navigate_to("Home")