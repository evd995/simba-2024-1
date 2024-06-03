from openai import OpenAI
import streamlit as st

openai_client = OpenAI()

def getAssistants():
    
    assistantslist = openai_client.beta.assistants.list()
    assistants = {}

    for a in assistantslist :
        newassistant = {}

        newassistant["id"] = a.id
        newassistant["name"] = a.name
        newassistant["model"] = a.model
        newassistant["description"] = a.description
        newassistant["instructions"] = a.instructions
        newassistant["metadata"] = a.metadata

        assistants[a.id] = newassistant

    return assistants

def setSelectedid(i):
    st.session_state["selectedID"] = i

@st.experimental_dialog("Edit the assistant's description")
def descrEdit():
    assistant = st.session_state["assistants"][st.session_state["selectedID"]]
    st.write()
    if assistant["description"] != None:
        newdesc = st.text_input("Modify the description or enter a new one", value = assistant["description"], placeholder = "New description...")
    else :
        newdesc = st.text_input("Modify the description or enter a new one", value = "", placeholder = "New description...")

    if newdesc :
        openai_client.beta.assistants.update(assistant["id"], description=newdesc)
        st.session_state["assistants"] = getAssistants()
        st.rerun()
    
    if st.button("Submit"):
        openai_client.beta.assistants.update(assistant["id"], description=newdesc)
        st.session_state["assistants"] = getAssistants()
        st.rerun()

