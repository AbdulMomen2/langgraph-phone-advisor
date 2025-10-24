# Phone Advisor

A complete, production-ready phone specification advisor system that scrapes Samsung phone data from GSMArena and provides natural language query capabilities using **LangGraph**, **FastAPI**, and **Streamlit**.

## Project Structure

```
phone-advisor/
├── config.py              # Configuration management
├── database.py            # Database operations
├── scraper.py             # Web scraping logic
├── langgraph_agent.py     # LangGraph RAG agent with state management
├── api.py                 # FastAPI backend with REST endpoints
├── app.py                 # Streamlit frontend interface
├── main.py                # CLI application entry point
├── requirements.txt       # Project dependencies
├── few_shot.json          # Few-shot examples for SQL generation
├── .env                   # Environment variables (create this)
├── Dockerfile             # Container configuration
├── docker-compose.yml     # Multi-container setup
├── run.sh                 # Startup script
└── stop.sh                # Shutdown script
```

## Features

### Core Features

- **LangGraph RAG Workflow**: State-based pipeline with conditional routing and error handling
- **FastAPI Backend**: RESTful API with automatic OpenAPI documentation
- **Streamlit Frontend**: Interactive chat interface with conversation history
- **Web Scraping**: Automatically scrapes Samsung phone specifications from GSMArena
- **Database Storage**: Stores phone data in PostgreSQL with proper indexing
- **Natural Language Queries**: Ask questions in plain English using RAG
- **Conversation Memory**: Thread-based conversation history with InMemorySaver
- **Multiple LLM Support**: Works with OpenAI GPT-4o or Groq Llama 3.3
- **Modular Design**: Clean, maintainable code structure
- **Batch Operations**: Efficient bulk data insertion
- **Docker Support**: One-command deployment with Docker Compose

## Architecture

```
┌─────────────────────────────────────────────────────┐
│              Streamlit Frontend (app.py)             │
│          Interactive Chat & Thread Management        │
└───────────────────┬─────────────────────────────────┘
                    │ HTTP REST API
┌───────────────────▼─────────────────────────────────┐
│              FastAPI Backend (api.py)                │
│        API Routes, Request Validation, CORS          │
└───────────────────┬─────────────────────────────────┘
                    │
        ┌───────────┴──────────┐
        │                      │
┌───────▼────────┐   ┌────────▼──────────┐
│  LangGraph RAG │   │  PostgreSQL DB     │
│     Agent      │   │  (database.py)     │
│                │   │                    │
│  ┌──────────┐ │   │  samsung_phones    │
│  │Question  │ │   │  - 47+ columns     │
│  │  ↓       │ │   │  - Indexed queries │
│  │SQL Gen   │←┼───┤  - Full specs      │
│  │  ↓       │ │   └────────────────────┘
│  │Execute   │ │
│  │  ↓       │ │
│  │Answer    │ │
│  └──────────┘ │
│                │
│  LLM: GPT-4o   │
│  or Llama 3.3  │
└────────────────┘
```

### LangGraph Workflow

The RAG agent uses a state graph with conditional edges:

```
START → Extract Question → Generate SQL → [Valid?]
                                            ↓ Yes
                                      Execute Query → [Success?]
                                                        ↓ Yes
                                                  Generate Answer → END
                                            ↓ No           ↓ No
                                      Handle Error → END
```

## Setup

### Quick Start with Docker (Recommended)

```bash
# 1. Clone and setup
git clone <your-repo>
cd phone-advisor

# 2. Create environment file
cat > .env << EOF
DB_PASSWORD=secure_password
OPENAI_API_KEY=sk-your-key
GROQ_API_KEY=your-groq-key
EOF

# 3. Start all services
docker-compose up -d

# 4. Access applications
# Frontend: http://localhost:8501
# API: http://localhost:8000
# API Docs: http://localhost:8000/docs
```

### Manual Setup

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure Environment Variables

Create a `.env` file in the project root:

```env
# Database Configuration
DB_NAME=phone_advisor
DB_USER=postgres
DB_PASSWORD=your_password
DB_HOST=localhost
DB_PORT=5432

# LLM Configuration (at least one required)
OPENAI_API_KEY=sk-your-openai-api-key
GROQ_API_KEY=your-groq-api-key
OPENAI_MODEL=gpt-4o-mini
```

