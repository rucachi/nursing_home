# 요양시설 기본 빈도분석 및 기술통계 R 스크립트

# 필요 패키지 설치 및 로드 (필요시 주석 해제)
# install.packages(c("dplyr", "psych", "tableone"))
library(dplyr)
library(psych)
library(tableone)

# 1. 데이터 불러오기 (인코딩 UTF-8 지정)
homes <- read.csv("data/요양원_전국데이터.csv", fileEncoding = "UTF-8", stringsAsFactors = FALSE)
hospitals <- read.csv("data/요양병원_전국데이터.csv", fileEncoding = "UTF-8", stringsAsFactors = FALSE)

# 데이터 구분을 위해 라벨 추가 (이미 facility_type이 있지만 명확히 하기 위해)
homes$dataset_type <- "요양원"
hospitals$dataset_type <- "요양병원"

# 2. 기초 변수 처리 및 팩터화
# 분석할 주요 범주형 변수
cat_vars <- c("sido", "scale_group", "distance_group", "age_group", "road_type", "strctCdNm")
# 분석할 주요 연속형 변수
cont_vars_homes <- c("capacity", "caregiver_count", "totArea", "fire_station_dist_km", "vam_score")
cont_vars_hosp <- c("doctor_count", "totArea", "fire_station_dist_km", "vam_score")

print("==================================================")
print("              요양원 (Nursing Homes) 분석 결과")
print("==================================================")

# 3. 요양원 빈도분석 (Frequency Analysis)
cat("\n[요양원 - 범주형 변수 빈도 분석]\n")
for (var in cat_vars) {
  if (var %in% colnames(homes)) {
    cat("\n---", var, "---\n")
    print(table(homes[[var]], useNA = "ifany"))
    print(prop.table(table(homes[[var]], useNA = "ifany")) * 100) # 백분율
  }
}

# 4. 요양원 기술통계 (Descriptive Statistics)
cat("\n[요양원 - 연속형 변수 기술통계]\n")
describe_homes <- describe(homes[, cont_vars_homes])
print(describe_homes)


print("==================================================")
print("            요양병원 (Nursing Hospitals) 분석 결과")
print("==================================================")

# 5. 요양병원 빈도분석 (Frequency Analysis)
cat("\n[요양병원 - 범주형 변수 빈도 분석]\n")
for (var in cat_vars) {
  if (var %in% colnames(hospitals)) {
    cat("\n---", var, "---\n")
    print(table(hospitals[[var]], useNA = "ifany"))
    print(prop.table(table(hospitals[[var]], useNA = "ifany")) * 100) # 백분율
  }
}

# 6. 요양병원 기술통계 (Descriptive Statistics)
cat("\n[요양병원 - 연속형 변수 기술통계]\n")
describe_hosp <- describe(hospitals[, cont_vars_hosp])
print(describe_hosp)

# 7. TableOne 패키지를 활용한 요약 표 생성 (선택 사항)
# 요양원과 요양병원을 합쳐서 비교하는 테이블을 원할 경우
# combined_data <- bind_rows(homes, hospitals)
# table1 <- CreateTableOne(vars = c("totArea", "fire_station_dist_km", "vam_score", "scale_group"), 
#                          strata = "dataset_type", data = combined_data)
# cat("\n[시설 유형별 비교 요약 테이블]\n")
# print(table1, showAllLevels = TRUE)

print("분석 스크립트 실행이 완료되었습니다.")
