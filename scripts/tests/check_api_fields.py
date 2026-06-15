import os, requests, xml.etree.ElementTree as ET
from dotenv import load_dotenv
load_dotenv()
API_KEY = os.getenv('PUBLIC_DATA_API_KEY_DECODED')

# ============================================
# 1. 병원정보서비스 - 요양병원(clCd=28) 상세 필드 확인
# ============================================
print("=" * 60)
print("1. 건강보험심사평가원 병원정보서비스 - 요양병원")
print("=" * 60)

url = 'https://apis.data.go.kr/B551182/hospInfoServicev2/getHospBasisList'
params = {
    'serviceKey': API_KEY,
    'pageNo': '1',
    'numOfRows': '3',
    'clCd': '28',
}
resp = requests.get(url, params=params)
root = ET.fromstring(resp.content)
total = root.findtext('.//totalCount')
print(f"전국 요양병원 수: {total}개\n")

for i, item in enumerate(root.findall('.//item')):
    name = item.findtext('yadmNm', '')
    print(f"--- [{i+1}] {name} ---")
    for child in item:
        print(f"  {child.tag}: {child.text}")
    print()

# ============================================
# 2. 장기요양기관 API 재시도 (다른 오퍼레이션들)
# ============================================
print("=" * 60)
print("2. 장기요양기관 API 탐색")
print("=" * 60)

# 가능한 서비스 목록 시도
services = [
    ('B550928', 'getLtcInsttDetailInfoService', 'getLtcInsttDetailInfo'),
    ('B550928', 'getLtcInsttDetailInfoService', 'getLtcInsttList'),
    ('B550928', 'getLtcInsttDetailInfoService02', 'getLtcInsttDetailInfo02'),
    ('B550928', 'searchLtcInsttService', 'searchLtcInsttList'),
    ('B550928', 'searchLtcInsttService', 'getLtcInsttSeDetail'),
]

for org, svc, op in services:
    url = f'https://apis.data.go.kr/{org}/{svc}/{op}'
    params = {'serviceKey': API_KEY, 'pageNo': '1', 'numOfRows': '2'}
    try:
        resp = requests.get(url, params=params, timeout=10)
        status = resp.status_code
        text = resp.text[:300]
        print(f"\n[{status}] {svc}/{op}")
        
        if status == 200 and '<?xml' in text:
            try:
                r = ET.fromstring(resp.content)
                code = r.findtext('.//resultCode')
                msg = r.findtext('.//resultMsg')
                total = r.findtext('.//totalCount')
                print(f"  resultCode={code}, msg={msg}, total={total}")
                
                # 필드 목록 출력
                for item in r.findall('.//item')[:1]:
                    print("  [필드 목록]")
                    for child in item:
                        print(f"    {child.tag}: {child.text}")
            except:
                print(f"  {text[:200]}")
        else:
            print(f"  {text[:200]}")
    except Exception as e:
        print(f"\n[ERROR] {svc}/{op}: {e}")
