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

#Delete assistant :
@st.experimental_dialog("Are you sure ?")
def delAssistant(assistant):
    st.write(f"""You are about to delete the activity '{assistant["name"]}'.
this action is irreversible, you will not be able recover it if you press the 'confirm' button.""")
    
    col1,col2 = st.columns([1,.2])
    with col1:
        if st.button("Cancel"):
            st.rerun()
    with col2:
        if st.button("Confirm"): 
            openai_client.beta.assistants.delete(assistant["id"])
            st.session_state["assistants"] = getAssistants()
            st.session_state["selectedID"] = 0
            st.rerun()
#New assistant :

partial_template = """You are a friendly virtual assistant for the Education and Society course. 
Your name is SIMBA 😸 (Sistema Inteligente de Medición, Bienestar y Apoyo) and you were created by the Núcleo Milenio de Educación Superior. 

Respond in a friendly, concise and proactive way, using emojis where possible. 

Help the student answer the following questions: 

{questions}

You should not give the answer, but guide the student to answer. Act as a Socratic tutor, taking the initiative in getting the students to answer the questions. 

Encourage them to go and read a section of the provided documents to answer. If they do not have access to the text, they can find it at ‘https://bmdigitales-bibliotecas-uc-cl.pucdechile.idm.oclc.org/html5/EDUCACION%20Y%20SOCIOLOGIA/50/’.

Your first message should begin with ‘Hello! 😸 This week I will help you reflect on the following questions: ’ Followed by the questions to answer.

Your answers should be 100 words maximum."""

@st.experimental_dialog("Define your new activity")
def newAssistant():

    if "initialized" not in st.session_state :
        st.session_state["initialized"] = False

    if not st.session_state["initialized"]:
        st.session_state["nbQuestions"] = 1
        st.session_state["questions"] = [""]

    newprompt = PromptTemplate.from_template(partial_template)

    newname = st.text_input("Activity's name", placeholder = "New name...")
    newdesc = st.text_input("Activity's description", placeholder = "New description...")
    model = "gpt-4-turbo"

    st.write("### Activity's questions")
    
    add,remove = st.columns([.5,1])
    with add:
        if st.button("add a question") :
            st.session_state["nbQuestions"] = st.session_state["nbQuestions"]+1
    with remove:
        if st.button("remove a question") :
            st.session_state["nbQuestions"] = st.session_state["nbQuestions"]-1

    for i in range(1,st.session_state["nbQuestions"]+1):
        if i-1 < len(st.session_state["questions"]):
            st.session_state["questions"][i-1] = st.text_input(f"Question {i}", placeholder="enter the question statement", key=f"question{i}", value=st.session_state["questions"][i-1])
        else :
            st.session_state["questions"].append("")
            st.session_state["questions"][i-1] = st.text_input(f"Question {i}", placeholder="enter the question statement", key=f"question{i}")

    st.session_state["initialized"] = True
    col1,col2 = st.columns([.5,1])
    with col1:
        if st.button("Cancel"):
            st.session_state["initialized"] = False
            st.rerun()
    with col2:
        if st.button("Create"): 
            openai_client.beta.assistants.create(
                name=newname,
                description=newdesc,
                instructions=newprompt.format(questions = questionsGen()),
                tools=[{"type": "retrieval"}],
                model=model
            )
            st.session_state["assistants"] = getAssistants()
            st.session_state["initialized"] = False
            st.rerun()
            

#Modifying the main prompt :

full_template ="""You are a {adj1} {teaching_adj} tutor for the course '{courseName}'.

Your name is SIMBA 😸 (Sistema Inteligente de Medición, Bienestar y Apoyo) and you were created by the Núcleo Milenio de Educación Superior.
Respond in a {adj1}, concise and proactive way{emojis}.

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

    if "initialized" not in st.session_state :
        st.session_state["initialized"] = False

    if not st.session_state["initialized"]:
        st.session_state["nbQuestions"] = vals["nbQuestions"]
        st.session_state["questions"] = vals["questions"]

    newprompt = PromptTemplate.from_template(full_template)

    courseName = st.text_input("what is the name of the course ?", value=vals["courseName"])

    attitudes = ["friendly","informal","formal"]
    adj1 = st.selectbox("What attitude should the assistant have toward the students ?", attitudes, index=attitudes.index(vals["adj1"]))

    teachtypes = ["socratic","other"]
    teachtype = st.selectbox("What should be the assistant's approach to teaching ?", teachtypes, index=teachtypes.index(vals["teaching_adj"]))

    st.write("### Activity's questions")
    
    add,remove = st.columns([.5,1])
    with add:
        if st.button("add a question") :
            st.session_state["nbQuestions"] = st.session_state["nbQuestions"]+1
    with remove:
        if st.button("remove a question") :
            st.session_state["nbQuestions"] = st.session_state["nbQuestions"]-1

    for i in range(1,st.session_state["nbQuestions"]+1):
        if i-1 < len(st.session_state["questions"]):
            st.session_state["questions"][i-1] = st.text_input(f"Question {i}", placeholder="enter the question statement", key=f"question{i}", value=st.session_state["questions"][i-1])
        else :
            st.session_state["questions"].append("")
            st.session_state["questions"][i-1] = st.text_input(f"Question {i}", placeholder="enter the question statement", key=f"question{i}")
    
    giveAnswers = st.checkbox("The assistant should give an answer to the activity questions if the student asks for it.", value=vals["answers"])

    useEmojis = st.checkbox("The assistant should use emojis.", value=vals["emojis"])

    mentiondocuments = st.checkbox("The assistant should encourage the student to rely on the provided documents for answering.", value=vals["documents"])
    if mentiondocuments:
        url = st.text_input("Is there an URL where to find those documents ?", value=vals["url"], placeholder="leave empty if you have no url")
    else :
        url = ""
    
    limit = st.number_input("include a word count limit for the assistant's answers ? (0 = no limit)", min_value=0, value=vals["limits"])
    
    st.session_state["initialized"] = True
    col1,col2 = st.columns([.5,1])
    with col1:
        if st.button("Cancel"):
            st.session_state["initialized"] = False
            st.rerun()
    with col2:
        if st.button("Submit"):
            openai_client.beta.assistants.update(assistant["id"], instructions=newprompt.format(
                courseName=courseName, 
                teaching_adj=teachtype,
                adj1 = adj1, 
                emojis = emojiGen(useEmojis),
                questions = questionsGen(),
                answers = answersGen(giveAnswers),
                teaching_type = teachTypeGen(teachtype),
                documents = docsGen(mentiondocuments, url),
                limits=limitsgen(limit)
            ))
            st.session_state["assistants"] = getAssistants()
            st.session_state["initialized"] = False
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

def emojiGen(useEmojis):
    nstr = ""
    if useEmojis :
        nstr = ", using emojis where possible."
    else :
        nstr = "."
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
    vals["questions"] = []
    sub = re.compile("Question . : ")
    splitQ = sub.split(prompt)
    vals["nbQuestions"] = len(sub.findall(prompt))
    for i in range(1,len(splitQ)):
        if i == len(splitQ):
            vals["questions"].append(splitQ[i].partition('\n')[0])
        else :
            vals["questions"].append(splitQ[i].partition('\n')[0])
    
    # answering questions
    if "You should not give the answer, but guide the student to answer." in prompt:
        vals["answers"] = True
    else :
        vals["answers"] = False

    # emojis
    if ", using emojis where possible." in prompt:
        vals["emojis"] = True
    else :
        vals["emojis"] = False

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
