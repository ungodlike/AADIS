from crewai import Agent, Task, Crew, LLM
from typing import Dict, Any, List

class QACrew:
    def __init__(self, knowledge_base):
        self.kb = knowledge_base
        self.llm = LLM(model="groq/llama-3.3-70b-versatile")
        
        self.supervisor_agent = Agent(
            role="Question Analysis Supervisor",
            goal="Analyze user questions and determine the best approach to answer them",
            backstory="You are an intelligent supervisor who understands user intent and coordinates different specialists to provide comprehensive answers.",
            verbose=False,
            allow_delegation=True,
            llm=self.llm
        )
        
        self.text_retrieval_agent = Agent(
            role="Text Information Retrieval Specialist",
            goal="Find and synthesize relevant text information to answer user questions",
            backstory="You specialize in searching through text content and documents to find relevant information and provide strictly 'to the point' answers based on textual context." \
                      "Do not generate an answer based on your knowledge but only based on the document context, ideally in similar language."\
                      "Do not write any code or perform any mathematics if the context is scientific.",
            verbose=False,
            allow_delegation=False,
            llm=self.llm
        )
        
        self.table_analysis_agent = Agent(
            role="Data Analysis Specialist",
            goal="Analyze tabular data and provide insights based on structured information",
            backstory="You are an expert in analyzing tables, charts, and structured data to answer questions that require numerical analysis or data interpretation.",
            verbose=False,
            allow_delegation=False,
            llm=self.llm
        )
    
    def answer_question(self, question: str) -> Dict[str, Any]:
        """Process user question using appropriate agents"""
        
        #using text/tables depending on the question
        relevant_texts = self.kb.search_text(question, limit=5)
        relevant_tables = self.kb.search_tables(question, limit=3)
        
        #supervisor task
        supervisor_task = Task(
            description=f"""
            Analyze this user question: "{question}"
            
            Available information:
            - Text chunks: {len(relevant_texts)} relevant pieces found
            - Tables: {len(relevant_tables)} relevant tables found
            
            Determine:
            1. What type of question this is (factual, analytical, comparative, etc.)
            2. Whether it requires text analysis, table analysis, or both
            3. What specific information should be retrieved
            
            Provide a plan for answering this question.
            """,
            agent=self.supervisor_agent,
            expected_output="Analysis plan specifying which agents to use and what information to focus on"
        )
        
        #text retrieval task
        text_task = Task(
            description=f"""
            Answer this question using text information: "{question}"
            
            Relevant text content:
            {self._format_text_chunks(relevant_texts)}
            
            Provide a comprehensive answer based on the text content.
            """,
            agent=self.text_retrieval_agent,
            expected_output="'To the point' answer based on text analysis"
        )
        
        #table analysis task
        table_task = Task(
            description=f"""
            Answer this question using table/data analysis: "{question}"
            
            Relevant tables:
            {self._format_tables(relevant_tables)}
            
            Analyze the data and provide insights relevant to the question.
            """,
            agent=self.table_analysis_agent,
            expected_output="Data-driven answer based on table analysis"
        )
        
        #final crew for qa
        crew = Crew(
            agents=[self.supervisor_agent, self.text_retrieval_agent, self.table_analysis_agent],
            tasks=[supervisor_task, text_task, table_task],
            verbose=False
        )
        
        result = crew.kickoff()
        
        #test code for agent check, using based on needs
        agent_used = "combined"
        if len(relevant_texts) > len(relevant_tables):
            agent_used = "text_retrieval"
        elif len(relevant_tables) > 0:
            agent_used = "table_analysis"
        
        return {
            "answer": str(result),
            "sources": [
                f"Text chunks: {len(relevant_texts)}",
                f"Tables: {len(relevant_tables)}"
            ],
            "agent_used": agent_used
        }
    
    def _format_text_chunks(self, text_chunks: List[Dict]) -> str:
        """Format text chunks for agent processing"""
        if not text_chunks:
            return "No relevant text found."
        
        formatted = ""
        for i, chunk in enumerate(text_chunks[:3]):  #limit top 3
            formatted += f"Text {i+1} (from {chunk['filename']}):\n{chunk['content']}\n\n"
        return formatted
    
    def _format_tables(self, tables: List[Dict]) -> str:
        """Format tables for agent processing"""
        if not tables:
            return "No relevant tables found."
        
        formatted = ""
        for i, table in enumerate(tables[:2]):  #limit top 2
            formatted += f"Table {i+1} (from {table['filename']}):\n"
            formatted += f"Description: {table.get('description', 'N/A')}\n"
            formatted += f"Data: {table['data']}\n\n"
        return formatted
