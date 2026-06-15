import os, requests, xml.etree.ElementTree as ET
from dotenv import load_dotenv
load_dotenv()
API_KEY = os.getenv('PUBLIC_DATA_API_KEY_DECODED')

base = 'https://apis.data.go.kr/1613000/ArchPmsHubService'

# 동작 확인된 2개 오퍼레이션의 전체 필드 확인
ops = ['getApBasisOulnInfo', 'getApFlrOulnInfo']

for op in ops:
    url = f'{base}/{op}'
    params = {
        'serviceKey': API_KEY,
        'pageNo': '1',
        'numOfRows': '1',
        'sigunguCd': '11680',
        'bjdongCd': '10300',
        'platGbCd': '0',
        'bun': '0012',
        'ji': '0000',
    }
    resp = requests.get(url, params=params, timeout=10)
    root = ET.fromstring(resp.content)
    total = root.findtext('.//totalCount')
    
    print("=" * 60)
    print(f"{op} (totalCount: {total})")
    print("=" * 60)
    
    for item in root.findall('.//item')[:1]:
        for child in item:
            print(f"  {child.tag}: {child.text}")
    print()

# 추가: 요양병원 주소를 이용해서 건축정보 조회 가능한지 확인
# 먼저 요양병원 주소에서 시군구코드/법정동코드를 매핑할 수 있는지 테스트
# 부산 부산진구 개금동의 요양병원 주소로 테스트
print("=" * 60)
print("요양병원 주소 기반 건축물 조회 테스트")
print("부산 부산진구(21004) 개금동(10400)")
print("=" * 60)

url = f'{base}/getApBasisOulnInfo'
params = {
    'serviceKey': API_KEY,
    'pageNo': '1',
    'numOfRows': '5',
    'sigunguCd': '26230',  # 부산 부산진구
    'bjdongCd': '10400',   # 개금동
}
resp = requests.get(url, params=params, timeout=10)
root = ET.fromstring(resp.content)
total = root.findtext('.//totalCount')
print(f"totalCount: {total}")

for item in root.findall('.//item')[:2]:
    print("\n--- ITEM ---")
    for child in item:
        print(f"  {child.tag}: {child.text}")
