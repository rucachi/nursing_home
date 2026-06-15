// 지도 초기화 (서울 중심)
const map = L.map('map', {
    zoomControl: false
}).setView([37.5665, 126.9780], 12);

// 줌 컨트롤 우측 하단으로 이동
L.control.zoom({
    position: 'bottomright'
}).addTo(map);

// V-World 배경지도 (다크모드 느낌을 위해 위성지도에 CSS 필터 적용)
L.tileLayer('https://xdworld.vworld.kr/2d/Base/service/{z}/{x}/{y}.png', {
    maxZoom: 19,
    attribution: '&copy; V-World'
}).addTo(map);

let currentReportData = null;

// UI 엘리먼트
const sidePanel = document.getElementById('side-panel');
const closeBtn = document.getElementById('close-btn');
const reportContent = document.getElementById('report-content');
const panelFooter = document.getElementById('panel-footer');
const downloadBtn = document.getElementById('download-btn');

// 패널 닫기 이벤트
closeBtn.addEventListener('click', () => {
    sidePanel.classList.remove('open');
});

// 마커 아이콘 생성 함수
function createMarkerIcon(color) {
    return L.divIcon({
        className: 'custom-marker',
        html: `<div style="width:100%; height:100%; border-radius:50%; background-color:${color};"></div>`,
        iconSize: [24, 24],
        iconAnchor: [12, 12]
    });
}

// GeoJSON 데이터 로드
fetch('facilities.geojson')
    .then(response => response.json())
    .then(data => {
        L.geoJSON(data, {
            pointToLayer: function (feature, latlng) {
                const color = feature.properties.color;
                const marker = L.marker(latlng, { icon: createMarkerIcon(color) });
                
                marker.on('click', () => {
                    renderReport(feature.properties);
                });
                
                return marker;
            }
        }).addTo(map);
    })
    .catch(error => {
        console.error('Error loading geojson:', error);
        reportContent.innerHTML = `<div class="empty-state">데이터를 불러오는 중 오류가 발생했습니다.<br>python -m http.server 로 실행했는지 확인하세요.</div>`;
    });

// 마크다운 형식의 텍스트를 파싱
function parseMarkdown(text) {
    return text.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
}

// 보고서 렌더링
function renderReport(props) {
    const contentDiv = document.getElementById('report-content');
    const footerDiv = document.getElementById('panel-footer');
    
    const bgColor = props.color || '#3b82f6';
    
    let factorsHtml = '';
    if (props.factors) {
        for (const [key, value] of Object.entries(props.factors)) {
            factorsHtml += `
                <tr>
                    <td class="fact-key">${key}</td>
                    <td class="fact-value">${value}</td>
                </tr>
            `;
        }
    }

    const html = `
        <div class="report-title">${props.name}</div>
        <div class="report-subtitle">${props.address}</div>
        
        <div class="report-section">
            <h3 style="border-bottom: 2px solid ${bgColor}; padding-bottom: 8px; margin-bottom: 16px;">시설 스펙 및 소방 환경 분석표</h3>
            <table class="fact-table">
                <tbody>
                    ${factorsHtml}
                </tbody>
            </table>
        </div>
    `;

    contentDiv.innerHTML = html;
    footerDiv.style.display = 'block';
    sidePanel.classList.add('open');
    
    currentReportData = props;
}

// HTML 파일 다운로드 생성기
downloadBtn.addEventListener('click', () => {
    if (!currentReportData) return;
    
    const props = currentReportData;
    const bgColor = props.color || '#3b82f6';
    let factorsHtml = '';
    if (props.factors) {
        for (const [key, value] of Object.entries(props.factors)) {
            factorsHtml += `
                <tr>
                    <td class="fact-key" style="padding: 12px 15px; border: 1px solid #e2e8f0; background-color: #f8fafc; font-weight: 600; width: 30%;">${key}</td>
                    <td class="fact-value" style="padding: 12px 15px; border: 1px solid #e2e8f0;">${value}</td>
                </tr>
            `;
        }
    }
    
    downloadHtmlReport(props, bgColor, factorsHtml);
});

function downloadHtmlReport(props, bgColor, factorsHtml) {
    const htmlContent = `
<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <title>${props.name} - 시설 스펙 및 소방 환경 분석표</title>
    <style>
        body { font-family: 'Malgun Gothic', sans-serif; line-height: 1.6; color: #333; max-width: 800px; margin: 40px auto; padding: 20px; }
        h1 { border-bottom: 2px solid ${bgColor}; padding-bottom: 10px; margin-bottom: 30px; }
        .info-p { font-size: 1.1rem; margin-bottom: 5px; }
        .fact-table { width: 100%; border-collapse: collapse; margin-top: 20px; box-shadow: 0 1px 3px rgba(0,0,0,0.1); }
        .fact-table th, .fact-table td { padding: 12px 15px; border: 1px solid #e2e8f0; text-align: left; }
        .fact-table th { background-color: #f8fafc; font-weight: 600; width: 30%; }
        .fact-table tr:nth-child(even) { background-color: #fcfcfc; }
    </style>
</head>
<body>
    <h1>🏥 ${props.name} 소방 환경 분석표</h1>
    <p class="info-p"><strong>주소:</strong> ${props.address}</p>
    
    <table class="fact-table">
        <tbody>
            ${factorsHtml}
        </tbody>
    </table>
</body>
</html>`;

    const blob = new Blob([htmlContent], { type: 'text/html;charset=utf-8' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `VAM_Report_${props.name.replace(/\s/g, '_')}.html`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
}
