import os, requests, xml.etree.ElementTree as ET
from dotenv import load_dotenv
load_dotenv()
API_KEY = os.getenv('PUBLIC_DATA_API_KEY_DECODED')

# 건강보험심사평가원 병원정보서비스v2 - 다른 오퍼레이션 탐색
base = 'https://apis.data.go.kr/B551182/hospInfoServicev2'
operations = [
    'getHospBasisList',      # 기본 목록 (이미 확인)
    'getHospBasisInfov2',    # 기본 정보 v2
    'getHospDetailList',     # 상세 목록?
    'getHospDetailInfo',     # 상세 정보?
    'getHospRcmdList',       # 추천 목록?
]

for op in operations:
    url = f'{base}/{op}'
    params = {'serviceKey': API_KEY, 'pageNo': '1', 'numOfRows': '1', 'clCd': '28'}
    try:
        resp = requests.get(url, params=params, timeout=10)
        print(f"\n[{resp.status_code}] {op}")
        if resp.status_code == 200 and '<?xml' in resp.text[:50]:
            root = ET.fromstring(resp.content)
            code = root.findtext('.//resultCode')
            msg = root.findtext('.//resultMsg')
            total = root.findtext('.//totalCount')
            print(f"  code={code}, msg={msg}, total={total}")
            for item in root.findall('.//item')[:1]:
                for child in item:
                    print(f"    {child.tag}: {child.text}")
        else:
            print(f"  {resp.text[:200]}")
    except Exception as e:
        print(f"  ERROR: {e}")

# 장기요양기관 API - 필수 파라미터 추가 시도
print("\n" + "=" * 60)
print("장기요양기관 API - 파라미터 조합 시도")
print("=" * 60)

base2 = 'https://apis.data.go.kr/B550928'
tests = [
    ('getLtcInsttDetailInfoService/getLtcInsttDetailInfo', {'siDoCd': '11', 'siGunGuCd': '110016'}),
    ('getLtcInsttDetailInfoService/getLtcInsttDetailInfo', {'ltcInsttAddr': '서울'}),
    ('getLtcInsttDetailInfoService/getLtcInsttDetailInfo', {'adminPttnCd': '1'}),
    ('searchLtcInsttService/searchLtcInsttList', {'siDoCd': '11'}),
    ('searchLtcInsttService/searchLtcInsttList', {'lcnsNo': ''}),
]

for path, extra_params in tests:
    url = f'{base2}/{path}'
    params = {'serviceKey': API_KEY, 'pageNo': '1', 'numOfRows': '2'}
    params.update(extra_params)
    try:
        resp = requests.get(url, params=params, timeout=10)
        param_str = ', '.join(f'{k}={v}' for k, v in extra_params.items())
        print(f"\n[{resp.status_code}] {path.split('/')[-1]} ({param_str})")
        if resp.status_code == 200 and '<?xml' in resp.text[:50]:
            root = ET.fromstring(resp.content)
            code = root.findtext('.//resultCode')
            msg = root.findtext('.//resultMsg')
            total = root.findtext('.//totalCount')
            print(f"  code={code}, msg={msg}, total={total}")
            for item in root.findall('.//item')[:1]:
                for child in item:
                    print(f"    {child.tag}: {child.text}")
        else:
            print(f"  {resp.text[:200]}")
    except Exception as e:
        print(f"  ERROR: {e}")
