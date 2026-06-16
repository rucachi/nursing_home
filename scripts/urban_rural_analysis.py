import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from scipy import stats
import folium
from folium.plugins import HeatMap
import os

# 한글 폰트 설정
plt.rcParams['font.family'] = 'Malgun Gothic'
plt.rcParams['axes.unicode_minus'] = False

def classify_region(sigungu):
    if pd.isna(sigungu): return '미상'
    sigungu = str(sigungu).strip()
    if sigungu.endswith('군'):
        return '농촌 (Rural)'
    else:
        return '도시 (Urban)'

def main():
    print("Loading data from CSVs...")
    homes = pd.read_csv(r'data\요양원_전국데이터.csv', encoding='utf-8')
    hospitals = pd.read_csv(r'data\요양병원_전국데이터.csv', encoding='utf-8')
    
    # 두 데이터프레임 병합
    df = pd.concat([homes, hospitals], ignore_index=True)
    df = df.dropna(subset=['lat', 'lon'])
    
    # 지역 분류 (군 vs 시/구)
    df['region_type'] = df['sigungu'].apply(classify_region)
    
    urban_df = df[df['region_type'] == '도시 (Urban)']
    rural_df = df[df['region_type'] == '농촌 (Rural)']
    
    print(f"Urban facilities: {len(urban_df)}, Rural facilities: {len(rural_df)}")
    
    os.makedirs(r'docs\plots', exist_ok=True)
    
    with open(r'docs\urban_rural_analysis_results.txt', 'w', encoding='utf-8') as f:
        f.write("=== 도시 vs 농촌 요양시설 취약성 통계 검증 ===\n\n")
        
        # ---------------------------------------------------------
        # 1. 소방서 거리 (골든타임) T-Test 분석
        # ---------------------------------------------------------
        u_dist = urban_df['fire_station_dist_km'].dropna()
        r_dist = rural_df['fire_station_dist_km'].dropna()
        
        t_stat, p_val = stats.ttest_ind(u_dist, r_dist, equal_var=False)
        
        f.write("[1. 소방서까지의 평균 거리 비교]\n")
        f.write(f"- 도시(Urban) 평균: {u_dist.mean():.2f} km\n")
        f.write(f"- 농촌(Rural) 평균: {r_dist.mean():.2f} km\n")
        f.write(f"- T-statistic: {t_stat:.2f}, p-value: {p_val:.5f}\n")
        if p_val < 0.05:
            f.write("-> 결론: 농촌 지역 시설이 도시 지역보다 소방서에서 유의미하게 더 멉니다.\n\n")
        
        # 시각화: 거리 비교 바 차트
        plt.figure(figsize=(8, 6))
        sns.barplot(x='region_type', y='fire_station_dist_km', data=df, errorbar='ci', capsize=0.1, palette='pastel', hue='region_type', legend=False)
        plt.title('도시 vs 농촌 소방서 평균 거리 비교\n(골든타임 확보 취약성 증명)', fontsize=16, fontweight='bold')
        plt.ylabel('평균 소방서 거리 (km)', fontsize=12)
        plt.xlabel('지역 구분', fontsize=12)
        plt.tight_layout()
        plt.savefig(r'docs\plots\05_urban_rural_distance.png', dpi=300)
        plt.close()

        # ---------------------------------------------------------
        # 2. VAM Score (종합화재취약성) T-Test 분석
        # ---------------------------------------------------------
        u_vam = urban_df['vam_score'].dropna()
        r_vam = rural_df['vam_score'].dropna()
        
        t_stat_v, p_val_v = stats.ttest_ind(u_vam, r_vam, equal_var=False)
        f.write("[2. 평균 VAM(화재취약성) 점수 비교]\n")
        f.write(f"- 도시(Urban) VAM 평균: {u_vam.mean():.2f} 점\n")
        f.write(f"- 농촌(Rural) VAM 평균: {r_vam.mean():.2f} 점\n")
        f.write(f"- T-statistic: {t_stat_v:.2f}, p-value: {p_val_v:.5f}\n")
        if p_val_v < 0.05:
            f.write("-> 결론: 농촌 지역 시설의 화재 취약성 점수가 도시보다 유의미하게 낮아(위험해) 구조적 개선이 시급합니다.\n\n")
        
        # 시각화: VAM 비교 바 차트
        plt.figure(figsize=(8, 6))
        sns.barplot(x='region_type', y='vam_score', data=df, errorbar='ci', capsize=0.1, palette='muted', hue='region_type', legend=False)
        plt.title('도시 vs 농촌 평균 VAM(화재취약성) 점수 비교\n(농어촌 맞춤형 표준모델 당위성)', fontsize=16, fontweight='bold')
        plt.ylabel('평균 VAM Score (100점 만점)', fontsize=12)
        plt.xlabel('지역 구분', fontsize=12)
        plt.ylim(60, 100)
        plt.tight_layout()
        plt.savefig(r'docs\plots\06_urban_rural_vam.png', dpi=300)
        plt.close()
        
    # ---------------------------------------------------------
    # 3. 전국 요양시설 밀집도 및 취약성 지도 (Folium Heatmap)
    # ---------------------------------------------------------
    print("Generating Folium Heatmap...")
    m = folium.Map(location=[36.5, 127.5], zoom_start=7, tiles='CartoDB positron')
    
    # 히트맵 레이어 (모든 시설)
    heat_data = [[row['lat'], row['lon']] for index, row in df.iterrows()]
    HeatMap(heat_data, radius=13, blur=10, max_zoom=1).add_to(m)
    
    # 취약 마커 레이어: 농촌 + 소방서거리 > 3km
    vulnerable_rural = rural_df[rural_df['fire_station_dist_km'] > 3.0]
    for index, row in vulnerable_rural.iterrows():
        folium.CircleMarker(
            location=[row['lat'], row['lon']],
            radius=3,
            color='red',
            fill=True,
            fill_color='red',
            fill_opacity=0.7,
            popup=f"[{row['facility_type']}] {row['name']}<br>소방서거리: {row['fire_station_dist_km']:.1f}km<br>VAM: {row['vam_score']}",
            tooltip="초고위험 농어촌 시설 (골든타임 사각지대)"
        ).add_to(m)
    
    m.save(r'docs\plots\heatmap.html')
    print("Analysis complete. Saved plots and heatmap.html to docs/plots/")

if __name__ == "__main__":
    main()
