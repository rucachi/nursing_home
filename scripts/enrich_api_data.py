import sqlite3
import requests
import os
import urllib.parse
from dotenv import load_dotenv

load_dotenv()
vworld_key = os.getenv('VWORLD_API_KEY')
arch_api_key = os.getenv('PUBLIC_DATA_API_KEY_DECODED')

db_path = r'd:\anti_gravity\nursing home\data\nursing_facilities.db'

def setup_db():
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS buildings (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        facility_id INTEGER,
        pnu TEXT,
        platPlc TEXT,
        mainPurpsCdNm TEXT,
        strctCdNm TEXT,
        archArea REAL,
        totArea REAL,
        flrNo INTEGER,
        archPmsDay TEXT,
        useAprDay TEXT,
        totPkngCnt INTEGER,
        FOREIGN KEY(facility_id) REFERENCES facilities(id)
    )
    ''')
    conn.commit()
    return conn

def get_pnu_from_address(address):
    # 주소 정제 (예: "종로구 비봉길 76 (구기동)" -> "종로구 비봉길 76")
    clean_addr = address.split('(')[0].strip()
    
    url = 'https://api.vworld.kr/req/search'
    params = {
        'service': 'search',
        'request': 'search',
        'version': '2.0',
        'crs': 'EPSG:4326',
        'size': '1',
        'page': '1',
        'query': clean_addr,
        'type': 'address',
        'category': 'road',
        'format': 'json',
        'errorformat': 'json',
        'key': vworld_key
    }
    
    try:
        resp = requests.get(url, params=params, timeout=5)
        data = resp.json()
        if data.get('response', {}).get('status') == 'OK':
            items = data['response']['result']['items']
            if items:
                return items[0]['id'] # 19-digit PNU
    except Exception as e:
        print(f"VWorld Error for {clean_addr}: {e}")
    return None

def get_building_info(pnu):
    if not pnu or len(pnu) != 19:
        return None
        
    sigunguCd = pnu[0:5]
    bjdongCd = pnu[5:10]
    platGbCd = "0" if pnu[10:11] == "1" else "1"
    bun = pnu[11:15]
    ji = pnu[15:19]
    
    url = "https://apis.data.go.kr/1613000/ArchPmsHubService/getApBasisOulnInfo"
    params = {
        "serviceKey": arch_api_key,
        "sigunguCd": sigunguCd,
        "bjdongCd": bjdongCd,
        "platGbCd": platGbCd,
        "bun": bun,
        "ji": ji,
        "numOfRows": "10",
        "pageNo": "1",
        "_type": "json"
    }
    
    try:
        resp = requests.get(url, params=params, timeout=5)
        data = resp.json()
        items = data.get('response', {}).get('body', {}).get('items', {}).get('item', [])
        
        # item이 단일 객체인 경우 리스트로 래핑
        if isinstance(items, dict):
            items = [items]
            
        if items:
            # 첫 번째 건물 정보 사용
            return items[0]
    except Exception as e:
        print(f"ArchHUB Error for PNU {pnu}: {e}")
    return None

def main():
    conn = setup_db()
    cursor = conn.cursor()
    
    cursor.execute('SELECT id, name, address FROM facilities')
    facilities = cursor.fetchall()
    
    print(f"Enriching {len(facilities)} facilities...")
    success_count = 0
    
    # 10개 샘플 제한 해제하여 전체 시설 조회
    for i, fac in enumerate(facilities):
        fac_id, name, address = fac
        pnu = get_pnu_from_address(address)
        if pnu:
            b_info = get_building_info(pnu)
            if b_info:
                cursor.execute('''
                INSERT INTO buildings (
                    facility_id, pnu, platPlc, mainPurpsCdNm, strctCdNm, 
                    archArea, totArea, flrNo, archPmsDay, useAprDay, totPkngCnt
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    fac_id, pnu,
                    b_info.get('platPlc', ''),
                    b_info.get('mainPurpsCdNm', ''),
                    b_info.get('strctCdNm', ''),
                    b_info.get('archArea', 0),
                    b_info.get('totArea', 0),
                    b_info.get('flrNo', 0),
                    b_info.get('archPmsDay', ''),
                    b_info.get('useAprDay', ''),
                    b_info.get('totPkngCnt', 0)
                ))
                conn.commit()
                success_count += 1
                print(f"[{i+1}/10] Success: {name} -> {b_info.get('mainPurpsCdNm', '')} (연면적 {b_info.get('totArea', 0)})")
            else:
                print(f"[{i+1}/10] ArchHUB failed for {name} (PNU: {pnu})")
        else:
            print(f"[{i+1}/10] VWorld failed for {name} (Addr: {address})")
            
    conn.commit()
    conn.close()
    print(f"Done. Successfully enriched {success_count} facilities.")

if __name__ == "__main__":
    main()
