# Phone Advisor

A modular phone specification advisor system that scrapes Samsung phone data from GSMArena and provides natural language query capabilities using RAG (Retrieval Augmented Generation).

## Project Structure

```
phone-advisor/
├── config.py           # Configuration management
├── database.py         # Database operations
├── scraper.py          # Web scraping logic
├── rag_agent.py        # RAG agent for NL queries
├── main.py             # Main application entry point
├── requirements.txt    # Project dependencies
├── .env                # Environment variables (create this)
└── few_shot.json       # Few-shot examples for SQL generation
```

## Features

- **Web Scraping**: Automatically scrapes Samsung phone specifications from GSMArena
- **Database Storage**: Stores phone data in PostgreSQL with proper indexing
- **Natural Language Queries**: Ask questions in plain English using RAG
- **Modular Design**: Clean, maintainable code structure
- **Batch Operations**: Efficient bulk data insertion

## Setup

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

## Troubleshooting

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
