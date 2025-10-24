from config import Config
from database import DatabaseManager
from scraper import PhoneScraper
from rag_agent import PhoneRAGAgent

class PhoneAdvisor:
    """Main application controller"""
    
    def __init__(self):
        self.config = Config()
        self.db = DatabaseManager(self.config)
        self.scraper = PhoneScraper(self.config)
        self.agent = None
    
    def setup_database(self):
        """Initialize database connection and tables"""
        print("\n=== Setting up database ===")
        self.db.connect()
        self.db.create_table()
        print("Database ready\n")
    
    def scrape_phones(self, limit=None):
        """Scrape phone data from GSMArena"""
        print("\n=== Starting phone scraping ===")
        phones = self.scraper.scrape_all_phones(limit=limit)
        
        if phones:
            self.scraper.save_to_json('samsung_phones.json')
            self.scraper.save_to_csv('samsung_phones.csv')
            print(f"\n✓ Scraped {len(phones)} phones successfully")
        else:
            print("✗ No phones scraped")
        
        return phones
    
    def load_data_to_database(self, json_file='samsung_phones.json'):
        """Load phone data from JSON into database"""
        print("\n=== Loading data to database ===")
        self.db.load_from_json(json_file)
        print("Data loaded successfully\n")
    
    def setup_rag_agent(self):
        """Initialize RAG agent for queries"""
        print("\n=== Setting up RAG agent ===")
        self.agent = PhoneRAGAgent(self.db, self.config)
        print("RAG agent ready\n")
    
    def ask_question(self, question):
        """Ask a natural language question about phones"""
        if not self.agent:
            self.setup_rag_agent()
        
        print(f"\nQuestion: {question}")
        print("-" * 60)
        answer = self.agent.answer_question(question)
        print(f"\nAnswer:\n{answer}\n")
        return answer
    
    def interactive_mode(self):
        """Start interactive query mode"""
        if not self.agent:
            self.setup_rag_agent()
        
        print("\n" + "="*60)
        print("Phone Advisor - Interactive Mode")
        print("="*60)
        print("Ask questions about Samsung phones (type 'exit' to quit)\n")
        
        while True:
            try:
                question = input("Your question: ").strip()
                
                if question.lower() in ['exit', 'quit', 'q']:
                    print("Goodbye!")
                    break
                
                if not question:
                    continue
                
                print("-" * 60)
                answer = self.agent.answer_question(question)
                print(f"\nAnswer:\n{answer}\n")
                
            except KeyboardInterrupt:
                print("\n\nGoodbye!")
                break
            except Exception as e:
                print(f"Error: {e}\n")
    
    def close(self):
        """Clean up resources"""
        self.db.close()


def main():
    """Main application entry point"""
    advisor = PhoneAdvisor()
    
    try:
        # Setup database
        advisor.setup_database()
        
        import os

        data_file = 'samsung_phones.json'

        if os.path.exists(data_file):
            print(f" Found existing data file: {data_file}")
            advisor.load_data_to_database(data_file)
        else:
            print(f"Data file not found! Scraping new data...")
            advisor.scrape_phones(limit=40)  
        
        
        # Setup RAG agent
        advisor.setup_rag_agent()
        
        # Example queries
        questions = [
            "Compare Galaxy S25 Ultra and M07 for photography",
            "Which phones have 5G support?",
            "Show me phones with the best battery capacity"
        ]
        
        print("\n" + "="*60)
        print("Running example queries")
        print("="*60)
        
        for question in questions:
            advisor.ask_question(question)
        
        # Start interactive mode (uncomment to use)
        # advisor.interactive_mode()
        
    except Exception as e:
        print(f"Error: {e}")
    
    finally:
        advisor.close()


if __name__ == "__main__":
    main()