### 3. Create Few-Shot Examples

Create `few_shot.json` with example queries:

```json
[
  {
    "user_question": "Which phones have 5G?",
    "sql_schema": "SELECT name, network_5g_bands FROM samsung_phones WHERE network_5g_bands != '' LIMIT 5"
  },
  {
    "user_question": "Compare Galaxy S25 and S24 cameras",
    "sql_schema": "SELECT name, main_camera, selfie_camera FROM samsung_phones WHERE name ILIKE '%Galaxy S25%' OR name ILIKE '%Galaxy S24%'"
  }
]
```

### 4. Setup Database and Data

```bash
# Option 1: Use setup script (recommended)
python setup_data.py

# Option 2: Manual setup
python -c "
from config import Config
from database import DatabaseManager

config = Config()
db = DatabaseManager(config)
db.connect()
db.create_table()
db.load_from_json('samsung_phones.json')
db.close()
"
```

### 5. Start the Application

**Using startup script:**

```bash
chmod +x run.sh
./run.sh
```

**Manual start:**

```bash
# Terminal 1: Start FastAPI
uvicorn api:app --reload --port 8000

# Terminal 2: Start Streamlit
streamlit run app.py
```

## Usage

### CLI Usage (Original)

```python
from main import PhoneAdvisor

# Initialize advisor
advisor = PhoneAdvisor()

# Setup database
advisor.setup_database()

# Option 1: Scrape new data
advisor.scrape_phones(limit=10)

# Option 2: Load existing data
advisor.load_data_to_database('samsung_phones.json')

# Setup RAG agent
advisor.setup_rag_agent()

# Ask questions
advisor.ask_question("Which phones have the best cameras?")

# Interactive mode
advisor.interactive_mode()

# Clean up
advisor.close()
```

### Streamlit Interface (New)

1. Open `http://localhost:8501`
2. Type questions naturally:
   - "Compare Galaxy S25 Ultra and S24 Ultra"
   - "Which phones have 5G support?"
   - "Show me phones with 200MP cameras"
   - "What's the cheapest 5G phone?"
3. Use sidebar for:
   - Starting new conversations
   - Viewing conversation history
   - Toggling SQL query display
   - Quick query shortcuts

### FastAPI Endpoints (New)

```bash
# Health check
curl http://localhost:8000/

# Ask a question
curl -X POST http://localhost:8000/ask \
  -H "Content-Type: application/json" \
  -d '{"question": "Which phones have 5G?", "thread_id": "my-chat"}'

# Get conversation history
curl http://localhost:8000/thread/my-chat

# Search phones
curl -X POST http://localhost:8000/search \
  -H "Content-Type: application/json" \
  -d '{"query": "Galaxy S25", "limit": 5}'

# Get statistics
curl http://localhost:8000/stats

# Get popular phones
curl http://localhost:8000/phones/popular

# Get phone by ID
curl http://localhost:8000/phones/1
```

## Module Documentation

### config.py

Centralized configuration management. Loads environment variables and provides configuration objects.

**Key Methods:**

- `get_db_params()`: Returns database connection parameters

### database.py

Handles all database operations including connection, table creation, and queries.

**Key Methods:**

- `connect()`: Establish database connection
- `create_table()`: Create samsung_phones table
- `insert_batch(phones_data)`: Insert multiple phones efficiently
- `execute_query(query)`: Execute SQL and return results
- `load_from_json(json_file)`: Load data from JSON file

### scraper.py

Web scraping functionality for GSMArena.

**Key Methods:**

- `get_all_phone_links()`: Get all phone URLs from listing pages
- `scrape_phone_details(phone_url)`: Scrape specs from single phone
- `scrape_all_phones(limit=None)`: Scrape all phones or up to limit
- `save_to_json(filename)`: Save data as JSON
- `save_to_csv(filename)`: Save data as CSV

### langgraph_agent.py (New)

LangGraph-based RAG agent for natural language queries with state management.

**Key Components:**

