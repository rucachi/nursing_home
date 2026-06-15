import os, requests, xml.etree.ElementTree as ET, json
from dotenv import load_dotenv
load_dotenv()
API_KEY_DECODED = os.getenv('PUBLIC_DATA_API_KEY_DECODED')
API_KEY_ENCODED = os.getenv('PUBLIC_DATA_API_KEY_ENCODED')

base = 'https://apis.data.go.kr/1613000/ArchPmsHubService'

# 403이 뜬 2개 오퍼레이션에 대해 다양한 파라미터 조합 시도
ops_to_test = ['getApBasisOulnInfo', 'getApFlrOulnInfo']

print("=" * 60)
print("403 오퍼레이션 상세 테스트")
print("=" * 60)

# 테스트 1: Encoded 키 사용
for op in ops_to_test:
    url = f'{base}/{op}'
    params = {
        'serviceKey': API_KEY_ENCODED,
        'pageNo': '1',
        'numOfRows': '2',
        'sigunguCd': '11680',
        'bjdongCd': '10300',
    }
    resp = requests.get(url, params=params, timeout=10)
    print(f"\n[{resp.status_code}] {op} (Encoded Key)")
    print(f"  {resp.text[:500]}")

# 테스트 2: Decoded 키 + type=json
for op in ops_to_test:
    url = f'{base}/{op}'
    params = {
        'serviceKey': API_KEY_DECODED,
        'pageNo': '1',
        'numOfRows': '2',
        'sigunguCd': '11680',
        'bjdongCd': '10300',
        'type': 'json',
    }
    resp = requests.get(url, params=params, timeout=10)
    print(f"\n[{resp.status_code}] {op} (Decoded + json)")
    print(f"  {resp.text[:500]}")

# 테스트 3: 파라미터 없이
for op in ops_to_test:
    url = f'{base}/{op}'
    params = {
        'serviceKey': API_KEY_DECODED,
    }
    resp = requests.get(url, params=params, timeout=10)
    print(f"\n[{resp.status_code}] {op} (키만)")
    print(f"  {resp.text[:500]}")

# 테스트 4: 다른 파라미터명 시도 (platGbCd 등)
for op in ops_to_test:
    url = f'{base}/{op}'
    params = {
        'serviceKey': API_KEY_DECODED,
        'pageNo': '1',
        'numOfRows': '2',
        'sigunguCd': '11680',
        'bjdongCd': '10300',
        'platGbCd': '0',
        'bun': '0012',
        'ji': '0000',
    }
    resp = requests.get(url, params=params, timeout=10)
    print(f"\n[{resp.status_code}] {op} (상세 파라미터)")
    text = resp.text[:800]
    print(f"  {text}")
    
    if resp.status_code == 200 and '<?xml' in text[:50]:
        try:
            root = ET.fromstring(resp.content)
            total = root.findtext('.//totalCount')
            print(f"  >>> totalCount: {total}")
            for item in root.findall('.//{*}item')[:1]:
                print("  >>> [필드 목록]")
                for child in item:
                    tag = child.tag.split('}')[-1] if '}' in child.tag else child.tag
                    print(f"      {tag}: {child.text}")
        except:
            pass
