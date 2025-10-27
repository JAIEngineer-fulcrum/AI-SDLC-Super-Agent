import streamlit as st
from langchain_xai import ChatXAI
from dotenv import load_dotenv
from github import Github

# ---------------------------
# Environment setup
# ---------------------------
load_dotenv()

# ---------------------------
# Session State Handling
# ---------------------------
for key in ["repo_summary", "detailed_summary", "plan", "code_output"]:
    if key not in st.session_state:
        st.session_state[key] = None

# ---------------------------
# LLM Setup (Hugging Face)
# ---------------------------

llm = ChatXAI(model='grok-4-fast-reasoning')

# ---------------------------
# Utility: Fetch Repo Structure
# ---------------------------
def fetch_repo_structure(repo_link: str, github_token: str):
    try:
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
    except Exception as e:
        st.error(f"Error fetching repo: {e}")
        return "Error fetching repository structure."

# ---------------------------
# Analyzer Agent
# ---------------------------
def analyzer_agent(repo_link, github_token):
    repo_tree = fetch_repo_structure(repo_link, github_token)
    response = llm.invoke(
        f"""You are an analyzer agent.
        Repo: {repo_link}
        Structure:
        {repo_tree}

        Summarize in detail what this repository is about.
        End your response by asking if the user wants a detailed technical breakdown."""
    )
    st.session_state.repo_summary = response.content

def analyzer_deepdive(repo_link, github_token):
    repo_tree = fetch_repo_structure(repo_link, github_token)
    response = llm.invoke(
        f"""You are an analyzer agent.
        Repo: {repo_link}
        Structure:
        {repo_tree}

        Provide a detailed technical breakdown including:
        - Directory structure and relationships
        - Purpose of each key file
        - Probable functions and their roles
        - Entry points and configurations"""
    )
    st.session_state.detailed_summary = response.content

# ---------------------------
# Planner Agent
# ---------------------------
def planner_agent(instruction):
    response = llm.invoke(
        f"""You are a planner agent helping to modify an existing codebase.

        Repo Summary:
        {st.session_state.repo_summary or ''}

        Detailed Summary:
        {st.session_state.detailed_summary or ''}

        User Instruction:
        {instruction}

        Generate a clear and structured implementation plan that includes:
        - Step-by-step tasks
        - Files/modules to modify or create
        - Functions or classes to add/update
        - Dependency or configuration changes
        - Testing and validation guidelines
        """
    )
    st.session_state.plan = response.content

# ---------------------------
# Coder Agent
# ---------------------------
def coder_agent():
    """
    Generates code snippets or modifications based on the approved plan.
    """
    if not st.session_state.plan:
        st.error("No implementation plan found. Please run the Planner Agent first.")
        return

    prompt = f"""
    You are a Coder Agent.

    The following repository has been analyzed and planned for modification:

    Repo Summary:
    {st.session_state.repo_summary or ''}

    Detailed Summary:
    {st.session_state.detailed_summary or ''}

    Implementation Plan:
    {st.session_state.plan}

    Your task:
    - Write code snippets or modifications for each planned step.
    - Clearly mention filenames and directory paths for each change.
    - Include necessary imports, function definitions, and docstrings.
    - Ensure the code integrates cleanly into existing project structure.
    - Add concise inline comments explaining logic.
    """

    response = llm.invoke(prompt)
    st.session_state.code_output = response.content

# ---------------------------
# Streamlit UI
# ---------------------------
st.set_page_config(page_title="AI Super-Agent POC", layout="wide")
st.title("🤖 AI Super-Agent for Codebases")
st.caption("**Analyzer → Planner → Coder** | An end-to-end intelligent code modification assistant")

# Sidebar: Repo Info
st.sidebar.header("🔗 Repository Access")
repo_link = st.sidebar.text_input("GitHub Repo Link", "https://github.com/streamlit/streamlit")
github_token = st.sidebar.text_input("GitHub Token", type="password")

if st.sidebar.button("Analyze Repo"):
    if not repo_link or not github_token:
        st.error("Please provide both a GitHub repo link and token.")
    else:
        analyzer_agent(repo_link, github_token)

# Analyzer Output
if st.session_state.repo_summary:
    st.subheader("📌 Repository Summary")
    st.write(st.session_state.repo_summary)

    detail_choice = st.radio("Do you want a detailed technical summary?", ["No", "Yes"], index=0)
    if detail_choice == "Yes":
        if st.button("Generate Detailed Summary"):
            analyzer_deepdive(repo_link, github_token)

        if st.session_state.detailed_summary:
            st.subheader("📂 Detailed Technical Summary")
            st.write(st.session_state.detailed_summary)

# Planner Section
if st.session_state.repo_summary:
    st.subheader("🛠️ Feature Planning")
    user_instruction = st.text_area("What feature or modification do you want to add?")
    if st.button("Generate Plan"):
        if not user_instruction.strip():
            st.error("Please enter a valid instruction.")
        else:
            planner_agent(user_instruction)

    if st.session_state.plan:
        st.subheader("✅ Implementation Plan")
        st.write(st.session_state.plan)

# Coder Section
if st.session_state.plan:
    st.subheader("💻 Code Generation")
    st.info("Generate actual code changes based on the implementation plan above.")
    if st.button("Generate Code"):
        coder_agent()

    if st.session_state.code_output:
        st.subheader("📝 Generated Code Snippets")
        st.code(st.session_state.code_output, language="python")

# Footer
st.markdown("---")
st.caption("🚀 Built with LangChain + Grok-4-Fast-Reasoning + Streamlit | AI Super-Agent Prototype")
