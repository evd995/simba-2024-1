from openai import OpenAI
import streamlit as st
from langchain_core.prompts import PromptTemplate

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

@st.experimental_dialog("Edit the activity's name")
def chgName(assistant):

    newname = st.text_input("Enter the activity's new name", value = assistant["name"], placeholder = "New name...")

    if newname :
        openai_client.beta.assistants.update(assistant["id"], name=newname)
        st.session_state["assistants"] = getAssistants()
        st.rerun()

    col1,col2 = st.columns([.5,1])
    with col1:
        if st.button("Cancel"):
            st.rerun()
    with col2:
        if st.button("Submit"):
            openai_client.beta.assistants.update(assistant["id"], name=newname)
            st.session_state["assistants"] = getAssistants()
            st.rerun()

@st.experimental_dialog("Edit the activity's description")
def descrEdit(assistant):

    if assistant["description"] != None:
        newdesc = st.text_input("Modify the description or enter a new one", value = assistant["description"], placeholder = "New description...")
    else :
        newdesc = st.text_input("Modify the description or enter a new one", value = "", placeholder = "New description...")

    if newdesc :
        openai_client.beta.assistants.update(assistant["id"], description=newdesc)
        st.session_state["assistants"] = getAssistants()
        st.rerun()
    

    col1,col2 = st.columns([.5,1])
    with col1:
        if st.button("Cancel"):
            st.rerun()
    with col2:
        if st.button("Submit"):
            openai_client.beta.assistants.update(assistant["id"], description=newdesc)
            st.session_state["assistants"] = getAssistants()
            st.rerun()

#Modifying the main prompt :

full_template ="""You are a {adj1} {teaching_adj} tutor for the course '{courseName}'.
    Your name is SIMBA 😸 (Sistema Inteligente de Medición, Bienestar y Apoyo) and you were created by the Núcleo Milenio de Educación Superior.
    Respond in a {adj1}, concise and proactive way, {emojis}.
    Help the student answer the following questions:
    {questions}
    {answers} {teaching_type}
    {documents}
    Your first message should begin with ‘Hello! 😸 This week I will help you reflect on the following questions: ’ Followed by the questions to answer.
    {limits}"""


@st.experimental_dialog("Edit the assistant's instructions for the activity")
def chgPrompt(assistant):

    newprompt = PromptTemplate.from_template(full_template)

    courseName = st.text_input("what is the name of the course ?", value=assistant["name"])

    limit = st.number_input("include a word count limit ? (0 = no limit)", min_value=0, value=0)

    adj1 = st.selectbox("What attitude should the assistant have toward the students ?", ("friendly","informal","formal"))

    teachtype = st.selectbox("What shloud be the assistant's approach to teaching ?", ("socratic","other"))

    mentiondocuments = st.checkbox("do you want the assistant to encourage the student to rely on the provided documents for answering ?")
    if mentiondocuments:
        url = st.text_input("Is there an URL where to find those documents ?", value="", placeholder="leave empty if you have no url")
    else :
        url = ""
    

    
    col1,col2 = st.columns([.5,1])
    with col1:
        if st.button("Cancel"):
            st.rerun()
    with col2:
        if st.button("Submit"):
            openai_client.beta.assistants.update(assistant["id"], instructions=newprompt.format(
                courseName=courseName, 
                teaching_adj=teachtype,
                adj1 = adj1, 
                emojis = "",
                questions = "",
                answers = "",
                teaching_type = teachTypeGen(teachtype),
                documents = docsGen(mentiondocuments, url),
                limits=limitsgen(limit)
            ))
            st.session_state["assistants"] = getAssistants()
            st.rerun()

def limitsgen(limit):
    nstr = ""
    if limit != 0:
        nstr = f"Your answers should be {limit} words maximum."
    return nstr
    
def docsGen(mentiondocuments, url):
    nstr = ""
    if mentiondocuments :
        nstr = "Encourage them to go and read a section of the provided documents to answer."
        if url != "":
            nstr += " If they do not have access to the text, they can find it at '" + url + "'."
    return nstr

def teachTypeGen(type):
    nstr = ""

    if type == "socratic":
        nstr = "You should not give the answer, but guide the student to answer. Act as a Socratic tutor, taking the initiative in getting the students to answer the questions."
    else :
        nstr = "You can give the answer to the students if they ask for it."
    return nstr