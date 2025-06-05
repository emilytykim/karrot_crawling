import os
import pandas as pd

# 📝 사용자에게 폴더명 입력 받기
folder_name = input("변환할 지역 폴더명을 입력하세요 (예: 나주시): ").strip()

# 📄 파일 경로 구성 (현재 디렉토리 기준)
csv_filename = f"{folder_name}_전체_통합.csv"
xlsx_filename = f"{folder_name}_전체_통합.xlsx"

csv_path = os.path.join(folder_name, csv_filename)
xlsx_path = os.path.join(folder_name, xlsx_filename)

# ✅ CSV → XLSX 변환
try:
    df = pd.read_csv(csv_path)
    df.to_excel(xlsx_path, index=False, engine="openpyxl")
    print(f"✅ 변환 완료: {xlsx_path}")
except Exception as e:
    print(f"❌ 변환 실패: {e}")
