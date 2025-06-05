import streamlit as st
import requests
import json
from typing import List
import time

#base page
st.set_page_config(
    page_title="AADIS",
    page_icon="📚",
    layout="wide"
)

#my fastapi url, match with yours (should ideally be this)
BACKEND_URL = "http://localhost:8000"

def upload_documents(files):
    """upload docs to FastAPI backend"""
    files_data = []
    for file in files:
        files_data.append(("files", (file.name, file.getvalue(), file.type)))
    
    try:
        response = requests.post(f"{BACKEND_URL}/upload-documents/", files=files_data)
        return response.json()
    except requests.exceptions.RequestException as e:
        return {"error": f"Connection error: {str(e)}"}

def ask_question(question: str):
    """question to FastAPI backend"""
    try:

        cleaned_question = ' '.join(question.split()) #json newline error handling debug

        response = requests.post(
            f"{BACKEND_URL}/ask-question/",
            json={"question": cleaned_question},
            headers={"Content-Type": "application/json"}
        )
        return response.json()
    except requests.exceptions.RequestException as e:
        return {"error": f"Connection error: {str(e)}"}

'''below mentioned frontend apis that connect to backend are still under work and may not work as intended but are not part of the final
deliverables'''

def get_documents():
    """list of processed documents"""
    try:
        response = requests.get(f"{BACKEND_URL}/documents/")
        return response.json()
    except requests.exceptions.RequestException as e:
        return {"error": f"Connection error: {str(e)}"}

def delete_document(doc_id: str):
    """delete a document based on id"""
    try:
        response = requests.delete(f"{BACKEND_URL}/documents/{doc_id}")
        return response.json()
    except requests.exceptions.RequestException as e:
        return {"error": f"Connection error: {str(e)}"}

#main app
def main():
    st.title("📚 AADIS")
    st.markdown("Upload documents and ask questions about their content using AI agents.")
    
    #sidebar for document management
    with st.sidebar:
        st.header("📋 Document Management")
        
        #refresh
        if st.button("🔄 Refresh Documents"):
            st.rerun()
        
        #get and display documents
        docs_response = get_documents()
        if "error" not in docs_response:
            documents = docs_response.get("documents", [])
            if documents:
                st.subheader("Processed Documents:")
                for idx, doc in enumerate(documents):
                    col1, col2 = st.columns([3, 1])
                    with col1:
                        st.text(f"📄 {doc.get('filename', 'Unknown')}")
                        st.caption(f"ID: {doc.get('id', 'N/A')}")
                    with col2:
                        #index as fallback if id is None to ensure unique keys (bugfix here)
                        doc_id = doc.get('id')
                        unique_key = f"delete_{doc_id}_{idx}" if doc_id else f"delete_unknown_{idx}"
                        
                        if doc_id:  #this only shows delete button if there is a valid id
                            if st.button("🗑️", key=unique_key, help="Delete document"):
                                result = delete_document(doc_id)
                                if "error" not in result:
                                    st.success("Document deleted!")
                                    st.rerun()
                                else:
                                    st.error(f"Error: {result['error']}")
                        else:
                            st.caption("No ID available")
            else:
                st.info("No documents uploaded yet.")
        else:
            st.error(f"Error loading documents: {docs_response['error']}")
    
    #main content area
    tab1, tab2 = st.tabs(["📤 Upload Documents", "❓ Ask Questions"])
    
    with tab1:
        st.header("Upload Documents")
        st.markdown("Upload your documents to process them with AI agents.")
        
        uploaded_files = st.file_uploader(
            "Choose files to upload",
            accept_multiple_files=True,
            type=['pdf', 'txt', 'docx', 'doc', 'csv', 'xlsx', 'xls'],
            help="Upload PDF, Word, text, or Excel files"
        )
        
        if uploaded_files:
            st.write(f"Selected {len(uploaded_files)} file(s):")
            for file in uploaded_files:
                st.write(f"- {file.name} ({file.type})")
            
            if st.button("🚀 Process Documents", type="primary"):
                with st.spinner("Processing documents... This may take a while."):
                    result = upload_documents(uploaded_files)
                    
                    if "error" in result:
                        st.error(f"Error: {result['error']}")
                    elif result.get("status") == "success":
                        st.success("Documents processed successfully!")
                        
                        #display processing results
                        processed_docs = result.get("processed_documents", [])
                        if processed_docs:
                            st.subheader("Processing Results:")
                            for doc in processed_docs:
                                with st.expander(f"📄 {doc['filename']}"):
                                    col1, col2, col3 = st.columns(3)
                                    with col1:
                                        st.metric("Document ID", doc['document_id'])
                                    with col2:
                                        st.metric("Text Chunks", doc['text_chunks'])
                                    with col3:
                                        st.metric("Tables", doc['tables'])
                        
                        #sidebar refresh
                        st.rerun()
                    else:
                        st.error("Unexpected response from server")
    
    with tab2:
        st.header("Ask Questions")
        st.markdown("Ask questions about your uploaded documents in natural language.")
        
        #documents exist error handling
        docs_response = get_documents()
        if "error" not in docs_response and docs_response.get("documents"):
            #question 
            question = st.text_area(
                "Enter your question:",
                placeholder="e.g., Tell me the models output on the ImageNet dataset?",
                height=100,
                help="Ask any question about your uploaded documents in natural language"
            )
            
            if st.button("🤔 Get Answer", type="primary", disabled=not question.strip()):
                if question.strip():
                    with st.spinner("Finding answer... AI agents are analyzing your documents."):
                        result = ask_question(question.strip())
                        
                        if "error" in result:
                            st.error(f"Error: {result['error']}")
                        else:
                            #answer
                            st.subheader("💡 Answer:")
                            st.write(result.get("answer", "No answer provided"))
                            
                            #sources used
                            sources = result.get("sources", [])
                            if sources:
                                with st.expander("📚 Sources"):
                                    for i, source in enumerate(sources, 1):
                                        st.write(f"{i}. {source}")
                            
                            #agent used
                            agent_used = result.get("agent_used", "")
                            if agent_used:
                                st.caption(f"🤖 Answered by: {agent_used}")

                            #store in history
                            if "qa_history" not in st.session_state:
                                st.session_state.qa_history = []
                            
                            st.session_state.qa_history.append({
                                "question": question.strip(),
                                "answer": result.get("answer", "No answer provided"),
                                "sources": sources
                            })
            
            #this is ai generated for visual pleasing (chat history)
            if "qa_history" not in st.session_state:
                st.session_state.qa_history = []
            
            if st.session_state.qa_history:
                st.subheader("💬 Recent Q&A History")
                for i, qa in enumerate(reversed(st.session_state.qa_history[-5:]), 1):
                    with st.expander(f"Q{i}: {qa['question'][:50]}..."):
                        st.write(f"**Question:** {qa['question']}")
                        st.write(f"**Answer:** {qa['answer']}")
                        if qa.get('sources'):
                            st.write(f"**Sources:** {', '.join(qa['sources'])}")
        else:
            st.info("👆 Please upload some documents first before asking questions.")
            if "error" in docs_response:
                st.error(f"Error checking documents: {docs_response['error']}")

    #footer
    st.markdown("---")
    st.markdown(
        "**Note:** Make sure your FastAPI backend is running on `http://localhost:8000` "
        "or update the `BACKEND_URL` in the code to match your backend location."
    )

if __name__ == "__main__":
    main()
