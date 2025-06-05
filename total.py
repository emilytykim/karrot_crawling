import os
import pandas as pd

# ─────────────────────────────────────────────
# 📁 기본 경로 설정
ROOT_DIR = "/Users/emily/karrot/"

# 🧑 사용자에게 지역 폴더명만 입력받기
subfolder = input("📂 폴더명을 입력하세요 (예: 나주시): ").strip()
region_name = input("🌍 지역구 이름을 입력하세요 (예: 나주시): ").strip()

base_dir = os.path.join(ROOT_DIR, subfolder)
output_file = os.path.join(base_dir, f"{region_name}_전체_통합.xlsx")

# ─────────────────────────────────────────────
# 🔄 통합 작업
total_df = pd.DataFrame()

for dong_folder in os.listdir(base_dir):
    dong_path = os.path.join(base_dir, dong_folder)

    if os.path.isdir(dong_path):
        csv_files = [
            f
            for f in os.listdir(dong_path)
            if f.endswith(".csv")
            and f.startswith("daangn_")
            and not f.endswith("_삽니다.csv")
        ]

        for file in csv_files:
            file_path = os.path.join(dong_path, file)
            try:
                df = pd.read_csv(file_path)
                df["동"] = dong_folder
                df["구"] = region_name
                total_df = pd.concat([total_df, df], ignore_index=True)
            except Exception as e:
                print(f"❌ 오류 - {dong_folder}/{file}: {e}")

# 컬럼 순서 정리
desired_order = ["구", "동", "category", "title", "price", "time"]
existing_columns = list(total_df.columns)
final_order = [col for col in desired_order if col in existing_columns] + [
    col for col in existing_columns if col not in desired_order
]

total_df = total_df[final_order]

# ✅ XLSX로 저장
total_df.to_excel(output_file, index=False, engine="openpyxl")
print(f"\n✅ '삽니다' 제외하고 엑셀 저장 완료: {output_file}")
