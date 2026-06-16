import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from scipy import stats
import os

# 폰트 설정 (Windows 한글 깨짐 방지)
plt.rcParams['font.family'] = 'Malgun Gothic'
plt.rcParams['axes.unicode_minus'] = False

def main():
    print("Loading data...")
    homes_df = pd.read_csv(r'data\요양원_전국데이터.csv', encoding='utf-8')
    
    # --- 데이터 전처리 ---
    # 1. PPT 기준(50, 100)에 맞게 규모 재분류
    def get_new_scale(cap):
        if pd.isna(cap) or cap == 0: return '미상'
        if cap >= 100: return '대형 (100인 이상)'
        elif cap >= 50: return '중형 (50~99인)'
        else: return '소형 (50인 미만)'
    
    homes_df['scale_group'] = homes_df['capacity'].apply(get_new_scale)
    
    # 2. 야간 보호 인력 비율 계산 (정원 / 상주 인력)
    # 인력 1명당 책임져야 할 환자 수
    # 야간에는 주간 인력의 약 1/4 만 남는다고 가정 (교대근무 및 휴게시간 고려)
    homes_df['patients_per_staff_day'] = homes_df['capacity'] / homes_df['caregiver_count']
    homes_df['patients_per_staff_night'] = homes_df['patients_per_staff_day'] * 4 
    homes_df.replace([float('inf'), -float('inf')], pd.NA, inplace=True)
    
    # 저장 디렉토리
    os.makedirs(r'docs\plots', exist_ok=True)
    
    with open(r'docs\analysis_results.txt', 'w', encoding='utf-8') as f:
        f.write("=== 요양원 대피체계 통계 분석 결과 (행정안전부 착수보고용) ===\n\n")
        
        # ---------------------------------------------------------
        # [기] 1. 규모별 분포 (Pie Chart)
        # ---------------------------------------------------------
        scale_counts = homes_df[homes_df['scale_group'] != '미상']['scale_group'].value_counts()
        plt.figure(figsize=(8, 8))
        colors = ['#ff9999','#66b3ff','#99ff99']
        plt.pie(scale_counts, labels=scale_counts.index, autopct='%1.1f%%', startangle=140, colors=colors, textprops={'fontsize': 14})
        plt.title('전국 요양원 시설 규모 분포\n(획일적 대피 매뉴얼의 한계)', fontsize=18, fontweight='bold')
        plt.tight_layout()
        plt.savefig(r'docs\plots\01_scale_distribution.png', dpi=300)
        plt.close()
        
        f.write("[1. 규모 분포]\n")
        f.write(scale_counts.to_string() + "\n\n")
        
        # ---------------------------------------------------------
        # [승] 2. 골든타임 부재 (소방서 거리 히스토그램)
        # ---------------------------------------------------------
        dist_data = homes_df['fire_station_dist_km'].dropna()
        plt.figure(figsize=(10, 6))
        sns.histplot(dist_data, bins=30, kde=True, color='coral')
        plt.axvline(x=3.0, color='red', linestyle='--', linewidth=2, label='골든타임 취약 기준선 (3km)')
        plt.title('전국 요양원 소방서 거리 분포\n(골든타임 내 자체 대피의 필요성)', fontsize=16, fontweight='bold')
        plt.xlabel('소방서까지의 직선 거리 (km)', fontsize=12)
        plt.ylabel('시설 수', fontsize=12)
        plt.legend()
        plt.tight_layout()
        plt.savefig(r'docs\plots\02_fire_station_distance.png', dpi=300)
        plt.close()
        
        golden_time_risk = len(dist_data[dist_data > 3.0])
        golden_time_ratio = golden_time_risk / len(dist_data) * 100
        f.write(f"[2. 소방서 거리 (골든타임)]\n")
        f.write(f"3km 초과(취약) 시설 수: {golden_time_risk}곳 ({golden_time_ratio:.1f}%)\n\n")

        # ---------------------------------------------------------
        # [승] 3. 야간 조력의 한계 (인력 비율 분포)
        # ---------------------------------------------------------
        night_staff = homes_df['patients_per_staff_night'].dropna()
        plt.figure(figsize=(10, 6))
        sns.boxplot(y=night_staff, color='skyblue')
        plt.axhline(y=10, color='red', linestyle='--', label='위험선: 직원 1인당 환자 10명 이상')
        plt.title('야간 요양보호사 1인당 담당 환자 수 추정치\n(야간 조력 대피의 물리적 한계)', fontsize=16, fontweight='bold')
        plt.ylabel('1인당 담당 환자 수 (명)', fontsize=12)
        plt.ylim(0, 30) # 이상치 제외 시각화
        plt.legend()
        plt.tight_layout()
        plt.savefig(r'docs\plots\03_night_shift_vulnerability.png', dpi=300)
        plt.close()
        
        danger_night_ratio = len(night_staff[night_staff > 10]) / len(night_staff) * 100
        f.write(f"[3. 야간 인력 한계]\n")
        f.write(f"야간 1인당 10명 이상 담당 추정 시설 비율: {danger_night_ratio:.1f}%\n\n")

        # ---------------------------------------------------------
        # [전] 4. VAM 점수 ANOVA 분석 및 박스플롯
        # ---------------------------------------------------------
        vam_df = homes_df[homes_df['scale_group'] != '미상'].dropna(subset=['vam_score'])
        
        plt.figure(figsize=(10, 6))
        sns.boxplot(x='scale_group', y='vam_score', data=vam_df, order=['소형 (50인 미만)', '중형 (50~99인)', '대형 (100인 이상)'], palette='Set2')
        plt.title('규모별 화재취약성(VAM) 점수 비교\n(데이터 기반의 위험도 유형화)', fontsize=16, fontweight='bold')
        plt.xlabel('시설 규모', fontsize=12)
        plt.ylabel('VAM Score (100점 만점)', fontsize=12)
        plt.tight_layout()
        plt.savefig(r'docs\plots\04_vam_by_scale.png', dpi=300)
        plt.close()
        
        group1 = vam_df[vam_df['scale_group'] == '소형 (50인 미만)']['vam_score']
        group2 = vam_df[vam_df['scale_group'] == '중형 (50~99인)']['vam_score']
        group3 = vam_df[vam_df['scale_group'] == '대형 (100인 이상)']['vam_score']
        
        f_stat, p_val = stats.f_oneway(group1, group2, group3)
        f.write(f"[4. ANOVA 분산 분석 결과]\n")
        f.write(f"규모별 VAM 점수 F-statistic: {f_stat:.2f}, p-value: {p_val:.5f}\n")
        if p_val < 0.05:
            f.write("-> 결론: 시설 규모에 따라 화재취약성 점수는 통계적으로 유의미한 차이가 존재함.\n")
        
        # 교차분석: 소방서 원거리(>3km) 시설 중 노후건물(2000년 이전) 비율
        old_buildings = homes_df[homes_df['age_group'] == '노후 (2000년 이전)']
        far_buildings = homes_df[homes_df['fire_station_dist_km'] > 3.0]
        f.write("\n[5. 교차 취약성]\n")
        f.write(f"골든타임 취약 시설({len(far_buildings)}곳) 중 노후 건축물 비율 등 복합 취약성 분석 가능.\n")

    print("Analysis complete. Plots saved to docs/plots/")

if __name__ == "__main__":
    main()
