from bs4 import BeautifulSoup
import requests
import time
import json
import csv
from urllib.parse import urljoin

class PhoneScraper:
    """Scrapes phone data from GSMArena"""
    
    def __init__(self, config):
        self.config = config
        self.headers = {'User-Agent': config.user_agent}
        self.phones_data = []
    
    def get_all_phone_links(self):
        """Get all phone links from listing pages"""
        all_links = []
        page_num = 1
        
        while True:
            url = self._build_page_url(page_num)
            print(f"Fetching page {page_num}...")
            
            soup = self._fetch_page(url)
            if not soup:
                break
            
            page_links = self._extract_phone_links(soup)
            if not page_links:
                print(f"No phones found on page {page_num}. Stopping.")
                break
            
            all_links.extend(page_links)
            print(f"Found {len(page_links)} phones on page {page_num}")
            
            page_num += 1
            time.sleep(1)
        
        print(f"\nTotal phones found: {len(all_links)}")
        return all_links
    
    def _build_page_url(self, page_num):
        """Build URL for specific page number"""
        if page_num == 1:
            return self.config.samsung_url
        return f"https://www.gsmarena.com/samsung-phones-f-9-0-p{page_num}.php"
    
    def _fetch_page(self, url):
        """Fetch and parse HTML page"""
        try:
            response = requests.get(url, headers=self.headers, timeout=10)
            response.raise_for_status()
            return BeautifulSoup(response.content, 'html.parser')
        except requests.RequestException as e:
            print(f"Error fetching {url}: {e}")
            return None
    
    def _extract_phone_links(self, soup):
        """Extract phone links from page"""
        links = []
        phone_divs = soup.find_all('div', class_='makers')
        
        for div in phone_divs:
            for link in div.find_all('a'):
                href = link.get('href')
                phone_name_elem = link.find('strong')
                
                if href and phone_name_elem:
                    links.append({
                        'url': urljoin(self.config.base_url, href),
                        'name': phone_name_elem.text.strip()
                    })
        
        return links
    
    def scrape_phone_details(self, phone_url):
        """Scrape detailed specifications from phone page"""
        soup = self._fetch_page(phone_url)
        if not soup:
            return None
        
        phone_data = self._create_empty_phone_data(phone_url)
        self._extract_basic_info(soup, phone_data)
        self._extract_specifications(soup, phone_data)
        
        return phone_data
    
    def _create_empty_phone_data(self, url):
        """Create phone data dictionary with default values"""
        fields = [
            'url', 'name', 'image_url', 'launch_announced', 'launch_status',
            'network_technology', 'network_2g_bands', 'network_3g_bands',
            'network_4g_bands', 'network_5g_bands', 'network_speed',
            'body_dimensions', 'body_weight', 'body_build', 'body_sim',
            'display_type', 'display_size', 'display_resolution', 'display_protection',
            'platform_os', 'platform_chipset', 'platform_cpu', 'platform_gpu',
            'memory_card_slot', 'memory_internal',
            'main_camera', 'main_camera_features', 'main_camera_video',
            'selfie_camera', 'selfie_camera_features', 'selfie_camera_video',
            'sound_loudspeaker', 'sound_3_5mm_jack',
            'comms_wlan', 'comms_bluetooth', 'comms_positioning',
            'comms_nfc', 'comms_radio', 'comms_usb',
            'features_sensors', 'battery_type', 'battery_charging',
            'misc_colors', 'misc_models', 'misc_sar', 'misc_sar_eu', 'misc_price'
        ]
        return {field: '' for field in fields} | {'url': url}
    
    def _extract_basic_info(self, soup, phone_data):
        """Extract name and image"""
        title = soup.find('h1', class_='specs-phone-name-title')
        if title:
            phone_data['name'] = title.text.strip()
        
        img_div = soup.find('div', class_='specs-photo-main')
        if img_div:
            img_tag = img_div.find('img')
            if img_tag and img_tag.get('src'):
                phone_data['image_url'] = img_tag['src']
    
    def _extract_specifications(self, soup, phone_data):
        """Extract all specifications from tables"""
        tables = soup.find_all('table')
        current_section = ""
        
        for table in tables:
            for row in table.find_all('tr'):
                section = row.find('th', scope='row')
                if section:
                    current_section = section.text.strip().lower()
                    continue
                
                spec_name_elem = row.find('td', class_='ttl')
                spec_value_elem = row.find('td', class_='nfo')
                
                if spec_name_elem and spec_value_elem:
                    spec_name = spec_name_elem.text.strip().lower()
                    spec_value = spec_value_elem.text.strip()
                    self._map_specification(spec_name, spec_value, current_section, phone_data)
    
    def _map_specification(self, spec_name, spec_value, section, phone_data):
        """Map specification to phone data field"""
        mapping = {
            'technology': 'network_technology',
            '2g bands': 'network_2g_bands',
            '3g bands': 'network_3g_bands',
            '4g bands': 'network_4g_bands',
            '5g bands': 'network_5g_bands',
            'speed': 'network_speed',
            'announced': 'launch_announced',
            'status': 'launch_status',
            'dimensions': 'body_dimensions',
            'weight': 'body_weight',
            'build': 'body_build',
            'sim': 'body_sim',
            'size': 'display_size',
            'resolution': 'display_resolution',
            'protection': 'display_protection',
            'os': 'platform_os',
            'chipset': 'platform_chipset',
            'cpu': 'platform_cpu',
            'gpu': 'platform_gpu',
            'card slot': 'memory_card_slot',
            'internal': 'memory_internal',
            'loudspeaker': 'sound_loudspeaker',
            '3.5mm jack': 'sound_3_5mm_jack',
            'wlan': 'comms_wlan',
            'bluetooth': 'comms_bluetooth',
            'positioning': 'comms_positioning',
            'nfc': 'comms_nfc',
            'radio': 'comms_radio',
            'usb': 'comms_usb',
            'sensors': 'features_sensors',
            'charging': 'battery_charging',
            'colors': 'misc_colors',
            'models': 'misc_models',
            'sar': 'misc_sar',
            'sar eu': 'misc_sar_eu',
            'price': 'misc_price'
        }
        
        # Section-specific mappings
        if 'type' in spec_name:
            if section == 'display':
                phone_data['display_type'] = spec_value
            elif section == 'battery':
                phone_data['battery_type'] = spec_value
        elif spec_name in ['single', 'dual', 'triple', 'quad', 'penta', 'hexa']:
            if 'selfie' in section:
                phone_data['selfie_camera'] = spec_value
            else:
                phone_data['main_camera'] = spec_value
        elif 'features' in spec_name and 'camera' in section:
            key = 'selfie_camera_features' if 'selfie' in section else 'main_camera_features'
            phone_data[key] = spec_value
        elif 'video' in spec_name and 'camera' in section:
            key = 'selfie_camera_video' if 'selfie' in section else 'main_camera_video'
            phone_data[key] = spec_value
        else:
            for key, field in mapping.items():
                if key in spec_name:
                    phone_data[field] = spec_value
                    break
    
    def scrape_all_phones(self, limit=None):
        """Scrape all phones or up to limit"""
        phone_links = self.get_all_phone_links()
        
        if limit:
            phone_links = phone_links[:limit]
        
        total = len(phone_links)
        
        for idx, phone in enumerate(phone_links, 1):
            print(f"\nScraping {idx}/{total}: {phone['name']}")
            phone_data = self.scrape_phone_details(phone['url'])
            
            if phone_data:
                self.phones_data.append(phone_data)
            
            time.sleep(self.config.request_delay)
        
        return self.phones_data
    
    def save_to_json(self, filename='samsung_phones.json'):
        """Save data to JSON file"""
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(self.phones_data, f, indent=2, ensure_ascii=False)
        print(f"\n✓ Data saved to {filename}")
    
    def save_to_csv(self, filename='samsung_phones.csv'):
        """Save data to CSV file"""
        if not self.phones_data:
            print("No data to save")
            return
        
        with open(filename, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=self.phones_data[0].keys())
            writer.writeheader()
            writer.writerows(self.phones_data)
        
        print(f"✓ Data saved to {filename}")