
# AADIS

Advanced Agentic Document Intelligence System is a FastAPI-based backend service that allows users to upload documents, extract their contents (text and tables), and perform question answering over the processed documents using agent-based orchestration



## Installation

First install the requirements

```bash
pip install -r requirements.txt
```
Then run the fastapi backend using
```bash
python main.py
```
To input questions in natural language, run the streamlit frontend
```bash
streamlit run frontend.py
```
## Features

```bash
User ↔ AADIS
    ├── /upload-documents/ → DocumentProcessingCrew → KnowledgeBase
    ├── /ask-question/     → QACrew → KnowledgeBase
    ├── /documents/        → KnowledgeBase
    └── /documents/{id}    → KnowledgeBase
```
The above figure shows the working of the agentic system with the endpoints used.

The Document Processing Crew consists of a text extraction agent and a table extraction agent. These two agents process the documents and store it in the KnowledgeBase.

The QA Crew consists of a text retrieval agent and a table analysis agent. These 2 agents are supervised by a Supervisor agent that delegates tasks based on the question asked and finally retrieve relevant data from the Knowledge Base. 
