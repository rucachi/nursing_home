import sqlite3
import requests
import os
import time
import math
import argparse
from dotenv import load_dotenv

load_dotenv()
VWORLD_KEY = os.getenv('VWORLD_API_KEY')
PUBLIC_DATA_KEY = os.getenv('PUBLIC_DATA_API_KEY_DECODED')

DB_PATH = r'd:\anti_gravity\nursing home\data\nursing_facilities_nationwide.db'

def setup_db():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # 마스터 테이블: 기본 정보 및 상태 관리
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS nationwide_facilities (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        facility_type TEXT, -- '요양병원' 또는 '요양원'
        name TEXT,
        address TEXT,
        sido TEXT,
        sigungu TEXT,
        capacity INTEGER DEFAULT 0,
        doctor_count INTEGER DEFAULT 0,
        nurse_count INTEGER DEFAULT 0,
        caregiver_count INTEGER DEFAULT 0,
        
        -- 수집 상태 관리 (PENDING, DONE, FAIL)
        status_vworld TEXT DEFAULT 'PENDING',
        status_arch TEXT DEFAULT 'PENDING',
        
        -- VWorld를 통해 수집될 데이터
        lat REAL,
        lon REAL,
        pnu TEXT
    )
    ''')
    
    # 건축물 정보 테이블
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS nationwide_buildings (
        facility_id INTEGER PRIMARY KEY,
        platPlc TEXT,
        mainPurpsCdNm TEXT,
        strctCdNm TEXT,
        archArea REAL,
        totArea REAL,
        flrNo INTEGER,
        useAprDay TEXT,
        totPkngCnt INTEGER,
        FOREIGN KEY(facility_id) REFERENCES nationwide_facilities(id)
    )
    ''')
    
    conn.commit()
    return conn