- `RAGState`: TypedDict defining workflow state
- `PhoneRAGGraph`: Main agent class with conditional workflow
- **Nodes**: extract_question, generate_sql, execute_query, generate_answer, handle_error
- **Edges**: Conditional routing based on validation checks

**Key Methods:**

- `ask(question, thread_id)`: Get complete answer with SQL and results
- `stream_ask(question, thread_id)`: Stream answer generation
- `get_conversation_history(thread_id)`: Retrieve conversation history

### api.py (New)

FastAPI backend providing REST API endpoints.

**Endpoints:**

- `GET /`: Health check
- `POST /ask`: Ask a question (returns answer, SQL, results)
- `GET /thread/{thread_id}`: Get conversation history
- `POST /search`: Search phones by query
- `GET /phones/popular`: Get popular/recent phones
- `GET /phones/{phone_id}`: Get phone details
- `GET /stats`: Database statistics

### app.py (New)

Streamlit frontend with interactive chat interface.

**Features:**

- Real-time chat interface
- Conversation thread management
- SQL query visualization
- Quick query suggestions
- Statistics dashboard
- Search functionality

### main.py

CLI application controller that orchestrates all modules.

**Key Methods:**

- `setup_database()`: Initialize database
- `scrape_phones(limit)`: Scrape phone data
- `load_data_to_database(json_file)`: Load data to database
- `setup_rag_agent()`: Initialize RAG agent
- `ask_question(question)`: Ask a question
- `interactive_mode()`: Start interactive CLI

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure Environment Variables

Create a `.env` file in the project root:

```env
# Database Configuration
DB_NAME=phone_advisor
DB_USER=your_username
DB_PASSWORD=your_password
DB_HOST=localhost
DB_PORT=5432

# OpenAI Configuration
OPENAI_API_KEY=your_openai_api_key
OPENAI_MODEL=gpt-4o-mini
```

### 3. Create Few-Shot Examples

Create `few_shot.json` with example queries:

```json
[
  {
    "user_question": "Which phones have 5G?",
    "sql_schema": "SELECT name, network_5g_bands FROM samsung_phones WHERE network_5g_bands != '' LIMIT 5"
  },
  {
    "user_question": "Compare Galaxy S25 and S24 cameras",
    "sql_schema": "SELECT name, main_camera, selfie_camera FROM samsung_phones WHERE name ILIKE '%Galaxy S25%' OR name ILIKE '%Galaxy S24%'"
  }
]
```

## Usage

### Basic Usage

```python
from main import PhoneAdvisor

# Initialize advisor
advisor = PhoneAdvisor()

# Setup database
advisor.setup_database()

# Option 1: Scrape new data
advisor.scrape_phones(limit=10)

# Option 2: Load existing data
advisor.load_data_to_database('samsung_phones.json')

# Setup RAG agent
advisor.setup_rag_agent()

# Ask questions
advisor.ask_question("Which phones have the best cameras?")

# Interactive mode
advisor.interactive_mode()

# Clean up
advisor.close()
```

### Run the Application

```bash
python main.py
```

## Module Documentation

### config.py

Centralized configuration management. Loads environment variables and provides configuration objects.

**Key Methods:**

- `get_db_params()`: Returns database connection parameters

### database.py

Handles all database operations including connection, table creation, and queries.

**Key Methods:**

- `connect()`: Establish database connection
- `create_table()`: Create samsung_phones table
- `insert_batch(phones_data)`: Insert multiple phones efficiently
- `execute_query(query)`: Execute SQL and return results
- `load_from_json(json_file)`: Load data from JSON file

### scraper.py

Web scraping functionality for GSMArena.

**Key Methods:**

- `get_all_phone_links()`: Get all phone URLs from listing pages
- `scrape_phone_details(phone_url)`: Scrape specs from single phone
- `scrape_all_phones(limit=None)`: Scrape all phones or up to limit
- `save_to_json(filename)`: Save data as JSON
- `save_to_csv(filename)`: Save data as CSV

### rag_agent.py

RAG agent for natural language queries using LangChain and OpenAI.

**Key Methods:**

- `generate_sql(question)`: Convert natural language to SQL
- `answer_question(question)`: Answer question with natural language response

### main.py

