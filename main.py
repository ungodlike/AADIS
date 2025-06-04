from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.responses import JSONResponse
import tempfile
import os
from typing import List
import uvicorn

from my_doc_agents import DocumentProcessingCrew
from my_qa_agents import QACrew
from knowledge_base import KnowledgeBase

app = FastAPI(title="AADIS")

#init 
kb = KnowledgeBase()
doc_crew = DocumentProcessingCrew()
qa_crew = QACrew(kb)

@app.post("/upload-documents/")
async def upload_documents(files: List[UploadFile] = File(...)):
    """Upload and process documents"""
    try:
        results = []
        
        for file in files:
            #temp file save
            with tempfile.NamedTemporaryFile(delete=False, suffix=f".{file.filename.split('.')[-1]}") as temp_file:
                content = await file.read()
                temp_file.write(content)
                temp_file_path = temp_file.name
            
            try:
                #process documents 
                extracted_data = doc_crew.process_document(temp_file_path, file.filename)
                
                #storing processed docs in kb 
                doc_id = kb.store_document(file.filename, extracted_data)
                
                results.append({
                    "filename": file.filename,
                    "document_id": doc_id,
                    "text_chunks": len(extracted_data.get("text_chunks", [])),
                    "tables": len(extracted_data.get("tables", []))
                })
                
            finally:
                #flush temp
                os.unlink(temp_file_path)
        
        return JSONResponse(content={"status": "success", "processed_documents": results})
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/ask-question/")
async def ask_question(question: dict):
    """Ask a question about uploaded documents"""
    try:
        user_question = question.get("question", "")
        if not user_question:
            raise HTTPException(status_code=400, detail="Ask a question")
        
        #process question using QA agents
        answer = qa_crew.answer_question(user_question)
        
        return JSONResponse(content={
            "question": user_question,
            "answer": answer["answer"],
            "sources": answer.get("sources", []),
            "agent_used": answer.get("agent_used", "")
        })
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/documents/")
async def list_documents():
    """List all processed documents"""
    documents = kb.list_documents()
    return JSONResponse(content={"documents": documents})

@app.delete("/documents/{doc_id}")
async def delete_document(doc_id: str):
    """Delete a document from knowledge base"""
    try:
        kb.delete_document(doc_id)
        return JSONResponse(content={"status": "success", "message": f"Document {doc_id} deleted"})
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
