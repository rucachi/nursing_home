import pdfplumber
import sqlite3
import re
import os

pdf_path = r'd:\anti_gravity\nursing home\data\2025+노인복지시설+현황.pdf'
db_path = r'd:\anti_gravity\nursing home\data\nursing_facilities.db'

conn = sqlite3.connect(db_path)
cursor = conn.cursor()
cursor.execute('DELETE FROM facilities')
conn.commit()

start_page = 127 # 표 데이터 시작
end_page = 135   # 서울 지역 일부

def clean_text(text):
    if text is None:
        return ""
    return str(text).replace('\n', ' ').strip()

def parse_phone_fax(text):
    text = clean_text(text)
    phones = re.findall(r'[\d\-]{9,15}', text.replace(' ', ''))
    phone = phones[0] if len(phones) > 0 else ""
    fax = phones[1] if len(phones) > 1 else ""
    return phone, fax

facility_type = "노인요양시설"
sido = "서울특별시"

print("Extracting...")
with pdfplumber.open(pdf_path) as pdf:
    for i in range(start_page, end_page + 1):
        page = pdf.pages[i]
        tables = page.extract_tables()
        if not tables:
            continue
            
        for table in tables:
            for row in table:
                if not row or len(row) < 14:
                    continue
                if row[0] and "일련" in str(row[0]):
                    continue
                if row[1] and "시･군･구" in str(row[1]):
                    continue
                
                try:
                    sigungu = clean_text(row[1])
                    if not sigungu or "계" in sigungu or "소" in sigungu:
                        continue
                        
                    name = clean_text(row[2])
                    director = clean_text(row[3])
                    
                    try:
                        capacity = int(clean_text(row[4]).replace(',', ''))
                    except:
                        capacity = 0
                        
                    try:
                        current_male = int(clean_text(row[6]).replace(',', ''))
                    except:
                        current_male = 0
                        
                    try:
                        current_female = int(clean_text(row[7]).replace(',', ''))
                    except:
                        current_female = 0
                        
                    try:
                        staff_count = int(clean_text(row[8]).replace(',', ''))
                    except:
                        staff_count = 0
                        
                    address = clean_text(row[11])
                    phone, fax = parse_phone_fax(row[12])
                    est_date = clean_text(row[13])
                    operator_type = clean_text(row[14]) if len(row) > 14 else ""
                    
                    if name and address and not address.isdigit():
                        cursor.execute('''
                        INSERT INTO facilities (
                            facility_type, sido, sigungu, name, director, capacity, 
                            current_male, current_female, staff_count, address, 
                            phone, fax, est_date, operator_type
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        ''', (facility_type, sido, sigungu, name, director, capacity, current_male, current_female, staff_count, address, phone, fax, est_date, operator_type))
                except Exception as e:
                    pass

conn.commit()

cursor.execute('SELECT COUNT(*) FROM facilities')
count = cursor.fetchone()[0]
print(f"Total extracted: {count} rows")

cursor.execute('SELECT sigungu, name, capacity, address FROM facilities LIMIT 5')
for row in cursor.fetchall():
    print(row)

conn.close()
print("Done.")
