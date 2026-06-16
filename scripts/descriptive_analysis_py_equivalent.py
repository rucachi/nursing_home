import pandas as pd

def analyze_df(df, name):
    print(f"\n{'='*50}\n[{name} 빈도분석 및 기술통계]\n{'='*50}")
    
    cat_vars = ['sido', 'scale_group', 'distance_group', 'age_group', 'road_type', 'strctCdNm']
    for var in cat_vars:
        if var in df.columns:
            print(f"\n--- {var} 빈도 및 비율 ---")
            counts = df[var].value_counts(dropna=False)
            props = df[var].value_counts(normalize=True, dropna=False) * 100
            df_freq = pd.DataFrame({'Count': counts, 'Percentage(%)': props}).round(2)
            print(df_freq)

    print("\n--- 연속형 변수 기술통계 ---")
    cont_vars = ['capacity', 'caregiver_count', 'doctor_count', 'totArea', 'fire_station_dist_km', 'vam_score']
    existing_cont = [v for v in cont_vars if v in df.columns]
    
    if existing_cont:
        desc = df[existing_cont].describe().round(2)
        print(desc)

def main():
    homes = pd.read_csv(r'data\요양원_전국데이터.csv', encoding='utf-8')
    hospitals = pd.read_csv(r'data\요양병원_전국데이터.csv', encoding='utf-8')
    
    with open('docs/descriptive_stats_output.txt', 'w', encoding='utf-8') as f:
        import sys
        sys.stdout = f
        analyze_df(homes, "요양원 (Nursing Homes)")
        analyze_df(hospitals, "요양병원 (Nursing Hospitals)")

if __name__ == "__main__":
    main()
