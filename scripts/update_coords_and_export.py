import sqlite3
import requests
import os
import json
import random
import math
import re
from dotenv import load_dotenv

def haversine(lat1, lon1, lat2, lon2):
    R = 6371.0 # Earth radius in kilometers
    
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    
    a = math.sin(dlat / 2)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon / 2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    
    return R * c

def load_fire_stations():
    try:
        with open(r'd:\anti_gravity\nursing home\data\fire_stations.json', 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"Warning: Could not load fire stations ({e})")
        return []

FIRE_STATIONS = load_fire_stations()

def get_nearest_fire_station(lat, lon):
    if not FIRE_STATIONS or not lat or not lon:
        return None, None
        
    nearest = min(FIRE_STATIONS, key=lambda fs: haversine(lat, lon, fs['lat'], fs['lon']))
    distance = haversine(lat, lon, nearest['lat'], nearest['lon'])
    return nearest['title'], distance

load_dotenv()
vworld_key = os.getenv('VWORLD_API_KEY')
db_path = r'd:\anti_gravity\nursing home\data\nursing_facilities.db'
export_path = r'd:\anti_gravity\nursing home\dashboard\facilities.geojson'

# Ensure directory exists
os.makedirs(os.path.dirname(export_path), exist_ok=True)

def get_coords(address):
    clean_addr = address.split('(')[0].strip()
    url = 'https://api.vworld.kr/req/address'
    params = {
        'service': 'address', 'request': 'getcoord', 'version': '2.0',
        'crs': 'epsg:4326', 'address': clean_addr, 'refine': 'true',
        'simple': 'false', 'format': 'json', 'type': 'ROAD', 'key': vworld_key
    }
    try:
        resp = requests.get(url, params=params, timeout=5)
        data = resp.json()
        point = data['response']['result']['point']
        return float(point['y']), float(point['x']) # lat, lon
    except:
        return None, None

def estimate_road_width(address):
    if not address:
        return "정보 없음"
    # 도로명 주소 기반 도로폭 추정
    if re.search(r'\b대로\b', address):
        return "대로 (8차로 이상, 폭 40m~) / 소방차 진입 용이"
    elif re.search(r'\b로\b', address):
        return "로 (2~7차로, 폭 12~40m) / 소방차 전개 가능"
    elif re.search(r'\b길\b', address):
        # 복잡한 이면도로 (ex: 15길 12-4)
        if re.search(r'길\s*\d+-\d+', address):
            return "복잡한 이면도로 (폭 12m 미만) / 대형 소방차 진입 매우 곤란"
        return "일반 이면도로 (폭 12m 미만) / 소방차 진입 주의"
    return "정보 없음"

def calculate_vam(fac):
    # fac = (name, capacity, staff, address, apr_day, struct, usage, tot_area, flr_no, lat, lon)
    name, capacity, staff, address, apr_day, struct, usage, tot_area, flr_no, lat, lon = fac
    
    score = 100
    factors = {}
    
    # 1. 정량적 팩트 구성
    factors['준공연도'] = f"{str(apr_day)[:4]}년" if apr_day else "정보 없음"
    if factors['준공연도'] != "정보 없음" and str(apr_day)[:4] < '2015':
        score -= 20
        
    factors['건축구조'] = struct if struct else "정보 없음"
    if struct and '콘크리트' in struct:
        score -= 15
        
    factors['건물용도'] = usage if usage else "정보 없음"
    if usage and usage != '노유자시설':
        score -= 15
        
    area_val = f"{tot_area}㎡" if tot_area else "정보 없음"
    flr_val = f"{flr_no}층" if flr_no else "정보 없음"
    factors['건물 규모'] = f"{flr_val} (연면적: {area_val})"
        
    cap_val = capacity if capacity else "정보 없음"
    staff_val = staff if staff else "정보 없음"
    factors['정원 및 종사자'] = f"정원 {cap_val}명 / 종사자 {staff_val}명"
    
    if capacity and staff:
        staff_ratio = staff / capacity
        night_ratio = staff_ratio / 4
        factors['야간 근무자 비율'] = f"야간근무자 1인당 환자 약 {1/night_ratio:.1f}명 담당" if night_ratio > 0 else "데이터 부족"
        if night_ratio < 0.1:
            score -= 20
    else:
        factors['야간 근무자 비율'] = "정보 없음"
        
    factors['인접 도로폭'] = estimate_road_width(address)
    
    nearest_fs_name, fs_dist = get_nearest_fire_station(lat, lon)
    if fs_dist is not None:
        factors['소방서 거리'] = f"{fs_dist:.1f}km ({nearest_fs_name})"
        if fs_dist > 3.0:
            score -= 20
    else:
        factors['소방서 거리'] = "정보 없음"

    if score <= 40:
        risk_level = "최고 위험 (Extreme)"
        color = "#ef4444" # red
    elif score <= 60:
        risk_level = "고위험 (High)"
        color = "#f59e0b" # orange/yellow
    else:
        risk_level = "보통 (Moderate)"
        color = "#10b981" # green

    return {
        "score": max(0, score),
        "risk_level": risk_level,
        "color": color,
        "factors": factors
    }

def main():
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Add lat/lon if not exists
    try:
        cursor.execute("ALTER TABLE facilities ADD COLUMN lat REAL")
        cursor.execute("ALTER TABLE facilities ADD COLUMN lon REAL")
        conn.commit()
    except:
        pass
        
    cursor.execute('SELECT id, name, address, lat, lon FROM facilities WHERE lat IS NULL')
    rows = cursor.fetchall()
    
    print(f"Fetching coordinates for {len(rows)} facilities...")
    for row in rows:
        fac_id, name, address, _, _ = row
        lat, lon = get_coords(address)
        if lat and lon:
            cursor.execute('UPDATE facilities SET lat=?, lon=? WHERE id=?', (lat, lon, fac_id))
    conn.commit()
    
    # Export to GeoJSON
    cursor.execute('''
    SELECT f.name, f.capacity, f.staff_count, f.address, b.useAprDay, b.strctCdNm, b.mainPurpsCdNm, b.totArea, b.flrNo, f.lat, f.lon
    FROM facilities f 
    LEFT JOIN buildings b ON f.id = b.facility_id
    WHERE f.lat IS NOT NULL
    ''')
    
    features = []
    for row in cursor.fetchall():
        name, capacity, staff, address, apr_day, struct, usage, tot_area, flr_no, lat, lon = row
        vam = calculate_vam(row)
        
        feature = {
            "type": "Feature",
            "geometry": {
                "type": "Point",
                "coordinates": [lon, lat]
            },
            "properties": {
                "name": name,
                "address": address,
                "capacity": capacity,
                "staff": staff,
                "score": vam['score'],
                "risk_level": vam['risk_level'],
                "color": vam['color'],
                "factors": vam['factors']
            }
        }
        features.append(feature)
        
    geojson = {
        "type": "FeatureCollection",
        "features": features
    }
    
    with open(export_path, 'w', encoding='utf-8') as f:
        json.dump(geojson, f, ensure_ascii=False, indent=2)
        
    print(f"Exported {len(features)} facilities to {export_path}")
    conn.close()

if __name__ == "__main__":
    main()
