import streamlit as st
import requests
import uuid
from datetime import datetime
import json

# Configuration
API_BASE_URL = "http://localhost:8000"

# Page config
st.set_page_config(
    page_title="Phone Advisor",
    page_icon="📱",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .stApp {
        max-width: 1200px;
        margin: 0 auto;
    }
    .chat-message {
        padding: 1rem;
        border-radius: 0.5rem;
        margin-bottom: 1rem;
    }
    .user-message {
        background-color: #e3f2fd;
    }
    .assistant-message {
        background-color: #f5f5f5;
    }
    .sql-query {
        background-color: #263238;
        color: #aed581;
        padding: 0.5rem;
        border-radius: 0.25rem;
        font-family: monospace;
        font-size: 0.85rem;
    }
    .stats-card {
        background-color: #f8f9fa;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #4caf50;
    }
</style>
""", unsafe_allow_html=True)

# Utility functions
def generate_thread_id():
    return str(uuid.uuid4())

def call_api(endpoint, method="GET", data=None):
    """Make API call"""
    url = f"{API_BASE_URL}{endpoint}"
    try:
        if method == "GET":
            response = requests.get(url)
        elif method == "POST":
            response = requests.post(url, json=data)
        
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        st.error(f"API Error: {e}")
        return None

def reset_chat():
    """Reset chat session"""
    st.session_state.thread_id = generate_thread_id()
    st.session_state.messages = []
    st.session_state.chat_threads.append({
        "id": st.session_state.thread_id,
        "title": f"Chat {len(st.session_state.chat_threads) + 1}",
        "created_at": datetime.now().isoformat()
    })

def load_thread(thread_id):
    """Load conversation history from thread"""
    result = call_api(f"/thread/{thread_id}", method="GET")
    if result:
        st.session_state.thread_id = thread_id
        st.session_state.messages = result.get("messages", [])

# Initialize session state
if "thread_id" not in st.session_state:
    st.session_state.thread_id = generate_thread_id()

if "messages" not in st.session_state:
    st.session_state.messages = []

if "chat_threads" not in st.session_state:
    st.session_state.chat_threads = [{
        "id": st.session_state.thread_id,
        "title": "Chat 1",
        "created_at": datetime.now().isoformat()
    }]

if "show_sql" not in st.session_state:
    st.session_state.show_sql = False

if "show_stats" not in st.session_state:
    st.session_state.show_stats = False

# Sidebar
with st.sidebar:
    st.title("📱 Phone Advisor")
    st.markdown("---")
    
    # New chat button
    if st.button("➕ New Chat", use_container_width=True):
        reset_chat()
        st.rerun()
    
    st.markdown("---")
    
    # Settings
    st.subheader("⚙️ Settings")
    st.session_state.show_sql = st.checkbox("Show SQL Queries", value=st.session_state.show_sql)
    st.session_state.show_stats = st.checkbox("Show Statistics", value=st.session_state.show_stats)
    
    st.markdown("---")
    
    # Chat history
    st.subheader("💬 Conversations")
    for thread in reversed(st.session_state.chat_threads):
        is_current = thread["id"] == st.session_state.thread_id
        button_label = f"{'🟢 ' if is_current else ''}{thread['title']}"
        
        if st.button(button_label, key=thread["id"], use_container_width=True):
            if not is_current:
                load_thread(thread["id"])
                st.rerun()
    
    st.markdown("---")
    

# Main content
st.title("Samsung Phone Advisor")
st.markdown("Ask me anything about Samsung phones!")

# Statistics section
if st.session_state.show_stats:
    with st.expander("Database Statistics", expanded=True):
        stats = call_api("/stats")
        if stats:
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Total Phones", stats.get("total_phones", 0))
            with col2:
                st.metric("Unique Chipsets", stats.get("unique_chipsets", 0))
            with col3:
                st.metric("5G Phones", stats.get("phones_with_5g", 0))

# Example queries
if not st.session_state.messages:
    st.markdown("### 💡 Example Questions")
    
    examples_col1, examples_col2 = st.columns(2)
    
    with examples_col1:
        st.markdown("""
        - Compare Samsung Galaxy S25 Ultra and Galaxy z fold special
        - What are the performence and the photo quaily of Samsung Galaxy S25 Ultra?
        - Which Samsung phone has the best battery under $1000?
        """)
    

# Chat messages
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])
        
        # Show SQL query if available
        if message["role"] == "assistant" and st.session_state.show_sql:
            if "sql_query" in message:
                with st.expander("🔍 SQL Query"):
                    st.code(message["sql_query"], language="sql")

# Chat input
user_input = st.chat_input("Ask about Samsung phones...")

if user_input:
    # Add user message
    st.session_state.messages.append({"role": "user", "content": user_input})
    
    # Display user message
    with st.chat_message("user"):
        st.markdown(user_input)
    
    # Get AI response
    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            # Call API
            result = call_api(
                "/ask",
                method="POST",
                data={
                    "question": user_input,
                    "thread_id": st.session_state.thread_id
                }
            )
            
            if result:
                answer = result.get("answer", "Sorry, I couldn't process that.")
                sql_query = result.get("sql_query", "")
                
                # Display answer
                st.markdown(answer)
                
                # Show SQL if enabled
                if st.session_state.show_sql and sql_query:
                    with st.expander("🔍 SQL Query"):
                        st.code(sql_query, language="sql")
                
                # Show results if available
                results = result.get("results", [])
                if results and len(results) > 0:
                    with st.expander(f"📊 Query Results ({len(results)} phones)"):
                        st.json(results)
                
                # Add to message history
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": answer,
                    "sql_query": sql_query
                })
            else:
                error_msg = "Sorry, I encountered an error. Please try again."
                st.error(error_msg)
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": error_msg
                })