Main application controller that orchestrates all modules.

**Key Methods:**

- `setup_database()`: Initialize database
- `scrape_phones(limit)`: Scrape phone data
- `load_data_to_database(json_file)`: Load data to database
- `setup_rag_agent()`: Initialize RAG agent
- `ask_question(question)`: Ask a question
- `interactive_mode()`: Start interactive CLI

## Database Schema

The `samsung_phones` table includes 47+ fields covering:

- Launch information
- Network capabilities (2G/3G/4G/5G)
- Body specifications
- Display details
- Platform (OS, chipset, CPU, GPU)
- Memory
- Camera specifications (main and selfie)
- Sound features
- Communications (WiFi, Bluetooth, NFC, USB)
- Battery information
- Miscellaneous (colors, models, price)

## Example Queries

```python
# Compare phones
advisor.ask_question("Compare Galaxy S25 Ultra and S24 Ultra")

# Find specific features
advisor.ask_question("Which phones have 200MP cameras?")

# Battery queries
advisor.ask_question("Show phones with best battery life")

# Price queries
advisor.ask_question("What are the cheapest 5G phones?")
```

## Best Practices

1. **Rate Limiting**: The scraper includes delays between requests to respect GSMArena's servers
2. **Error Handling**: All modules include comprehensive error handling
3. **Resource Cleanup**: Always call `advisor.close()` when done
4. **Batch Operations**: Use `insert_batch()` for multiple records instead of individual inserts
5. **Environment Variables**: Never commit `.env` file to version control

## Example Queries

### Comparison Queries

```
"Compare Galaxy S25 Ultra and S24 Ultra"
"Compare flagship phones from 2024"
"Which is better for photography: S25 or S24?"
```

### Feature Queries

```
"Which phones have 5G support?"
"Show me phones with 200MP cameras"
"Phones with wireless charging"
"Which phones have 120Hz displays?"
```

### Price Queries

```
"What are the cheapest 5G phones?"
"Phones under $500"
"Best value flagship phones"
```

### Technical Queries

```
"Which phones use Snapdragon 8 Gen 3?"
"Show phones with best battery capacity"
"Phones with AMOLED displays"
"Latest phones with fast charging"
```

## Troubleshooting

### Database Connection Issues

```bash
# Check PostgreSQL is running
sudo systemctl status postgresql

# Verify credentials in .env file
psql -U your_username -d phone_advisor

# Test connection
python -c "from config import Config; from database import DatabaseManager; db = DatabaseManager(Config()); db.connect()"
```

### API Not Starting

```bash
# Check port availability
lsof -i :8000

# Install missing dependencies
pip install -r requirements.txt --upgrade

# Check logs
tail -f logs/api.log
```

### Streamlit Connection Error

```bash
# Ensure API is running first
curl http://localhost:8000/

# Update API_BASE_URL in app.py if needed
# Default is http://localhost:8000
```

### LLM API Errors

```bash
# Verify API keys in .env
cat .env | grep API_KEY

# Test Groq API
curl https://api.groq.com/openai/v1/models \
  -H "Authorization: Bearer $GROQ_API_KEY"

# Switch LLM provider in api.py
# use_groq=True  (Groq Llama 3.3)
# use_groq=False (OpenAI GPT-4o-mini)
```

### Docker Issues

```bash
# View logs
docker-compose logs -f

# Restart services
docker-compose restart

# Rebuild images
docker-compose build --no-cache

# Remove and recreate
docker-compose down -v
docker-compose up -d
```

## Stopping the Application

```bash
# Using stop script
./stop.sh

# Using Docker
docker-compose down

# Manual shutdown
# Kill processes on ports 8000 and 8501
pkill -f "uvicorn api:app"
pkill -f "streamlit run"
```

### Database Connection Issues

- Ensure PostgreSQL is running
- Verify credentials in `.env` file
- Check if database exists (will auto-create if missing)

### Scraping Issues

- Website structure may change; update selectors in `scraper.py`
- Respect rate limits; adjust `request_delay` in config

### RAG Agent Issues

- Ensure OpenAI API key is valid
- Check `few_shot.json` exists and is valid JSON
- Verify database contains data

## License

MIT License

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request
