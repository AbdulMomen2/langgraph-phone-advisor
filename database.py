import psycopg2
from psycopg2 import sql, extras
import json

class DatabaseManager:
    """Handles all database operations"""
    
    def __init__(self, config):
        self.config = config
        self.conn = None
        self.cursor = None
    
    def connect(self):
        """Establish database connection"""
        try:
            params = self.config.get_db_params()
            self.conn = psycopg2.connect(**params)
            self.cursor = self.conn.cursor()
            print("✓ Connected to database")
            return True
        except psycopg2.OperationalError as e:
            if "does not exist" in str(e):
                print(f"Database doesn't exist. Creating...")
                self._create_database()
                return self.connect()
            else:
                print(f"✗ Connection error: {e}")
                raise
    
    def _create_database(self):
        """Create database if it doesn't exist"""
        params = self.config.get_db_params()
        db_name = params.pop('dbname')
        params['dbname'] = 'postgres'
        
        temp_conn = psycopg2.connect(**params)
        temp_conn.autocommit = True
        temp_cursor = temp_conn.cursor()
        
        temp_cursor.execute(
            sql.SQL("CREATE DATABASE {}").format(sql.Identifier(db_name))
        )
        
        temp_cursor.close()
        temp_conn.close()
        print(f"✓ Database '{db_name}' created")
    
    def create_table(self):
        """Create samsung_phones table"""
        query = """
        CREATE TABLE IF NOT EXISTS samsung_phones (
            id SERIAL PRIMARY KEY,
            url TEXT UNIQUE,
            name VARCHAR(255),
            image_url TEXT,
            launch_announced VARCHAR(100),
            launch_status VARCHAR(100),
            network_technology TEXT,
            network_2g_bands TEXT,
            network_3g_bands TEXT,
            network_4g_bands TEXT,
            network_5g_bands TEXT,
            network_speed VARCHAR(100),
            body_dimensions VARCHAR(100),
            body_weight VARCHAR(100),
            body_build TEXT,
            body_sim TEXT,
            display_type TEXT,
            display_size VARCHAR(100),
            display_resolution VARCHAR(100),
            display_protection TEXT,
            platform_os TEXT,
            platform_chipset TEXT,
            platform_cpu TEXT,
            platform_gpu TEXT,
            memory_card_slot TEXT,
            memory_internal TEXT,
            main_camera TEXT,
            main_camera_features TEXT,
            main_camera_video TEXT,
            selfie_camera TEXT,
            selfie_camera_features TEXT,
            selfie_camera_video TEXT,
            sound_loudspeaker VARCHAR(50),
            sound_3_5mm_jack VARCHAR(50),
            comms_wlan TEXT,
            comms_bluetooth TEXT,
            comms_positioning TEXT,
            comms_nfc VARCHAR(50),
            comms_radio VARCHAR(50),
            comms_usb TEXT,
            features_sensors TEXT,
            battery_type TEXT,
            battery_charging TEXT,
            misc_colors TEXT,
            misc_models TEXT,
            misc_sar VARCHAR(100),
            misc_sar_eu VARCHAR(100),
            misc_price TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        
        CREATE INDEX IF NOT EXISTS idx_phone_name ON samsung_phones(name);
        CREATE INDEX IF NOT EXISTS idx_launch_announced ON samsung_phones(launch_announced);
        """
        
        self.cursor.execute(query)
        self.conn.commit()
        print("✓ Table created/verified")
    
    def insert_batch(self, phones_data):
        """Insert multiple phones efficiently"""
        query = """
        INSERT INTO samsung_phones (
            url, name, image_url, launch_announced, launch_status,
            network_technology, network_2g_bands, network_3g_bands, 
            network_4g_bands, network_5g_bands, network_speed,
            body_dimensions, body_weight, body_build, body_sim,
            display_type, display_size, display_resolution, display_protection,
            platform_os, platform_chipset, platform_cpu, platform_gpu,
            memory_card_slot, memory_internal,
            main_camera, main_camera_features, main_camera_video,
            selfie_camera, selfie_camera_features, selfie_camera_video,
            sound_loudspeaker, sound_3_5mm_jack,
            comms_wlan, comms_bluetooth, comms_positioning, 
            comms_nfc, comms_radio, comms_usb,
            features_sensors,
            battery_type, battery_charging,
            misc_colors, misc_models, misc_sar, misc_sar_eu, misc_price
        ) VALUES %s
        ON CONFLICT (url) DO UPDATE SET
            name = EXCLUDED.name,
            image_url = EXCLUDED.image_url,
            updated_at = CURRENT_TIMESTAMP;
        """
        
        values = [self._prepare_phone_tuple(phone) for phone in phones_data]
        
        extras.execute_values(self.cursor, query, values)
        self.conn.commit()
        print(f"✓ Inserted {len(phones_data)} phones")
    
    def _prepare_phone_tuple(self, phone):
        """Prepare phone data tuple for insertion"""
        return (
            phone.get('url', ''),
            phone.get('name', ''),
            phone.get('image_url', ''),
            phone.get('launch_announced', ''),
            phone.get('launch_status', ''),
            phone.get('network_technology', ''),
            phone.get('network_2g_bands', ''),
            phone.get('network_3g_bands', ''),
            phone.get('network_4g_bands', ''),
            phone.get('network_5g_bands', ''),
            phone.get('network_speed', ''),
            phone.get('body_dimensions', ''),
            phone.get('body_weight', ''),
            phone.get('body_build', ''),
            phone.get('body_sim', ''),
            phone.get('display_type', ''),
            phone.get('display_size', ''),
            phone.get('display_resolution', ''),
            phone.get('display_protection', ''),
            phone.get('platform_os', ''),
            phone.get('platform_chipset', ''),
            phone.get('platform_cpu', ''),
            phone.get('platform_gpu', ''),
            phone.get('memory_card_slot', ''),
            phone.get('memory_internal', ''),
            phone.get('main_camera', ''),
            phone.get('main_camera_features', ''),
            phone.get('main_camera_video', ''),
            phone.get('selfie_camera', ''),
            phone.get('selfie_camera_features', ''),
            phone.get('selfie_camera_video', ''),
            phone.get('sound_loudspeaker', ''),
            phone.get('sound_3_5mm_jack', ''),
            phone.get('comms_wlan', ''),
            phone.get('comms_bluetooth', ''),
            phone.get('comms_positioning', ''),
            phone.get('comms_nfc', ''),
            phone.get('comms_radio', ''),
            phone.get('comms_usb', ''),
            phone.get('features_sensors', ''),
            phone.get('battery_type', ''),
            phone.get('battery_charging', ''),
            phone.get('misc_colors', ''),
            phone.get('misc_models', ''),
            phone.get('misc_sar', ''),
            phone.get('misc_sar_eu', ''),
            phone.get('misc_price', '')
        )
    
    def execute_query(self, query):
        """Execute SQL query and return results as list of dicts"""
        self.cursor.execute(query)
        
        columns = [desc[0] for desc in self.cursor.description] if self.cursor.description else []
        
        try:
            results = self.cursor.fetchall()
        except psycopg2.ProgrammingError:
            results = []
        
        self.conn.commit()
        return [dict(zip(columns, row)) for row in results]
    
    def load_from_json(self, json_file):
        """Load data from JSON file and insert"""
        with open(json_file, 'r', encoding='utf-8') as f:
            phones_data = json.load(f)
        
        print(f"Loaded {len(phones_data)} phones from {json_file}")
        self.insert_batch(phones_data)
    
    def close(self):
        """Close database connection"""
        if self.cursor:
            self.cursor.close()
        if self.conn:
            self.conn.close()
            print("✓ Database connection closed")