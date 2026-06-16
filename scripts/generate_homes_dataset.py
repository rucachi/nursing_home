import sqlite3
import pandas as pd
import json
import math
import re
import os

DB_PATH = r'd:\anti_gravity\nursing home\data\nursing_facilities_nationwide.db'
FIRE_STATIONS_PATH = r'd:\anti_gravity\nursing home\data\fire_stations.json'
OUTPUT_CSV = r'd:\anti_gravity\nursing home\data\nationwide_nursing_homes_analysis.csv'

def haversine(lat1, lon1, lat2, lon2):
    R = 6371.0 # Earth radius in kilometers
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = math.sin(dlat / 2)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon / 2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c

def load_fire_stations():
    try:
        with open(FIRE_STATIONS_PATH, 'r', encoding='utf-8') as f:
            return json.load(f)
    except:
        return []

FIRE_STATIONS = load_fire_stations()

def get_nearest_fire_station_dist(lat, lon):
    if not FIRE_STATIONS or pd.isna(lat) or pd.isna(lon):
        return None
    nearest = min(FIRE_STATIONS, key=lambda fs: haversine(lat, lon, fs['lat'], fs['lon']))
    return haversine(lat, lon, nearest['lat'], nearest['lon'])

def estimate_road_width(address):
    if not address or pd.isna(address):
        return "정보 없음"
    if re.search(r'\b대로\b', address): return "대로"
    elif re.search(r'\b로\b', address): return "로"
    elif re.search(r'\b길\b', address): return "길"
    return "기타"

def get_scale_group(capacity):
    if pd.isna(capacity) or capacity == 0: return "미상"
    if capacity >= 50: return "대규모 (50인 이상)"
    elif capacity >= 10: return "중규모 (10~49인)"
    else: return "소규모 (10인 미만)"

def get_distance_group(dist):
    if pd.isna(dist): return "미상"
    if dist < 1.0: return "근거리 (1km 미만)"
    elif dist <= 3.0: return "중거리 (1~3km)"
    else: return "원거리 (3km 초과)"

def get_age_group(apr_day):
    if not apr_day or pd.isna(apr_day): return "미상"
    try:
        year = int(str(apr_day)[:4])
        if year < 2000: return "노후 (2000년 이전)"
        elif year <= 2015: return "일반 (2000~2015년)"
        else: return "신축 (2015년 이후)"
    except:
        return "미상"

def calculate_vam_score(row):
    score = 100
    apr_day = row['useAprDay']
    struct = row['strctCdNm']
    usage = row['mainPurpsCdNm']
    capacity = row['capacity']
    caregiver = row['caregiver_count']
    dist = row['fire_station_dist_km']
    
    if pd.notna(apr_day) and str(apr_day)[:4] < '2015': score -= 20
    if pd.notna(struct) and '콘크리트' in struct: score -= 15
    if pd.notna(usage) and usage != '노유자시설': score -= 15
    if pd.notna(capacity) and pd.notna(caregiver) and capacity > 0:
        caregiver_ratio = caregiver / capacity
        night_ratio = caregiver_ratio / 4
        if night_ratio < 0.1: score -= 20
    if pd.notna(dist) and dist > 3.0: score -= 20
        
    return max(0, score)

def main():
    print("Loading nationwide nursing homes from database...")
    conn = sqlite3.connect(DB_PATH)
    query = '''
        SELECT f.id, f.facility_type, f.name, f.sido, f.sigungu, f.address, 
               f.capacity, f.caregiver_count, f.lat, f.lon, 
               b.useAprDay, b.strctCdNm, b.mainPurpsCdNm, b.totArea, b.flrNo
        FROM nationwide_facilities f 
        LEFT JOIN nationwide_buildings b ON f.id = b.facility_id
        WHERE f.status_vworld = 'DONE' AND f.facility_type = '요양원'
    '''
    df = pd.read_sql_query(query, conn)
    conn.close()

    print("Generating derived variables...")
    # 소방서 거리 산출
    df['fire_station_dist_km'] = df.apply(lambda r: get_nearest_fire_station_dist(r['lat'], r['lon']), axis=1)
    
    # 카테고리화 (요양원은 정원 데이터가 있음)
    df['scale_group'] = df['capacity'].apply(get_scale_group)
    df['distance_group'] = df['fire_station_dist_km'].apply(get_distance_group)
    df['age_group'] = df['useAprDay'].apply(get_age_group)
    df['road_type'] = df['address'].apply(estimate_road_width)
    
    # VAM 점수 산출
    df['vam_score'] = df.apply(calculate_vam_score, axis=1)
    
    print("Saving dataset to CSV...")
    df.to_csv(OUTPUT_CSV, index=False, encoding='utf-8-sig')
    
    print(f"Nationwide Nursing Homes Dataset generated successfully! ({len(df)} rows)")

if __name__ == "__main__":
    main()
