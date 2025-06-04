import chromadb
import uuid
from typing import Dict, List, Any
import json

class KnowledgeBase:
    def __init__(self, persist_directory: str = "./chroma_db"):
        #init chroma
        self.client = chromadb.PersistentClient(path=persist_directory)
        
        #make collections
        self.text_collection = self.client.get_or_create_collection(
            name="document_texts",
            metadata={"description": "Text chunks from documents"}
        )
        
        self.table_collection = self.client.get_or_create_collection(
            name="document_tables", 
            metadata={"description": "Tables from documents"}
        )
        
        #stor doc metadata
        self.documents = {}
    
    def store_document(self, filename: str, extracted_data: Dict[str, Any]) -> str:
        """Store extracted document data in vector database"""
        doc_id = str(uuid.uuid4())
        
        #store text chunks
        if extracted_data.get("text_chunks"):
            text_ids = []
            text_documents = []
            text_metadata = []
            
            for i, chunk in enumerate(extracted_data["text_chunks"]):
                chunk_id = f"{doc_id}_text_{i}"
                text_ids.append(chunk_id)
                text_documents.append(chunk)
                text_metadata.append({
                    "document_id": doc_id,
                    "filename": filename,
                    "chunk_index": i,
                    "type": "text"
                })
            
            self.text_collection.add(
                ids=text_ids,
                documents=text_documents,
                metadatas=text_metadata
            )
        
        #store tables
        if extracted_data.get("tables"):
            table_ids = []
            table_documents = []
            table_metadatas = []
            
            for i, table in enumerate(extracted_data["tables"]):
                table_id = f"{doc_id}_table_{i}"
                table_ids.append(table_id)
                
                #table to searchable text
                table_text = self._table_to_text(table)
                table_documents.append(table_text)
                table_metadatas.append({
                    "document_id": doc_id,
                    "filename": filename,
                    "table_index": i,
                    "type": "table",
                    "table_data": json.dumps(table)
                })
            
            self.table_collection.add(
                ids=table_ids,
                documents=table_documents,
                metadatas=table_metadatas
            )
        
        #store doc metadata
        self.documents[doc_id] = {
            "filename": filename,
            "text_chunks": len(extracted_data.get("text_chunks", [])),
            "tables": len(extracted_data.get("tables", [])),
            "created_at": str(uuid.uuid4())  # Placeholder timestamp
        }
        
        return doc_id
    
    def search_text(self, query: str, limit: int = 5) -> List[Dict]:
        """Search for relevant text chunks"""
        try:
            results = self.text_collection.query(
                query_texts=[query],
                n_results=limit
            )
            
            text_results = []
            if results["documents"] and results["documents"][0]:
                for i, (doc, metadata) in enumerate(zip(results["documents"][0], results["metadatas"][0])):
                    text_results.append({
                        "content": doc,
                        "filename": metadata["filename"],
                        "chunk_index": metadata["chunk_index"],
                        "score": results["distances"][0][i] if results["distances"] else 0
                    })
            
            return text_results
        except Exception as e:
            print(f"Text search error: {e}")
            return []
    
    def search_tables(self, query: str, limit: int = 3) -> List[Dict]:
        """Search for relevant tables"""
        try:
            results = self.table_collection.query(
                query_texts=[query],
                n_results=limit
            )
            
            table_results = []
            if results["documents"] and results["documents"][0]:
                for i, (doc, metadata) in enumerate(zip(results["documents"][0], results["metadatas"][0])):
                    table_data = json.loads(metadata["table_data"])
                    table_results.append({
                        "description": doc,
                        "filename": metadata["filename"],
                        "table_index": metadata["table_index"],
                        "data": table_data,
                        "score": results["distances"][0][i] if results["distances"] else 0
                    })
            
            return table_results
        except Exception as e:
            print(f"Table search error: {e}")
            return []
    
    def list_documents(self) -> List[Dict]:
        """List all stored documents"""
        return list(self.documents.values())
    
    def delete_document(self, doc_id: str):
        """Delete a document and its associated data"""
        #delete doc
        try:
            #get all text chunks for one doc
            text_results = self.text_collection.get(where={"document_id": doc_id})
            if text_results["ids"]:
                self.text_collection.delete(ids=text_results["ids"])
            
            #get all tables for one doc 
            table_results = self.table_collection.get(where={"document_id": doc_id})
            if table_results["ids"]:
                self.table_collection.delete(ids=table_results["ids"])
            
            #remove from doc metadata
            if doc_id in self.documents:
                del self.documents[doc_id]
                
        except Exception as e:
            raise Exception(f"Error deleting document: {e}")
    
    def _table_to_text(self, table: Dict) -> str:
        """Convert table data to searchable text"""
        if "error" in table:
            return table["error"]
        
        text_parts = []
        if "data" in table and table["data"]:
            #assuming first row might be headers
            data = table["data"]
            if data:
                headers = data[0]
                text_parts.append("Table headers: " + " | ".join(headers))
                
                #adding sample rows
                for row in data[1:min(4, len(data))]:  #first 3 data rows
                    text_parts.append(" | ".join(str(cell) for cell in row))
        
        return "\n".join(text_parts)
