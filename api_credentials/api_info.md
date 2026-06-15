# 통합 API 정보 및 활용 가이드

이 폴더는 프로젝트 전반에서 사용될 여러 API 키와 관련 문서들을 중앙에서 관리하기 위해 만들어졌습니다. 개발 시 `.env` 파일을 참조하여 사용하세요.

## 1. 공공데이터포털 (요양원/요양병원 정보)
- **용도:** 전국 요양원, 요양병원, 보건소 등의 기본 정보 및 상세 시설 정보 조회
- **관련 엔드포인트:** 
  - 장기요양기관: `https://apis.data.go.kr/B550928/getLtcInsttDetailInfoService02`
  - 병원정보서비스: `https://apis.data.go.kr/B551182/hospInfoServicev2`
- **인증키 환경변수:** `PUBLIC_DATA_API_KEY_DECODED` (Python의 `requests` 사용 시 decoded 키 사용 권장)

## 2. Cesium Ion (3D 지도 시각화)
- **용도:** 웹 브라우저 기반의 3D 지구본 및 지도 시각화 엔진. 요양원 위치를 3D 지형 위에 표현할 때 사용.
- **인증키 환경변수:** `CESIUM_ION_TOKEN`
- **사용 예시 (JavaScript):**
  ```javascript
  Cesium.Ion.defaultAccessToken = process.env.CESIUM_ION_TOKEN;
  const viewer = new Cesium.Viewer('cesiumContainer');
  ```

## 3. V-World (오픈플랫폼 공간정보)
- **용도:** 대한민국의 고해상도 위성 지도 타일맵 제공, 표고(Elevation) 및 경사도 등 지형 공간 분석 API 제공.
- **인증키 환경변수:** `VWORLD_API_KEY`
- **사용 예시 (타일맵 호출):**
  `https://api.vworld.kr/req/wmts/1.0.0/${VWORLD_API_KEY}/Satellite/{z}/{y}/{x}.jpeg`

## 4. 추후 연동 가능 API
- **Open Elevation API:** `https://api.open-elevation.com/api/v1/lookup?locations={lat},{lon}` (V-World 장애 시 대체 무료 API)
- **기상청 API:** 실시간 날씨/기상 특보 (향후 추가 필요 시 발급 요망)
