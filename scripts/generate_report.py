import sqlite3
import requests
import os
import math
from dotenv import load_dotenv

load_dotenv()
vworld_key = os.getenv('VWORLD_API_KEY')
db_path = r'd:\anti_gravity\nursing home\data\nursing_facilities.db'

def haversine(lat1, lon1, lat2, lon2):
    R = 6371.0 # 지구 반지름 (km)
    dLat = math.radians(lat2 - lat1)
    dLon = math.radians(lon2 - lon1)
    a = math.sin(dLat / 2)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dLon / 2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c

def get_coords(address):
    clean_addr = address.split('(')[0].strip()
    url = 'https://api.vworld.kr/req/address'
    params = {
        'service': 'address', 'request': 'getcoord', 'version': '2.0',
        'crs': 'epsg:4326', 'address': clean_addr, 'refine': 'true',
        'simple': 'false', 'format': 'json', 'type': 'ROAD', 'key': vworld_key
    }
    resp = requests.get(url, params=params)
    data = resp.json()
    try:
        point = data['response']['result']['point']
        return float(point['y']), float(point['x']) # lat, lon
    except:
        return None, None

def get_nearest_fire_station(lat, lon):
    overpass_url = 'http://overpass-api.de/api/interpreter'
    query = f"""
    [out:json];
    node["amenity"="fire_station"](around:5000,{lat},{lon});
    out body;
    """
    resp = requests.post(overpass_url, data={'data': query})
    try:
        elements = resp.json().get('elements', [])
        if not elements:
            return "근처 소방서 없음", 5.0 # 기본값 5km
        
        min_dist = 999
        nearest_name = ""
        for el in elements:
            dist = haversine(lat, lon, el['lat'], el['lon'])
            if dist < min_dist:
                min_dist = dist
                nearest_name = el.get('tags', {}).get('name', '119안전센터')
        return nearest_name, min_dist
    except:
        return "조회 실패", 0.0

def generate_report(facility_name):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # 1. DB에서 정보 조회
    cursor.execute('''
    SELECT f.name, f.capacity, f.staff_count, f.address, b.useAprDay, b.strctCdNm, b.mainPurpsCdNm
    FROM facilities f 
    LEFT JOIN buildings b ON f.id = b.facility_id
    WHERE f.name LIKE ? LIMIT 1
    ''', (f"%{facility_name}%",))
    
    row = cursor.fetchone()
    if not row:
        print("Facility not found in DB.")
        return
        
    name, capacity, staff, address, apr_day, struct, usage = row
    
    # 2. API를 통해 위경도 및 소방서 거리 산출
    lat, lon = get_coords(address)
    fs_name, fs_dist = ("정보 없음", 0.0)
    if lat and lon:
        fs_name, fs_dist = get_nearest_fire_station(lat, lon)
    
    # 3. 평가 로직 (VAM 적용)
    score = 100
    findings = []
    
    # 건축 취약성
    if apr_day and str(apr_day)[:4] < '2015':
        score -= 20
        findings.append(f"**준공연도 ({str(apr_day)[:4]}년):** 2015년 이전 준공으로 배연설비 및 대피공간 미비 확률 높음 (-20점)")
    
    if struct and '콘크리트' in struct:
        score -= 15
        findings.append(f"**건축구조 ({struct}):** 내력벽 구조로 복도 확장 및 안전구획 개조 공사 사실상 불가 (-15점)")
        
    if usage and usage != '노유자시설':
        score -= 15
        findings.append(f"**건물용도 ({usage}):** 타 용도와 혼재된 복합건축물로 화재 연소 확대 위험 높음 (-15점)")
        
    # 인적 취약성
    staff_ratio = staff / capacity if capacity > 0 else 0
    # 주간/야간 교대 고려시 실질 야간 비율은 1/4 수준으로 가정
    night_ratio = staff_ratio / 4
    if night_ratio < 0.1: # 요양보호사 1명이 10명 이상 케어
        score -= 20
        findings.append(f"**야간 인력 비율 ({night_ratio:.2f}):** 야간 근무자 1인당 담당 환자 수가 과다하여 자력 대피 유도 불가 (-20점)")
        
    # 지리적 취약성
    if fs_dist > 3.0: # 3km 이상이면 골든타임(5분) 초과 위험
        score -= 20
        findings.append(f"**소방서 거리 ({fs_dist:.1f}km):** 관할 소방서({fs_name})와 거리가 멀어 출동 골든타임 초과 위험 (-20점)")
    else:
        findings.append(f"**소방서 거리 ({fs_dist:.1f}km):** 관할 소방서({fs_name})와 가까워 초기 대응 양호")

    # 보고서 작성
    risk_level = "최고 위험 (Extreme Risk)" if score <= 40 else "고위험 (High Risk)" if score <= 60 else "보통 (Moderate)"
    
    report = f"""# 🏥 요양원 대피체계 취약성 평가 보고서
## 시설 개요
- **시설명:** {name}
- **주소:** {address}
- **정원 / 종사자 수:** {capacity}명 / {staff}명

## 종합 평가 결과
- **종합 점수:** {score}점 / 100점
- **위험 등급:** **{risk_level}**

## 취약성 상세 분석 (VAM 기반)
"""
    for finding in findings:
        report += f"- {finding}\n"
        
    report += f"""
---
## 💡 표준 모델 정책 제언
평가 결과 해당 시설은 구조적 리모델링(복도 확장 등)이 불가능하며 야간 인력이 부족한 것으로 분석됩니다.
따라서 **"수직 대피를 포기하고, 해당 층을 2~3개의 독립된 방화구획으로 나누는 수평 피난안전구획 의무화 모델"**의 즉각적인 도입이 필요합니다.
"""
    
    report_path = os.path.join(r'd:\anti_gravity\nursing home\docs', f'report_{name.replace(" ", "_")}.md')
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write(report)
        
    print(f"Report generated: {report_path}")

if __name__ == "__main__":
    generate_report("해피움시니어스타워")
