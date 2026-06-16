import sqlite3
import pandas as pd

def clean_sido(sido_text):
    if pd.isna(sido_text): return "미상"
    sido_text = str(sido_text).strip()
    mapping = {
        '서울특별시': '서울', '부산광역시': '부산', '대구광역시': '대구', '인천광역시': '인천',
        '광주광역시': '광주', '대전광역시': '대전', '울산광역시': '울산', '세종특별자치시': '세종',
        '경기도': '경기', '강원도': '강원', '강원특별자치도': '강원',
        '충청북도': '충북', '충청남도': '충남', '전라북도': '전북', '전북특별자치도': '전북',
        '전라남도': '전남', '경상북도': '경북', '경상남도': '경남', '제주특별자치도': '제주'
    }
    for full, short in mapping.items():
        if sido_text.startswith(full) or sido_text.startswith(short):
            return short
    return sido_text.split()[0] if sido_text else "미상"

def main():
    conn = sqlite3.connect(r'data\nursing_facilities_nationwide.db')
    
    # 병원 데이터
    hosp_df = pd.read_sql_query('''
        SELECT sido, sigungu FROM nationwide_facilities WHERE facility_type='요양병원'
    ''', conn)
    hosp_df['sido'] = hosp_df['sido'].apply(clean_sido)
    hosp_counts = hosp_df.groupby(['sido', 'sigungu']).size().reset_index(name='hospital_count')
    
    # 요양원 데이터
    homes_df = pd.read_sql_query('''
        SELECT f.sido as f_sido, f.sigungu, b.platPlc 
        FROM nationwide_facilities f 
        LEFT JOIN nationwide_buildings b ON f.id = b.facility_id
        WHERE f.facility_type='요양원'
    ''', conn)
    
    # 요양원은 platPlc에서 sido를 추출
    homes_df['sido'] = homes_df['platPlc'].apply(lambda x: clean_sido(x.split()[0]) if pd.notna(x) and len(x.split()) > 0 else '미상')
    homes_counts = homes_df.groupby(['sido', 'sigungu']).size().reset_index(name='home_count')
    
    # 병합
    merged = pd.merge(hosp_counts, homes_counts, on=['sido', 'sigungu'], how='outer').fillna(0)
    merged['hospital_count'] = merged['hospital_count'].astype(int)
    merged['home_count'] = merged['home_count'].astype(int)
    merged['total_count'] = merged['hospital_count'] + merged['home_count']
    
    merged = merged.sort_values(by=['sido', 'total_count'], ascending=[True, False])
    
    # 결과 저장
    merged.to_csv(r'docs\regional_distribution.csv', index=False, encoding='utf-8-sig')
    
    with open(r'docs\regional_distribution_summary.txt', 'w', encoding='utf-8') as f:
        f.write("=== 시·군·구별 요양병원 및 요양원 분포 TOP 20 ===\n\n")
        top20 = merged.sort_values(by='total_count', ascending=False).head(20)
        f.write(top20.to_string(index=False))
        
        f.write("\n\n=== 광역 시·도별 종합 분포 ===\n\n")
        sido_agg = merged.groupby('sido').sum().sort_values(by='total_count', ascending=False)
        f.write(sido_agg.to_string())

if __name__ == "__main__":
    main()
