from streamlit_config_helper import set_streamlit_page_config_once

# set_streamlit_page_config_once()

from auth_helper import get_auth_status
import streamlit as st
import parameters_functions
import chatpage_template


st.set_page_config(layout="wide")

st.session_state["activities"] = parameters_functions.getAssistants()

st.write("# Activity chat")

activityContainer = st.container()
with activityContainer:
    if "selected activity" not in st.session_state or st.session_state["selected activity"]=="":
        st.write("### Select the activity you want to do on the left")
    else :
        assistant = st.session_state["activities"][st.session_state["selected activity"]]
        chatpage_template.load_template(
            activity_id=assistant["id"], 
            assistant_id=assistant["id"], 
            title=assistant["name"]
        )
        
with st.sidebar:
    activityExpander = st.expander("📝 Activities")
    with activityExpander:
        for id in st.session_state["activities"]:
            if st.button(st.session_state["activities"][id]["name"], use_container_width=True) and get_auth_status():
                st.session_state["selected activity"] = id
                    

