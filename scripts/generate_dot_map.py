import pandas as pd
import folium
import json
import os

def classify_region(sigungu):
    if pd.isna(sigungu): return '미상'
    sigungu = str(sigungu).strip()
    return '농촌 (Rural)' if sigungu.endswith('군') else '도시 (Urban)'

def main():
    print("Loading data...")
    homes = pd.read_csv(r'data\요양원_전국데이터.csv', encoding='utf-8')
    hospitals = pd.read_csv(r'data\요양병원_전국데이터.csv', encoding='utf-8')
    
    df = pd.concat([homes, hospitals], ignore_index=True)
    df = df.dropna(subset=['lat', 'lon'])
    df['region_type'] = df['sigungu'].apply(classify_region)
    
    with open(r'data\fire_stations.json', 'r', encoding='utf-8') as f:
        fire_stations = json.load(f)
        
    print("Generating Folium Dot Map...")
    m = folium.Map(location=[36.5, 127.5], zoom_start=7, tiles='CartoDB positron')
    
    # 1. 일반 요양시설 점(Dot)으로 표시
    # 성능을 위해 팝업 없이 단순 점으로 그림
    for _, row in df.iterrows():
        is_rural = (row['region_type'] == '농촌 (Rural)')
        is_far = (row['fire_station_dist_km'] > 3.0)
        
        if is_rural and is_far:
            # 고위험 (빨간색 큰 점, 팝업 있음)
            folium.CircleMarker(
                location=[row['lat'], row['lon']],
                radius=4,
                color='red',
                fill=True,
                fill_color='red',
                fill_opacity=0.9,
                popup=f"[{row['facility_type']}] {row['name']}<br>소방서거리: {row['fire_station_dist_km']:.1f}km",
                tooltip="초고위험 농촌 시설 (골든타임 취약)"
            ).add_to(m)
        else:
            # 일반 시설 (회색/주황색 작은 점, 팝업 없음)
            color = 'orange' if is_rural else 'gray'
            folium.CircleMarker(
                location=[row['lat'], row['lon']],
                radius=1.5,
                color=color,
                weight=1,
                fill=True,
                fill_color=color,
                fill_opacity=0.6
            ).add_to(m)
            
    # 2. 소방서 표시 (파란색 아이콘)
    for fs in fire_stations:
        folium.Marker(
            location=[fs['lat'], fs['lon']],
            icon=folium.Icon(color='blue', icon='fire', prefix='fa'),
            tooltip=f"{fs['title']}"
        ).add_to(m)
        
    m.save(r'docs\plots\heatmap.html') # 덮어쓰기
    print("Dot map with fire stations generated successfully.")

if __name__ == "__main__":
    main()
