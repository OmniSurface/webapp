import streamlit as st
import time
import azure_connection
import base64
from streamlit_extras.stylable_container import stylable_container
from PIL import Image


# Streamlit UI------------------------------------------------------------------

def btn_callback():
    st.session_state.display_result=False


# Streamlit UI------------------------------------------------------------------


def display_home():
    # with stylable_container(
    #     key="intro",
    #     css_styles='''
    #         {
    #             background-color: #D8D8D8;
    #             background-image: url("data:img/background.png");
    #             background-size: 100vw 100vh;
    #             # color: black;
    #         }'''
    # ):
    #     st.title("OmniSurface")
    #     if st.button("Train New Gesture"):
    #         st.session_state.page = "train_new_gesture"
    #         st.rerun()

    # bg_image_base64 = encode_image("img/background.jpg")

        
    # st.markdown('''
    #             <style>
    #                 [data-testid="stAppViewContainer"] > .main  {
    #                     # background-color: #D8D8D8;
    #                     background-image: url("data:image/jpg;base64,{bg_image_base64}");

    #                     background-size: 100%, 50%;
    #                 }
    #             </style>
    #         ''', unsafe_allow_html=True)

    
    st.title("OmniSurface")
    st.markdown("**Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat...**")
    st.text(" ")
    st.text(" ")
    st.text(" ")
    st.text(" ")
    st.text(" ")

    if st.button("Train New Gesture"):
        st.session_state.page = "train_new_gesture"
        st.rerun()

def display_train_new_gesture():

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

    if st.session_state.status == "not_started":
        # st.button("Start Recording Gesture", key = "start_recording_data", on_click=btn_callback)
        if st.button("Start Recording Gesture", key = "start_recording_data"):
            st.session_state.status = "training"
            st.rerun()
    elif st.session_state.status == "training":
        if st.session_state.count < 10:
            if st.session_state.new_data:
                azure_connection.update_env_variables(record_state=True, label=label, data_count=0)
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
                    st.session_state.status = "finished"
                    st.rerun()
                    
    elif st.session_state.status == "finished":
        st.subheader(st.session_state.training_result)

        if st.button("Return Home", key='return_home'):
            st.session_state.page = "home"
            st.rerun()


def main():
    st.set_page_config(
        page_title="OmniSurface",
        page_icon="🫳"
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

