from langgraph.graph import StateGraph, START, END
from typing import TypedDict, Annotated, List, Optional
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, SystemMessage
from langgraph.graph.message import add_messages
from langgraph.checkpoint.memory import InMemorySaver
from langchain_openai import ChatOpenAI
import re
import json

class RAGState(TypedDict):
    """State for RAG workflow"""
    messages: Annotated[List[BaseMessage], add_messages]
    question: str
    sql_query: str
    db_results: List[dict]
    final_answer: str
    error: Optional[str]

class PhoneRAGGraph:
    """LangGraph-based RAG agent for phone queries"""
    
    def __init__(self, db_manager, config, use_groq=False):
        self.db = db_manager
        self.config = config
        self.schema = self._load_schema()
        self.examples = self._load_examples()
        
        # Choose LLM
        if use_groq:
            self.llm = ChatOpenAI(
                model="gpt-4o-mini",
                temperature=0.0,
                max_retries=2
            )
        else:
            self.llm = ChatOpenAI(
                model_name=config.openai_model,
                temperature=0
            )
        
        # Build graph
        self.graph = self._build_graph()
        self.checkpointer = InMemorySaver()
        self.app = self.graph.compile(checkpointer=self.checkpointer)
    
    def _load_schema(self):
        """Load database schema"""
        return """
        Table: samsung_phones
        
        Columns:
        - id: integer (primary key)
        - name: varchar (phone model name)
        - url: text (product page URL)
        - image_url: text (phone image URL)
        - launch_announced: varchar (announcement date)
        - launch_status: varchar (availability status)
        - network_technology: text (network types)
        - network_5g_bands: text (5G band support)
        - network_4g_bands: text (4G/LTE bands)
        - body_dimensions: varchar (physical dimensions)
        - body_weight: varchar (weight in grams)
        - display_type: text (screen technology)
        - display_size: varchar (screen size in inches)
        - display_resolution: varchar (screen resolution)
        - platform_os: text (operating system)
        - platform_chipset: text (processor chipset)
        - platform_cpu: text (CPU details)
        - platform_gpu: text (GPU details)
        - memory_internal: text (storage options)
        - main_camera: text (rear camera specs)
        - main_camera_features: text (camera features)
        - main_camera_video: text (video recording capabilities)
        - selfie_camera: text (front camera specs)
        - battery_type: text (battery capacity)
        - battery_charging: text (charging capabilities)
        - misc_price: text (price information)
        - misc_colors: text (available colors)
        """
    
    def _load_examples(self):
        """Load few-shot examples"""
        try:
            with open("few_shot.json", "r", encoding="utf-8") as f:
                return json.load(f)
        except FileNotFoundError:
            return [
                {
                    "user_question": "Which phones have 5G?",
                    "sql_schema": "SELECT name, network_5g_bands FROM samsung_phones WHERE network_5g_bands != '' AND network_5g_bands IS NOT NULL LIMIT 5"
                },
                {
                    "user_question": "Compare Galaxy S25 and S24 cameras",
                    "sql_schema": "SELECT name, main_camera, selfie_camera, main_camera_features FROM samsung_phones WHERE name ILIKE '%Galaxy S25%' OR name ILIKE '%Galaxy S24%'"
                }
            ]
    
    def _build_graph(self):
        """Build LangGraph workflow"""
        graph = StateGraph(RAGState)
        
        # Add nodes
        graph.add_node("extract_question", self.extract_question_node)
        graph.add_node("generate_sql", self.generate_sql_node)
        graph.add_node("execute_query", self.execute_query_node)
        graph.add_node("generate_answer", self.generate_answer_node)
        graph.add_node("handle_error", self.handle_error_node)
        
        # Add edges
        graph.add_edge(START, "extract_question")
        graph.add_edge("extract_question", "generate_sql")
        graph.add_conditional_edges(
            "generate_sql",
            self.check_sql_valid,
            {
                "valid": "execute_query",
                "invalid": "handle_error"
            }
        )
        graph.add_conditional_edges(
            "execute_query",
            self.check_results,
            {
                "success": "generate_answer",
                "error": "handle_error"
            }
        )
        graph.add_edge("generate_answer", END)
        graph.add_edge("handle_error", END)
        
        return graph
    
    def extract_question_node(self, state: RAGState):
        """Extract question from messages"""
        messages = state["messages"]
        last_message = messages[-1]
        
        if isinstance(last_message, HumanMessage):
            question = last_message.content
        else:
            question = str(last_message)
        
        return {"question": question}
    
    def generate_sql_node(self, state: RAGState):
        """Generate SQL query from question"""
        question = state["question"]
        
        examples_text = "\n\n".join([
            f"Question: {ex['user_question']}\nSQL: {ex['sql_schema']}"
            for ex in self.examples
        ])
        
        prompt = f"""
You are an expert at converting natural language questions into PostgreSQL queries.

DATABASE SCHEMA:
{self.schema}

EXAMPLE QUERIES:
{examples_text}

RULES:
1. Generate syntactically correct PostgreSQL only
2. Use ILIKE for case-insensitive string matching
3. Include LIMIT 5 unless specified otherwise
4. Return ONLY the SQL query, no explanations or markdown
5. Handle NULL values appropriately
6. Use proper WHERE clauses for filtering

USER QUESTION:
{question}

SQL QUERY:"""
        
        messages = [
            SystemMessage(content="You are a SQL expert. Generate valid PostgreSQL queries."),
            HumanMessage(content=prompt)
        ]
        
        response = self.llm.invoke(messages)
        sql_query = self._clean_sql(response.content)
        
        return {"sql_query": sql_query}
    
    def execute_query_node(self, state: RAGState):
        """Execute SQL query against database"""
        sql_query = state["sql_query"]
        
        try:
            results = self.db.execute_query(sql_query)
            return {"db_results": results}
        except Exception as e:
            return {"error": f"Database error: {str(e)}"}
    
    def generate_answer_node(self, state: RAGState):
        """Generate natural language answer from results"""
        question = state["question"]
        results = state["db_results"]
        
        if not results:
            answer = "I couldn't find any phones matching your criteria. Try rephrasing your question or asking about different specifications."
            return {
                "final_answer": answer,
                "messages": [AIMessage(content=answer)]
            }
        
        prompt = f"""
You are a helpful Samsung smartphone expert assistant.

USER QUESTION:
{question}

DATABASE RESULTS:
{json.dumps(results, indent=2)}

TASK:
- Explain the results in clear, conversational English
- Highlight key specifications and differences
- Be specific with numbers and details
- If comparing phones, present side-by-side comparisons
- Keep response concise but informative (100-200 words)
- Don't mention SQL or databases

ANSWER:"""
        
        messages = [
            SystemMessage(content="You are a knowledgeable phone advisor who explains specifications clearly."),
            HumanMessage(content=prompt)
        ]
        
        response = self.llm.invoke(messages)
        answer = response.content.strip()
        
        return {
            "final_answer": answer,
            "messages": [AIMessage(content=answer)]
        }
    
    def handle_error_node(self, state: RAGState):
        """Handle errors in the workflow"""
        error = state.get("error", "Unknown error occurred")
        answer = f"I encountered an issue processing your question: {error}\n\nPlease try rephrasing your question or ask something else about Samsung phones."
        
        return {
            "final_answer": answer,
            "messages": [AIMessage(content=answer)]
        }
    
    def check_sql_valid(self, state: RAGState):
        """Check if SQL query was generated"""
        sql_query = state.get("sql_query", "")
        if sql_query and len(sql_query) > 10:
            return "valid"
        return "invalid"
    
    def check_results(self, state: RAGState):
        """Check if query execution was successful"""
        if state.get("error"):
            return "error"
        return "success"
    
    def _clean_sql(self, sql_text):
        """Clean SQL query from LLM response"""
        # Remove markdown code blocks
        sql = re.sub(r"```(?:sql)?|```", "", sql_text, flags=re.IGNORECASE)
        # Remove extra whitespace and semicolons
        sql = sql.strip().rstrip(";")
        return sql
    
    def ask(self, question: str, thread_id: str = "default"):
        """Ask a question and get answer"""
        config = {"configurable": {"thread_id": thread_id}}
        
        result = self.app.invoke(
            {"messages": [HumanMessage(content=question)]},
            config=config
        )
        
        return {
            "answer": result.get("final_answer", ""),
            "sql_query": result.get("sql_query", ""),
            "results": result.get("db_results", [])
        }
    
    def stream_ask(self, question: str, thread_id: str = "default"):
        """Stream the answer generation"""
        config = {"configurable": {"thread_id": thread_id}}
        
        for event in self.app.stream(
            {"messages": [HumanMessage(content=question)]},
            config=config
        ):
            yield event
    
    def get_conversation_history(self, thread_id: str):
        """Get conversation history for a thread"""
        state = self.app.get_state(
            config={"configurable": {"thread_id": thread_id}}
        )
        return state.values.get("messages", [])