def seed_nursing_hospitals(conn):
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM nationwide_facilities WHERE facility_type='요양병원'")
    if cursor.fetchone()[0] > 0:
        print("요양병원 기초 데이터가 이미 존재합니다. 시드를 건너뜁니다.")
        return

    print("공공데이터포털에서 전국 요양병원 목록을 전체 수집합니다...")
    url = "http://apis.data.go.kr/B551182/hospInfoServicev2/getHospBasisList"
    
    page = 1
    total_count = 0
    while True:
        params = {
            "serviceKey": PUBLIC_DATA_KEY,
            "pageNo": str(page),
            "numOfRows": "1000",
            "clCd": "28", # 요양병원
            "_type": "json"
        }
        
        try:
            resp = requests.get(url, params=params, timeout=15)
            data = resp.json()
            items = data.get('response', {}).get('body', {}).get('items', {}).get('item', [])
            
            if not items:
                break
                
            if isinstance(items, dict): items = [items]
                
            for item in items:
                name = item.get('yadmNm', '')
                addr = item.get('addr', '')
                sido = item.get('sidoCdNm', '')
                sigungu = item.get('sgguCdNm', '')
                dr_tot = item.get('drTotCnt', 0)
                
                cursor.execute('''
                    INSERT INTO nationwide_facilities (facility_type, name, address, sido, sigungu, doctor_count)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', ('요양병원', name, addr, sido, sigungu, dr_tot))
                total_count += 1
                
            conn.commit()
            print(f"요양병원 시드 진행 중... 현재 {total_count}건 수집 (페이지 {page})")
            page += 1
            time.sleep(0.5)
        except Exception as e:
            print(f"요양병원 시드 오류 (페이지 {page}): {e}")
            break
            
    print(f"요양병원 {total_count}건 전국 시드 완료!")

def process_vworld(conn, limit=100):
    cursor = conn.cursor()
    cursor.execute('''
        SELECT id, address FROM nationwide_facilities 
        WHERE status_vworld = 'PENDING' LIMIT ?
    ''', (limit,))
    rows = cursor.fetchall()
    
    if not rows:
        print("VWorld 수집 대기 중인 데이터가 없습니다.")
        return

    print(f"VWorld 공간 정보 수집 시작 ({len(rows)}건)...")
    url = 'https://api.vworld.kr/req/search'
    
    success, fail = 0, 0
    for fac_id, address in rows:
        if not address:
            cursor.execute("UPDATE nationwide_facilities SET status_vworld='FAIL' WHERE id=?", (fac_id,))
            fail += 1
            continue
            
        clean_addr = address.split('(')[0].strip()
        params = {
            'service': 'search', 'request': 'search', 'version': '2.0',
            'crs': 'EPSG:4326', 'size': '1', 'page': '1', 'query': clean_addr,
            'type': 'address', 'category': 'road', 'format': 'json',
            'errorformat': 'json', 'key': VWORLD_KEY
        }
        
        try:
            resp = requests.get(url, params=params, timeout=5)
            data = resp.json()
            if data.get('response', {}).get('status') == 'OK':
                items = data['response']['result']['items']
                if items:
                    pnu = items[0]['id']
                    lon, lat = float(items[0]['point']['x']), float(items[0]['point']['y'])
                    cursor.execute('''
                        UPDATE nationwide_facilities 
                        SET status_vworld='DONE', pnu=?, lat=?, lon=?
                        WHERE id=?
                    ''', (pnu, lat, lon, fac_id))
                    success += 1
                else:
                    cursor.execute("UPDATE nationwide_facilities SET status_vworld='FAIL' WHERE id=?", (fac_id,))
                    fail += 1
            else:
                cursor.execute("UPDATE nationwide_facilities SET status_vworld='FAIL' WHERE id=?", (fac_id,))
                fail += 1
        except Exception as e:
            print(f"[{fac_id}] API 오류: {e}")
            # 예기치 않은 오류 발생 시 잠시 후 재시도를 위해 PENDING 유지
            break 
            
        time.sleep(0.1) # 트래픽 조절 제한 방지
        
    conn.commit()
    print(f"VWorld 수집 종료 (성공: {success}, 실패: {fail})")

def process_archhub(conn, limit=100):
    cursor = conn.cursor()
    cursor.execute('''
        SELECT id, pnu FROM nationwide_facilities 
        WHERE status_vworld = 'DONE' AND status_arch = 'PENDING' AND pnu IS NOT NULL
        LIMIT ?
    ''', (limit,))
    rows = cursor.fetchall()
    
    if not rows:
        print("ArchHub 수집 대기 중인 데이터가 없습니다.")
        return

    print(f"ArchHub 건축물 정보 수집 시작 ({len(rows)}건)...")
    url = "https://apis.data.go.kr/1613000/ArchPmsHubService/getApBasisOulnInfo"
    
    success, fail = 0, 0
    for fac_id, pnu in rows:
        if len(pnu) != 19:
            cursor.execute("UPDATE nationwide_facilities SET status_arch='FAIL' WHERE id=?", (fac_id,))
            fail += 1
            continue
            
        sigunguCd, bjdongCd = pnu[0:5], pnu[5:10]
        platGbCd = "0" if pnu[10:11] == "1" else "1"
        bun, ji = pnu[11:15], pnu[15:19]
        
        params = {
            "serviceKey": PUBLIC_DATA_KEY,
            "sigunguCd": sigunguCd, "bjdongCd": bjdongCd, "platGbCd": platGbCd,
            "bun": bun, "ji": ji, "numOfRows": "10", "pageNo": "1", "_type": "json"
        }
        
        try:
            resp = requests.get(url, params=params, timeout=5)
            data = resp.json()
            items = data.get('response', {}).get('body', {}).get('items', {}).get('item', [])
            
            if isinstance(items, dict): items = [items]
                
            if items:
                b_info = items[0]
                cursor.execute('''
                    INSERT INTO nationwide_buildings (
                        facility_id, platPlc, mainPurpsCdNm, strctCdNm, archArea, totArea, flrNo, useAprDay, totPkngCnt
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    fac_id, b_info.get('platPlc', ''), b_info.get('mainPurpsCdNm', ''), b_info.get('strctCdNm', ''),
                    b_info.get('archArea', 0), b_info.get('totArea', 0), b_info.get('flrNo', 0),
                    b_info.get('useAprDay', ''), b_info.get('totPkngCnt', 0)
                ))
                cursor.execute("UPDATE nationwide_facilities SET status_arch='DONE' WHERE id=?", (fac_id,))
                success += 1
            else:
                cursor.execute("UPDATE nationwide_facilities SET status_arch='FAIL' WHERE id=?", (fac_id,))
                fail += 1
        except Exception as e:
            print(f"[{fac_id}] API 오류 (트래픽 초과 가능성): {e}")
            break # 트래픽 제한 걸렸을 가능성이 높으므로 루프 탈출
            
        time.sleep(0.3) # ArchHub는 트래픽 제한이 빡세므로 충분히 쉼
        
    conn.commit()
    print(f"ArchHub 수집 종료 (성공: {success}, 실패: {fail})")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="전국 요양시설 데이터 파이프라인")
    parser.add_argument('--limit', type=int, default=500, help='한 번에 처리할 개수')
    parser.add_argument('--seed', action='store_true', help='기초 데이터 시딩 실행')
    parser.add_argument('--loop', action='store_true', help='무한 루프 모드 (전체 처리 완료 시까지)')
    args = parser.parse_args()
    
    conn = setup_db()
    
    if args.seed:
        seed_nursing_hospitals(conn)
        
    if args.loop:
        print("무한 루프(Goal) 모드로 실행합니다. 트래픽에 유의하며 잔여 데이터가 없을 때까지 실행합니다.")
        iteration = 1
        while True:
            print(f"\n--- [루프 {iteration}] 수집 시작 ---")
            
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM nationwide_facilities WHERE status_vworld='PENDING'")
            vworld_pending = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM nationwide_facilities WHERE status_vworld='DONE' AND status_arch='PENDING' AND pnu IS NOT NULL")
            arch_pending = cursor.fetchone()[0]
            
            print(f"현재 남은 대기 건수 - VWorld: {vworld_pending}건, ArchHub: {arch_pending}건")
            
            if vworld_pending == 0 and arch_pending == 0:
                print("모든 수집이 완료되었습니다!")
                break
                
            process_vworld(conn, limit=args.limit)
            process_archhub(conn, limit=args.limit)
            iteration += 1
            print("다음 루프를 위해 잠시 대기합니다 (10초)...")
            time.sleep(10)
    else:
        process_vworld(conn, limit=args.limit)
        process_archhub(conn, limit=args.limit)
        print("파이프라인 1회 사이클 완료.")
        
    conn.close()
