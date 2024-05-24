import streamlit as st
import time
import azure_connection
import base64
from streamlit_extras.stylable_container import stylable_container
from streamlit_extras.row import row
from streamlit_modal import Modal

from PIL import Image


# Streamlit UI------------------------------------------------------------------

def btn_callback():
    st.session_state.display_result=False

def encode_image(image_path):
    with open(image_path, "rb") as img_file:
        return base64.b64encode(img_file.read()).decode()
 
@st.experimental_dialog("Edit Gesture Mapping")
def edit_gesture_mapping(gesture):
    st.subheader(f"Gesture: {gesture}")
    object = st.selectbox("Select the Object to Control", ["Red Light", "Green Light", "Blue Light"])
    if object == "Red Light":
        virtualPin = 1
    elif object == "Green Light":
        virtualPin = 2
    elif object == "Blue Light":
        virtualPin = 3
    action = st.selectbox("Select the Action to Trigger", ["Turn On/Off"])
    if st.button("Save"):
        azure_connection.update_gesture_mapping(gesture, object, action, virtualPin)
        st.session_state.page = "home"
        st.rerun()
# Streamlit UI------------------------------------------------------------------


def display_home():
    # st.markdown(":orange[Test:]")
    # st.markdown(f":orange[{st.session_state.label}]")

    # if st.session_state.label != "":
    #     azure_connection.delete_blob("omnisurface-ml-data", f"{st.session_state.label}.json")
    #     st.session_state.label = ""
    #     st.session_state.count = 0
    #     azure_connection.update_env_variables(label="", data_count=0)
    #     st.rerun()

    bg_image_base64 = encode_image("img/background.png")

    st.markdown(f'''
        <style>
            [data-testid="stAppViewContainer"] > .main  {{
                background-image: url("data:image/png;base64,{bg_image_base64}");
                # background-color: black;
                background-size: 100% 100%;
                background-repeat: no-repeat;
                background-position: top center;
                background-attachment: local;
            }}
        </style>
        ''', unsafe_allow_html=True)
    
    st.markdown(
        """
        <style>
            div[data-testid="column"]:nth-of-type(2) 
            {
                text-align: end;
                min-width: 400px;
                max-width: 500px;
            } 
        </style>
        """,unsafe_allow_html=True
    )

    col1, col2 = st.columns(2)
    with col1:
        st.text(" ")
        st.text(" ")   
        st.text(" ") 
        st.text(" ")

        # title
        st.markdown('''
        <p style = "
        color: white;
;
        font-size: 60px;
        font-weight: bold;
        font-family: 'Inter', sans-serif;
        ">
        OmniSurface
        </p>
        ''', unsafe_allow_html=True)


        # subtitle
        st.markdown('''
        <p style = "
        color: white;
        font-size: 30px;
        font-family: 'Inter', sans-serif;
        ">
        Create Your Limitless Surface Console
        </p>
        ''', unsafe_allow_html=True)


        # text
        st.markdown('''
        <p style = "
        color: white;
        font-size: 20px;
        font-family: 'Inter', sans-serif;
        ">
        1 Gesture + 1 Applied Surface = Customized Remote Control
        </p>
        ''', unsafe_allow_html=True)

        st.text(" ")
        st.text(" ")
        st.text(" ")
        st.text(" ")

        if st.button("Train New Gesture"):
            st.session_state.page = "train_new_gesture"
            st.rerun()
    
    with col2:
        st.image("img/figure.png")


    st.text(" ")
    st.text(" ")
    st.text(" ")


    with stylable_container(
    key="gesture_list",
    css_styles='''
        {
            background-color: #FFFFFF;
            color: black;
            border-radius: 40px;
            padding: 30px 40px;
        }
        '''
    ):
        
        # header = row([1, 1], vertical_align="bottom")
        # header.subheader("Gesture List")
        # header.button("Refresh", key="refresh_gesture_list")
        st.subheader("Gesture List")

        st.markdown(
            """
            <style>
                div[data-testid="column"]:nth-of-type(2) 
                {
                    text-align: start;
                    min-width: 20px;
                } 
            </style>
            """,unsafe_allow_html=True
        )

        title1, title2, title3, title4 = st.columns([3,3,3,1])
        title1.write("**Gesture**")
        title2.write("**Object**")
        title3.write("**Action**")
        all_blobs = azure_connection.list_all_blobs("omnisurface-ml-data")

        for blob in all_blobs:
            gesture = blob.split(".")[0]
            entity = azure_connection.get_existing_entity("map", gesture)
            if entity == None:
                azure_connection.delete_blob("omnisurface-ml-data", f"{gesture}.json")
                st.session_state.count = 0
                st.session_state.label = ""
                azure_connection.update_env_variables(record_state=False,label="", data_count=0)
                st.rerun()
            else:
                try:
                    action = azure_connection.get_existing_entity("map", gesture)["Action"]
                    object = azure_connection.get_existing_entity("map", gesture)["Object"]
                except KeyError:
                    action = "Undefined"
                    object = "Undefined"

            col1, col2, col3, col4 = st.columns([3,3,3,1])
            col1.write(gesture)
            col2.write(object)
            col3.write(action)
            if col4.button("Edit", key=f"edit_{gesture}"):
                edit_gesture_mapping(gesture)

        st.text(" ")

