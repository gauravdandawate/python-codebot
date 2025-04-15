import streamlit as st
import requests

FASTAPI_URL = "http://localhost:8000"  # Change if needed

st.title("💬 CodeBot: Ask questions about your code")

tab1, tab2 = st.tabs(["Ask", "Generate Embeddings"])

with tab1:
    st.subheader("Ask a question about your codebase")
    query = st.text_input("Question", placeholder="e.g., What does the login function do?")
    if st.button("Get Answer") and query:
        response = requests.post(f"{FASTAPI_URL}/ask?query={query}")
        if response.status_code == 200:
            data = response.json()
            st.markdown(f"### ✅ Answer:\n{data['answer']}")
        else:
            st.error("Something went wrong!")

with tab2:
    st.subheader("Generate Embeddings")
    codebase_path = st.text_input("Path to codebase", placeholder="Path to your codebase")

    if st.button("Run Embedding"):
        response = requests.post(f"{FASTAPI_URL}/embed?code_path={codebase_path}")
        if response.status_code == 200:
            st.success(response.json().get("message"))
        else:
            st.error("Error generating embeddings.")
