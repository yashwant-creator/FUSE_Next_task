import requests
import re
from datetime import datetime
from typing import Dict, Any, List

SETTINGS = {
    "api_url": "https://www.aisc.org/jsonexport.aspx",
    "static_fields": {
        "doc_type": "AISC.org"
    },
    "html_tag_pattern": re.compile(r'<[^>]+>')
}

def fetch_data(url: str) -> List[Dict[str, Any]]:
    try:
        browser_disguise = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        http_response = requests.get(url, headers=browser_disguise)
        http_response.raise_for_status()
        
        print(f"Response status: {http_response.status_code}")
        print(f"Content type: {http_response.headers.get('Content-Type')}")
        print(f"Content length: {len(http_response.content)} bytes")
        
        return http_response.json()
    except requests.RequestException as oops:
        print(f"Error fetching data: {oops}")
        print(f"Response status code: {getattr(oops.response, 'status_code', 'N/A')}")
        return []


def sanitize_html(messy_text: str) -> str:
    if not isinstance(messy_text, str):
        return messy_text
    
    scrubbed = SETTINGS["html_tag_pattern"].sub('', messy_text)
    return scrubbed.strip()


def parse_date(date_string: str) -> datetime:
    try:
        time_travel_string = date_string.replace('Z', '+00:00')
        return datetime.fromisoformat(time_travel_string)
    except (ValueError, AttributeError):
        return datetime.now()


def process_field(field_name: str, field_value: Any) -> tuple:
    looks_like_a_date = isinstance(field_value, str) and (
        'date' in field_name.lower() or 
        re.match(r'\d{4}-\d{2}-\d{2}', field_value)
    )
    
    if looks_like_a_date:
        fancy_field_name = f"{field_name}_date"
        return fancy_field_name, parse_date(field_value)
    
    elif isinstance(field_value, dict):
        nested_treasure = {}
        for k, v in field_value.items():
            transformed_key, transformed_value = process_field(k, v)
            nested_treasure[transformed_key] = transformed_value
        return f"{field_name}_obj", nested_treasure
    
    elif isinstance(field_value, str):
        return field_name, sanitize_html(field_value)
    
    else:
        return field_name, field_value


def create_series(item: Dict[str, Any], item_id: Any) -> Dict[str, Any]:
    field_bucket = {}
    
    for attr_name, attr_value in item.items():
        spicy_name, spicy_value = process_field(attr_name, attr_value)
        field_bucket[spicy_name] = spicy_value
    
    field_bucket.update(SETTINGS["static_fields"])
    
    shiny_series = {
        "series_id": f"AISC\\{item_id}",
        "fields": field_bucket
    }
    
    return shiny_series


def process():
    """This function is the main entry point of the script. 
    It should retrieve and process data. Create as many functions as necessary.
    """
    print("Starting data processing...")
    
    data_payload = fetch_data(SETTINGS["api_url"])
    
    if not data_payload:
        print("No data retrieved. Exiting.")
        return False
    
    print(f"Retrieved {len(data_payload)} items.")
    
    for idx, data_chunk in enumerate(data_payload):
        chunk_id = data_chunk.get('id', idx)
        magical_series = create_series(data_chunk, chunk_id)
        print(magical_series)
    
    print("\nProcessing complete!")
    return True

if __name__ == '__main__':
    process()
