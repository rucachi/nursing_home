import os
import requests
import urllib.parse
from dotenv import load_dotenv

# .env 파일에서 API 키 로드
load_dotenv()
API_KEY = os.getenv('PUBLIC_DATA_API_KEY_DECODED')

def test_long_term_care_api():
    print("--- 국민건강보험공단 장기요양기관 시설별 상세조회 서비스 테스트 ---")
    url = 'https://apis.data.go.kr/B550928/getLtcInsttDetailInfoService02/getLtcInsttDetailInfo02'
    
    # 예시 파라미터 (실제 가이드에 따라 수정 필요)
    params = {
        'serviceKey': API_KEY,
        'pageNo': '1',
        'numOfRows': '10',
    }
    
    try:
        response = requests.get(url, params=params)
        print(f"Status Code: {response.status_code}")
        # 응답 내용의 앞부분만 출력
        print(response.text[:500])
    except Exception as e:
        print(f"Error: {e}")
    print("\n")

def test_hospital_info_api():
    print("--- 건강보험심사평가원 병원정보서비스 테스트 ---")
    url = 'https://apis.data.go.kr/B551182/hospInfoServicev2/getHospBasisList'
    
    # 예시 파라미터 (실제 가이드에 따라 수정 필요)
    params = {
        'serviceKey': API_KEY,
        'pageNo': '1',
        'numOfRows': '10',
    }
    
    try:
        response = requests.get(url, params=params)
        print(f"Status Code: {response.status_code}")
        # 응답 내용의 앞부분만 출력
        print(response.text[:500])
    except Exception as e:
        print(f"Error: {e}")
    print("\n")

if __name__ == "__main__":
    if not API_KEY:
        print("API 키를 .env 파일에서 찾을 수 없습니다.")
    else:
        test_long_term_care_api()
        test_hospital_info_api()