def display_train_new_gesture():
    if st.button("Back", key="back_to_home"):
        st.session_state.page = "home"
        st.session_state.status = "not_started"
        st.session_state.label = ""
        st.session_state.count = 0
        azure_connection.update_env_variables(record_state=False,label="", data_count=0)
        st.rerun()

    st.title('Train New Gesture')
    
    label = st.text_input(
            "Gesture Name",
            label_visibility="visible",
            placeholder="Ex: Tap, Slap",
            value=st.session_state.label
        )
    st.markdown(''' 
                <style>
                div.stButton > button:first-child {
                    background-color: white;
                    color:black;
                    border: 1px solid black;
                }
                div.stButton > button:hover {
                    background-color:black;
                    color:white;
                    border: 1px solid black;
                }
                </style>
    ''', unsafe_allow_html=True)
    st.session_state.label = label

    if st.session_state.status == "not_started":
        # st.button("Start Recording Gesture", key = "start_recording_data", on_click=btn_callback)
        if st.button("Start Recording Gesture", key = "start_recording_data"):
            st.session_state.status = "training"
            st.session_state.new_data = True
            st.rerun()
    elif st.session_state.status == "training":
        if st.session_state.count < 10:
            if st.session_state.new_data:
                azure_connection.update_env_variables(record_state=True, label=st.session_state.label, data_count=0)
                st.session_state.count = azure_connection.get_env_variables()[2]
                st.markdown(f"**Recording Gesture (progress: {st.session_state.count}/10)**")
                st.caption("When the system detects your gesture, the red light will turn on. Repeat this process ten times.")
                st.session_state.new_data = False
            else:
                st.session_state.count = azure_connection.get_env_variables()[2]
                st.markdown(f"**Recording Gesture (progress: {st.session_state.count}/10)**")
                st.caption("When the system detects your gesture, the red light will turn on. Repeat this process ten times.")
        
        # if st.session_state.count < 10:
            # st.session_state.count = get_env_variables()[2]
            time.sleep(1)
            st.rerun()
        else:
            st.markdown("**Gesture recorded successfully!**")
            azure_connection.update_env_variables(record_state=False,data_count=st.session_state.count)
            if st.button("Start Training", key = 'start_training'):
                with st.spinner("Training model..."):
                    st.session_state.training_result = azure_connection.call_train_model_function()
                    entity=azure_connection.get_or_create_entity("map", st.session_state.label)
                    azure_connection.upsert_entity(entity)
                    st.session_state.status = "finished"
                    st.rerun()
                    
    elif st.session_state.status == "finished":
        st.subheader(st.session_state.training_result)
        # edit_gesture_mapping(label)
        object = st.selectbox("Select the Object to Control", ["Red Light", "Green Light", "Blue Light"])
        if object == "Red Light":
            virtualPin = 1
        elif object == "Green Light":
            virtualPin = 2
        elif object == "Blue Light":
            virtualPin = 3
        action = st.selectbox("Select the Action to Trigger", ["Turn On/Off"])
        if st.button("Save", type="primary"):
            azure_connection.update_gesture_mapping(label, object, action, virtualPin)
            azure_connection.update_env_variables(record_state=False,label="", data_count=0)
            st.session_state.page = "home"
            st.session_state.status = "not_started"
            st.session_state.label = ""
            st.session_state.count = 0
            st.rerun()

        if st.button("Skip and Return Home", key='return_home'):
            azure_connection.update_env_variables(record_state=False,label="", data_count=0)
            st.session_state.page = "home"
            st.session_state.status = "not_started"
            st.session_state.label = ""
            st.session_state.count = 0
            st.rerun()


def main():
    st.set_page_config(
        page_title="OmniSurface",
        page_icon="🫳",
        layout="wide"
    )

    # button
    if 'status' not in st.session_state:
        st.session_state.status = "not_started"

    # 初始化 Session State
    if 'page' not in st.session_state:
        st.session_state.page = "home"
    if 'label' not in st.session_state:
        st.session_state.label = ""
    if 'count' not in st.session_state:
        st.session_state.count = 0
    if 'new_data' not in st.session_state:
        st.session_state.new_data = True
    if 'training_result' not in st.session_state:
        st.session_state.training_result = ""


    if st.session_state.page == "home":
        display_home()
    elif st.session_state.page == "train_new_gesture":
        display_train_new_gesture()
    

        


if __name__ == "__main__":
    main()

