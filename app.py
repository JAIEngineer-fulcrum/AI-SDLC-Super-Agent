import streamlit as st
from langchain_xai import ChatXAI
from dotenv import load_dotenv
from github import Github

load_dotenv()

# ---------------------------
# State handling
# ---------------------------
if "repo_summary" not in st.session_state:
    st.session_state.repo_summary = None
if "detailed_summary" not in st.session_state:
    st.session_state.detailed_summary = None
if "plan" not in st.session_state:
    st.session_state.plan = None

# ---------------------------
# LLM setup
# ---------------------------

llm = ChatXAI(model='grok-4-fast-reasoning')

# ---------------------------
# Utility: Fetch repo structure
# ---------------------------
def fetch_repo_structure(repo_link: str, github_token: str):
    g = Github(github_token)
    owner, repo_name = repo_link.rstrip("/").replace("https://github.com/", "").split("/")[:2]
    repo = g.get_repo(f"{owner}/{repo_name}")

    contents = repo.get_contents("")
    file_tree = []
    while contents:
        file_content = contents.pop(0)
        if file_content.type == "dir":
            file_tree.append(f"[DIR] {file_content.path}")
        else:
            file_tree.append(f"[FILE] {file_content.path}")
    return "\n".join(file_tree)

# ---------------------------
# Analyzer Agents
# ---------------------------
def analyzer_agent(repo_link, github_token):
    repo_tree = fetch_repo_structure(repo_link, github_token)
    response = llm.invoke(
        f"""You are an analyzer agent. 
        Repo: {repo_link}
        Structure:
        {repo_tree}
        Summarize what this repo is about, then ask if the user wants a detailed technical breakdown."""
    )
    st.session_state.repo_summary = response.content

def analyzer_deepdive(repo_link, github_token):
    repo_tree = fetch_repo_structure(repo_link, github_token)
    response = llm.invoke(
        f"""You are an analyzer agent.
        Repo: {repo_link}
        Structure:
        {repo_tree}
        Provide:
        - Directory breakdown
        - Purpose of each file
        - Probable functions/features
        - Entry points"""
    )
    st.session_state.detailed_summary = response.content

# ---------------------------
# Planner Agent
# ---------------------------
def planner_agent(instruction):
    response = llm.invoke(
        f"""You are a planner agent.
        Repo summary: {st.session_state.repo_summary or ""}
        Detailed summary: {st.session_state.detailed_summary or ""}
        Instruction: {instruction}
        Generate:
        - Step-by-step design
        - Files/modules to modify
        - Functions to add/update
        - Dependencies/config changes
        - Testing considerations"""
    )
    st.session_state.plan = response.content

# ---------------------------
# Streamlit UI
# ---------------------------
st.set_page_config(page_title="AI Super-Agent POC", layout="wide")
st.title("🤖 AI Super-Agent for Codebases")

# Sidebar inputs
st.sidebar.header("Repository Details")
repo_link = st.sidebar.text_input("GitHub Repo Link", "https://github.com/streamlit/streamlit")
github_token = st.sidebar.text_input("GitHub Token", type="password")

if st.sidebar.button("Analyze Repo"):
    if not repo_link or not github_token:
        st.error("Please provide both a GitHub repo link and token.")
    else:
        analyzer_agent(repo_link, github_token)

# Show repo summary if available
if st.session_state.repo_summary:
    st.subheader("📌 Repo Summary")
    st.write(st.session_state.repo_summary)

    detail_choice = st.radio("Do you want a detailed technical summary?", ["No", "Yes"], index=0)

    if detail_choice == "Yes":
        if st.button("Generate Detailed Summary"):
            analyzer_deepdive(repo_link, github_token)

        if st.session_state.detailed_summary:
            st.subheader("📂 Detailed Technical Summary")
            st.write(st.session_state.detailed_summary)

# Planner Agent Section
if st.session_state.repo_summary:
    st.subheader("🛠️ Feature Planning")
    user_instruction = st.text_area("What modification/feature do you want to add?")
    if st.button("Generate Plan"):
        if not user_instruction.strip():
            st.error("Please enter a feature request.")
        else:
            planner_agent(user_instruction)

    if st.session_state.plan:
        st.subheader("✅ Implementation Plan")
        st.write(st.session_state.plan)
