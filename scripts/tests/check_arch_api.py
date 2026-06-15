import os, requests, xml.etree.ElementTree as ET, json
from dotenv import load_dotenv
load_dotenv()
API_KEY = os.getenv('PUBLIC_DATA_API_KEY_DECODED')

base = 'https://apis.data.go.kr/1613000/ArchPmsHubService'

# 건축인허가정보 서비스 - 가능한 오퍼레이션 탐색
operations = [
    # 건축물대장 관련 일반적 오퍼레이션명
    'getApBasisOulnInfo',       # 건축허가 기본개요
    'getApFlrOulnInfo',         # 건축허가 층별개요
    'getApUsInfo',              # 건축허가 용도별
    'getApExpoInfo',            # 건축허가 호별
    'getHsBasisOulnInfo',       # 주택인허가 기본개요
    'getBrBasisOulnInfo',       # 건축물대장 기본개요
    'getBrFlrOulnInfo',         # 건축물대장 층별
    'getBrExpoInfo',            # 건축물대장 호별
    'getBrTitleInfo',           # 건축물대장 표제부
    'getBrRecapTitleInfo',      # 건축물대장 총괄표제부
    # ArchPmsHubService 전용 오퍼레이션 추정
    'getArchPmsHubList',
    'getArchPmsList',
    'getArchPmsInfo',
    'getArchPmsDetail',
    'getPmsAplyInfo',
    'getBldRgstInfo',
    'getApBldRgstInfo',
]

print("=" * 60)
print("건축HUB 건축인허가정보 서비스 - 오퍼레이션 탐색")
print(f"Base: {base}")
print("=" * 60)

for op in operations:
    url = f'{base}/{op}'
    # 서울 종로구 시범 조회
    params = {
        'serviceKey': API_KEY,
        'pageNo': '1',
        'numOfRows': '2',
        'sigunguCd': '11680',
        'bjdongCd': '10300',
    }
    try:
        resp = requests.get(url, params=params, timeout=10)
        status = resp.status_code
        
        if status == 200:
            # JSON인지 XML인지 확인
            text = resp.text.strip()
            if text.startswith('{'):
                data = json.loads(text)
                print(f"\n[{status}] {op} (JSON)")
                print(f"  {json.dumps(data, ensure_ascii=False, indent=2)[:500]}")
            elif text.startswith('<'):
                try:
                    root = ET.fromstring(resp.content)
                    code = root.findtext('.//resultCode') or root.findtext('.//{http://www.w3.org/2003/05/soap-envelope}resultCode')
                    msg = root.findtext('.//resultMsg') or ''
                    total = root.findtext('.//totalCount') or '0'
                    print(f"\n[{status}] {op} (XML) code={code}, msg={msg}, total={total}")
                    
                    for item in root.findall('.//{*}item')[:1]:
                        print("  [필드 목록]")
                        for child in item:
                            tag = child.tag.split('}')[-1] if '}' in child.tag else child.tag
                            print(f"    {tag}: {child.text}")
                except Exception as e2:
                    print(f"\n[{status}] {op}: XML parse error - {e2}")
                    print(f"  {text[:200]}")
            else:
                print(f"\n[{status}] {op}: {text[:200]}")
        else:
            preview = resp.text[:100].strip()
            print(f"\n[{status}] {op}: {preview}")
    except Exception as e:
        print(f"\n[ERR] {op}: {e}")
