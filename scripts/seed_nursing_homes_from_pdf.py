import pdfplumber
import sqlite3
import re
import os
import argparse
import time

DB_PATH = r'd:\anti_gravity\nursing home\data\nursing_facilities_nationwide.db'
PDF_PATH = r'd:\anti_gravity\nursing home\data\2025+노인복지시설+현황.pdf'

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

def main():
    parser = argparse.ArgumentParser(description="전국 요양원 PDF 추출 및 시딩")
    parser.add_argument('--start', type=int, required=True, help='시작 페이지 (0-indexed)')
    parser.add_argument('--end', type=int, required=True, help='종료 페이지 (0-indexed)')
    args = parser.parse_args()
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    print(f"Extracting nursing homes from page {args.start} to {args.end}...")
    
    count = 0
    with pdfplumber.open(PDF_PATH) as pdf:
        for i in range(args.start, args.end + 1):
            if i >= len(pdf.pages):
                break
                
            page = pdf.pages[i]
            
            # Extract text to verify it's the right section
            text = page.extract_text()
            if not text or '노인요양시설' not in text:
                continue
                
            tables = page.extract_tables()
            if not tables:
                continue
                
            for table in tables:
                for row in table:
                    if not row or len(row) < 13:
                        continue
                        
                    # Skip header rows
                    if row[0] and ("일련" in str(row[0]) or "연번" in str(row[0])):
                        continue
                    if row[1] and "시･군･구" in str(row[1]):
                        continue
                        
                    sigungu = clean_text(row[1])
                    if not sigungu or "계" in sigungu or "소" in sigungu or "합계" in sigungu:
                        continue
                        
                    name = clean_text(row[2])
                    
                    try:
                        capacity = int(clean_text(row[4]).replace(',', ''))
                    except:
                        capacity = 0
                        
                    try:
                        staff_count = int(clean_text(row[8]).replace(',', ''))
                    except:
                        staff_count = 0
                        
                    # Columns sometimes shift slightly, but usually address is around idx 11
                    address = clean_text(row[11])
                    
                    # If address looks like a phone number or date, it's shifted
                    if re.match(r'^[\d\-]+$', address) and len(address) > 8:
                        address = clean_text(row[10])
                        
                    # Validate address is mostly Korean/spaces
                    if name and address and len(address) > 5 and not address.isdigit():
                        # Determine sido from sigungu or default (PDF doesn't explicitly give sido for every row, but often it's in the header or implicit)
                        # For now, we will leave sido empty and rely on VWorld to find the full address coords.
                        sido = "" 
                        
                        cursor.execute('''
                            INSERT INTO nationwide_facilities (
                                facility_type, name, address, sido, sigungu, capacity, caregiver_count
                            ) VALUES (?, ?, ?, ?, ?, ?, ?)
                        ''', ('요양원', name, address, sido, sigungu, capacity, staff_count))
                        count += 1
                        
            if i % 10 == 0:
                print(f"Processed up to page {i}... extracted {count} homes.")
                conn.commit()
                
    conn.commit()
    print(f"Total extracted: {count} nursing homes!")
    conn.close()

if __name__ == "__main__":
    main()
