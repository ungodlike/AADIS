import streamlit as st
import requests
import json
from typing import List
import time

# Configure the page
st.set_page_config(
    page_title="Document Intelligence System",
    page_icon="📚",
    layout="wide"
)

# FastAPI backend URL - adjust this to match your backend
BACKEND_URL = "http://localhost:8000"

def upload_documents(files):
    """Upload documents to FastAPI backend"""
    files_data = []
    for file in files:
        files_data.append(("files", (file.name, file.getvalue(), file.type)))
    
    try:
        response = requests.post(f"{BACKEND_URL}/upload-documents/", files=files_data)
        return response.json()
    except requests.exceptions.RequestException as e:
        return {"error": f"Connection error: {str(e)}"}

def ask_question(question: str):
    """Send question to FastAPI backend"""
    try:
        response = requests.post(
            f"{BACKEND_URL}/ask-question/",
            json={"question": question},
            headers={"Content-Type": "application/json"}
        )
        return response.json()
    except requests.exceptions.RequestException as e:
        return {"error": f"Connection error: {str(e)}"}

def get_documents():
    """Get list of processed documents"""
    try:
        response = requests.get(f"{BACKEND_URL}/documents/")
        return response.json()
    except requests.exceptions.RequestException as e:
        return {"error": f"Connection error: {str(e)}"}

def delete_document(doc_id: str):
    """Delete a document"""
    try:
        response = requests.delete(f"{BACKEND_URL}/documents/{doc_id}")
        return response.json()
    except requests.exceptions.RequestException as e:
        return {"error": f"Connection error: {str(e)}"}

# Main app
def main():
    st.title("📚 Document Intelligence System")
    st.markdown("Upload documents and ask questions about their content using AI agents.")
    
    # Sidebar for document management
    with st.sidebar:
        st.header("📋 Document Management")
        
        # Refresh button
        if st.button("🔄 Refresh Documents"):
            st.rerun()
        
        # Get and display documents
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
                        # Use index as fallback if id is None to ensure unique keys
                        doc_id = doc.get('id')
                        unique_key = f"delete_{doc_id}_{idx}" if doc_id else f"delete_unknown_{idx}"
                        
                        if doc_id:  # Only show delete button if we have a valid ID
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
    
    # Main content area
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
                        
                        # Display processing results
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
                        
                        # Refresh sidebar
                        st.rerun()
                    else:
                        st.error("Unexpected response from server")
    
    with tab2:
        st.header("Ask Questions")
        st.markdown("Ask questions about your uploaded documents in natural language.")
        
        # Check if documents exist
        docs_response = get_documents()
        if "error" not in docs_response and docs_response.get("documents"):
            # Question input
            question = st.text_area(
                "Enter your question:",
                placeholder="e.g., What are the main topics discussed in the documents? Can you summarize the key findings?",
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
                            # Display answer
                            st.subheader("💡 Answer:")
                            st.write(result.get("answer", "No answer provided"))
                            
                            # Display sources if available
                            sources = result.get("sources", [])
                            if sources:
                                with st.expander("📚 Sources"):
                                    for i, source in enumerate(sources, 1):
                                        st.write(f"{i}. {source}")
                            
                            # Display agent used
                            agent_used = result.get("agent_used", "")
                            if agent_used:
                                st.caption(f"🤖 Answered by: {agent_used}")
            
            # Chat history (simple implementation)
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

    # Footer
    st.markdown("---")
    st.markdown(
        "**Note:** Make sure your FastAPI backend is running on `http://localhost:8000` "
        "or update the `BACKEND_URL` in the code to match your backend location."
    )

if __name__ == "__main__":
    main()