import os
import json
import requests
import time
from dotenv import load_dotenv

load_dotenv(r'd:\anti_gravity\nursing home\.env')
VWORLD_API_KEY = os.getenv('VWORLD_API_KEY')

def fetch_all_fire_stations():
    url = 'http://api.vworld.kr/req/search'
    fire_stations = []
    
    queries = ['119안전센터', '소방서']
    
    for query in queries:
        page = 1
        while True:
            params = {
                'service': 'search',
                'request': 'search',
                'version': '2.0',
                'crs': 'EPSG:4326',
                'size': '100',
                'page': str(page),
                'query': query,
                'type': 'PLACE',
                'format': 'json',
                'errorformat': 'json',
                'key': VWORLD_API_KEY
            }
            
            resp = requests.get(url, params=params)
            data = resp.json()
            
            if 'response' not in data or 'result' not in data['response']:
                break
                
            items = data['response']['result'].get('items', [])
            if not items:
                break
                
            for item in items:
                category = item.get('category', '')
                title = item.get('title', '')
                
                # 버스정류장 등 노이즈 필터링
                if '정류장' in category or '정류소' in category:
                    continue
                if '소방서' not in title and '119안전센터' not in title and '119지역대' not in title:
                    continue
                    
                fire_stations.append({
                    'id': item['id'],
                    'title': title,
                    'address': item.get('address', {}).get('road', '') or item.get('address', {}).get('parcel', ''),
                    'lat': float(item['point']['y']),
                    'lon': float(item['point']['x'])
                })
                
            total_pages = int(data['response']['page']['total'])
            if page >= total_pages:
                break
            page += 1
            time.sleep(0.1) # Rate limit 방지
            
    # 중복 제거 (id 기준)
    unique_stations = {fs['id']: fs for fs in fire_stations}.values()
    
    output_path = r'd:\anti_gravity\nursing home\data\fire_stations.json'
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(list(unique_stations), f, ensure_ascii=False, indent=2)
        
    print(f"Successfully saved {len(unique_stations)} fire stations to {output_path}")

if __name__ == '__main__':
    fetch_all_fire_stations()
