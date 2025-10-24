import re
import json
from langchain_openai import ChatOpenAI
from langchain.messages import HumanMessage, SystemMessage

class PhoneRAGAgent:
    """RAG agent for natural language phone queries"""
    
    def __init__(self, db_manager, config):
        self.db = db_manager
        self.config = config
        self.llm = ChatOpenAI(
            model_name=config.openai_model,
            temperature=0
        )
        self.schema = self._load_schema()
        self.examples = self._load_examples()
    
    def _load_schema(self):
        """Load database schema"""
        return """
        id: integer
        url: text
        name: character varying
        image_url: text
        launch_announced: character varying
        launch_status: character varying
        network_technology: text
        network_2g_bands: text
        network_3g_bands: text
        network_4g_bands: text
        network_5g_bands: text
        network_speed: character varying
        body_dimensions: character varying
        body_weight: character varying
        body_build: text
        body_sim: text
        display_type: text
        display_size: character varying
        display_resolution: character varying
        display_protection: text
        platform_os: text
        platform_chipset: text
        platform_cpu: text
        platform_gpu: text
        memory_card_slot: text
        memory_internal: text
        main_camera: text
        main_camera_features: text
        main_camera_video: text
        selfie_camera: text
        selfie_camera_features: text
        selfie_camera_video: text
        sound_loudspeaker: character varying
        sound_3_5mm_jack: character varying
        comms_wlan: text
        comms_bluetooth: text
        comms_positioning: text
        comms_nfc: character varying
        comms_radio: character varying
        comms_usb: text
        features_sensors: text
        battery_type: text
        battery_charging: text
        misc_colors: text
        misc_models: text
        misc_sar: character varying
        misc_sar_eu: character varying
        misc_price: text
        """
    
    def _load_examples(self):
        """Load few-shot examples"""
        try:
            with open("few_shot.json", "r", encoding="utf-8") as f:
                return json.load(f)
        except FileNotFoundError:
            print("Warning: few_shot.json not found. Using no examples.")
            return []
    
    def generate_sql(self, question):
        """Generate SQL query from natural language question"""
        examples_text = self._format_examples()
        prompt = self._build_sql_prompt(question, examples_text)
        
        messages = [
            SystemMessage(content=self._get_system_message()),
            HumanMessage(content=prompt)
        ]
        
        response = self.llm.invoke(messages)
        sql_query = self._clean_sql(response.content)
        
        return sql_query
    
    def _format_examples(self):
        """Format few-shot examples as text"""
        if not self.examples:
            return "No examples available."
        
        return "\n\n".join([
            f"Question: {ex['user_question']}\nSQL: {ex['sql_schema']}"
            for ex in self.examples
        ])
    
    def _build_sql_prompt(self, question, examples_text):
        """Build prompt for SQL generation"""
        return f"""
                You are an expert at converting natural language questions into PostgreSQL queries.

                DATABASE SCHEMA (table: samsung_phones):
                {self.schema}

                EXAMPLES:
                {examples_text}

                RULES:
                - Generate syntactically correct PostgreSQL only
                - Use ILIKE for case-insensitive string matching
                - Include LIMIT 5 unless specified otherwise
                - Return only the SQL query, no explanations
                - Handle comparisons and sorting appropriately

                USER QUESTION:
                {question}
                """
                
    def _get_system_message(self):
        """Get system message for SQL generation"""
        return (
            "You are a skilled SQL expert. Given a user's question and database schema, "
            "generate a single valid PostgreSQL query that retrieves the requested information. "
            "Return only the SQL query with no additional text."
        )
    
    def _clean_sql(self, sql_text):
        """Clean SQL query from LLM response"""
        sql = re.sub(r"```(?:sql)?|```", "", sql_text, flags=re.IGNORECASE)
        return sql.strip().rstrip(";")
    
    def answer_question(self, question):
        """Answer natural language question about phones"""
        sql_query = self.generate_sql(question)
        
        if not sql_query:
            return "Failed to generate SQL query."
        
        print(f"Generated SQL: {sql_query}\n")
        
        results = self.db.execute_query(sql_query)
        
        if not results:
            return "No results found for your query."
        
        summary = self._generate_summary(question, results)
        return summary
    
    def _generate_summary(self, question, results):
        """Generate natural language summary of results"""
        prompt = f"""
            You are a Samsung smartphone expert assistant.

            USER QUESTION:
            {question}

            DATABASE RESULTS:
            {json.dumps(results, indent=2)}

            TASK:
            - Explain the results in clear, simple English
            - Highlight key specifications and differences
            - Keep the response under 150 words unless more detail is needed
            - Be conversational and helpful
            - Do not mention SQL or databases
            """
        
        messages = [
            SystemMessage(content=(
                "You are a helpful assistant that explains smartphone specifications "
                "in natural, user-friendly language."
            )),
            HumanMessage(content=prompt)
        ]
        
        response = self.llm.invoke(messages)
        return response.content.strip()