import json
import csv
import os

def get_risk_info(score_str):
    try:
        score = float(score_str)
    except (ValueError, TypeError):
        score = 0
    
    if score >= 80:
        return "#10b981", "안전 (Safe)"
    elif score >= 60:
        return "#f59e0b", "보통 (Moderate)"
    else:
        return "#ef4444", "위험 (High Risk)"

def format_year(date_str):
    if not date_str or date_str.strip() == "":
        return "정보 없음"
    # Usually YYYYMMDD
    if len(date_str) >= 4:
        return f"{date_str[:4]}년"
    return "정보 없음"

def generate_geojson():
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    nursing_home_csv = os.path.join(base_dir, 'data', '요양원_전국데이터.csv')
    hospital_csv = os.path.join(base_dir, 'data', '요양병원_전국데이터.csv')
    output_geojson = os.path.join(base_dir, 'dashboard', 'facilities.geojson')
    
    features = []
    
    # Process 요양원 (Nursing Homes)
    with open(nursing_home_csv, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            try:
                lat = float(row.get('lat', 0))
                lon = float(row.get('lon', 0))
            except ValueError:
                continue
                
            if lat == 0 or lon == 0:
                continue
                
            score_str = row.get('vam_score', '0')
            color, risk_level = get_risk_info(score_str)
            
            capacity = row.get('capacity', '0')
            staff = row.get('caregiver_count', '0')
            
            # format scale
            scale_group = row.get('scale_group', '정보 없음')
            tot_area = row.get('totArea', '정보 없음')
            scale_str = f"{scale_group} (연면적: {tot_area}㎡)"
            
            dist_km = row.get('fire_station_dist_km', '')
            if dist_km:
                try:
                    dist_str = f"{float(dist_km):.1f}km"
                except:
                    dist_str = dist_km + "km"
            else:
                dist_str = "정보 없음"
            
            feature = {
                "type": "Feature",
                "geometry": {
                    "type": "Point",
                    "coordinates": [lon, lat]
                },
                "properties": {
                    "name": row.get('name', ''),
                    "address": row.get('address', ''),
                    "capacity": capacity,
                    "staff": staff,
                    "score": score_str,
                    "risk_level": risk_level,
                    "color": color,
                    "factors": {
                        "준공연도": format_year(row.get('useAprDay', '')),
                        "건축구조": row.get('strctCdNm', '정보 없음') or '정보 없음',
                        "건물용도": row.get('mainPurpsCdNm', '정보 없음') or '정보 없음',
                        "건물 규모": scale_str,
                        "정원 및 종사자": f"정원 {capacity}명 / 종사자 {staff}명",
                        "인접 도로폭": row.get('road_type', '정보 없음') or '정보 없음',
                        "소방서 거리": dist_str
                    }
                }
            }
            features.append(feature)

    # Process 요양병원 (Hospitals)
    with open(hospital_csv, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            try:
                lat = float(row.get('lat', 0))
                lon = float(row.get('lon', 0))
            except ValueError:
                continue
                
            if lat == 0 or lon == 0:
                continue
                
            score_str = row.get('vam_score', '0')
            color, risk_level = get_risk_info(score_str)
            
            doctor_count = row.get('doctor_count', '0')
            
            # format scale
            scale_group = row.get('scale_group', '정보 없음')
            tot_area = row.get('totArea', '정보 없음')
            scale_str = f"{scale_group} (연면적: {tot_area}㎡)"
            
            dist_km = row.get('fire_station_dist_km', '')
            if dist_km:
                try:
                    dist_str = f"{float(dist_km):.1f}km"
                except:
                    dist_str = dist_km + "km"
            else:
                dist_str = "정보 없음"
                
            feature = {
                "type": "Feature",
                "geometry": {
                    "type": "Point",
                    "coordinates": [lon, lat]
                },
                "properties": {
                    "name": row.get('name', ''),
                    "address": row.get('address', ''),
                    "score": score_str,
                    "risk_level": risk_level,
                    "color": color,
                    "factors": {
                        "준공연도": format_year(row.get('useAprDay', '')),
                        "건축구조": row.get('strctCdNm', '정보 없음') or '정보 없음',
                        "건물용도": row.get('mainPurpsCdNm', '정보 없음') or '정보 없음',
                        "건물 규모": scale_str,
                        "의료 인력": f"의사수 {doctor_count}명",
                        "인접 도로폭": row.get('road_type', '정보 없음') or '정보 없음',
                        "소방서 거리": dist_str
                    }
                }
            }
            features.append(feature)

    geojson_collection = {
        "type": "FeatureCollection",
        "features": features
    }

    with open(output_geojson, 'w', encoding='utf-8') as f:
        json.dump(geojson_collection, f, ensure_ascii=False, indent=2)

    print(f"Successfully generated geojson with {len(features)} features at {output_geojson}")

if __name__ == "__main__":
    generate_geojson()
