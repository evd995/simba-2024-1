from openai import OpenAI
import streamlit as st
from langchain_core.prompts import PromptTemplate
import os
import re

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

    oldprompt = assistant["instructions"]

    vals = extractVals(oldprompt)

    newprompt = PromptTemplate.from_template(full_template)

    courseName = st.text_input("what is the name of the course ?", value=vals["courseName"])

    attitudes = ["friendly","informal","formal"]
    adj1 = st.selectbox("What attitude should the assistant have toward the students ?", attitudes, index=attitudes.index(vals["adj1"]))

    teachtypes = ["socratic","other"]
    teachtype = st.selectbox("What shloud be the assistant's approach to teaching ?", teachtypes, index=teachtypes.index(vals["teaching_adj"]))

    if "nbQuestions" not in st.session_state :
        st.session_state["nbQuestions"] = 1

    st.write("### Activity questions")
    
    add,remove = st.columns([.5,1])
    with add:
        if st.button("add a question") :
            st.session_state["nbQuestions"] = st.session_state["nbQuestions"]+1
    with remove:
        if st.button("remove a question") :
            st.session_state["nbQuestions"] = st.session_state["nbQuestions"]-1

    for i in range(1,st.session_state["nbQuestions"]+1):
        st.text_input(f"Question {i}", placeholder="enter the question statement", key=f"question{i}")
    
    giveAnswers = st.checkbox("The assistant should give an answer to the activity questions if the student asks for it.")

    mentiondocuments = st.checkbox("The assistant should encourage the student to rely on the provided documents for answering.")
    if mentiondocuments:
        url = st.text_input("Is there an URL where to find those documents ?", value="", placeholder="leave empty if you have no url")
    else :
        url = ""
    
    limit = st.number_input("include a word count limit for the assistant's answers ? (0 = no limit)", min_value=0, value=0)
    
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
                questions = questionsGen(),
                answers = answersGen(giveAnswers),
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
        nstr = "Act as a Socratic tutor, taking the initiative in getting the students to answer the questions."
    else :
        nstr = "Act as a standard teacher."
    return nstr

def answersGen(give):
    nstr = ""
    if give :
        nstr = "You should not give the answer, but guide the student to answer."
    else:
        nstr = "You can provide an answer to the provided questions if the student asks for it."
    return nstr

def questionsGen():
    nstr = ""

    for i in range(1,st.session_state["nbQuestions"]+1):
        nstr = nstr + f"Question {i} : {st.session_state[f'question{i}']} \n"

    return nstr

def extractVals(prompt):
    vals = {}
    checkstring = "Your name is SIMBA 😸 (Sistema Inteligente de Medición, Bienestar y Apoyo) and you were created by the Núcleo Milenio de Educación Superior."
    
    # Adj
    if checkstring in prompt:
        result = re.search('You are a (.*) ', prompt)
        vals["adj1"] = result.group(1).split(" ")[0]
    else :
        vals["adj1"] = "friendly"

    # teaching style
    if checkstring in prompt:
        result = re.search(' (.*) tutor for the course', prompt)
        vals["teaching_adj"] = result.group(1).split(" ")[-1]
    else :
        vals["teaching_adj"] = "socratic"

    # course name
    if checkstring in prompt:
        result = re.search("tutor for the course '(.*)'.", prompt)
        vals["courseName"] = result.group(1)
    else :
        vals["courseName"] = "default name"

    # questions

    # answering questions
    if "You should not give the answer, but guide the student to answer." in prompt:
        vals["answers"] = True
    else :
        vals["answers"] = False

    # documents
    vals["documents"] = False
    vals["url"] = ""
    if "Encourage them to go and read a section of the provided documents to answer." in prompt:
        vals["documents"] = True
        if " If they do not have access to the text, they can find it at '" in prompt:
            result = re.search(" If they do not have access to the text, they can find it at '(.*)'.", prompt)
            vals["url"] = result.group(1)
        
    # words limit
    if checkstring in prompt and "Your answers should be " in prompt:
        result = re.search('Your answers should be (.*) words maximum.', prompt)
        vals["limits"] = int(result.group(1))
    else :
        vals["limits"] = 0

    return vals
