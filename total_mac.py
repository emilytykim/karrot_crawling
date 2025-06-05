import os
import pandas as pd

# 🔧 경로 설정
base_dir = "/Users/emily/karrot/공주시"
output_file = os.path.join(base_dir, "공주시_전체_통합.csv")

gangnam_total_df = pd.DataFrame()

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
                df["구"] = "공주시"
                gangnam_total_df = pd.concat([gangnam_total_df, df], ignore_index=True)
            except Exception as e:
                print(f"❌ 오류 - {dong_folder}/{file}: {e}")

# 컬럼 순서 정리
desired_order = ["구", "동", "category", "title", "price", "time"]
existing_columns = list(gangnam_total_df.columns)
final_order = [col for col in desired_order if col in existing_columns] + [
    col for col in existing_columns if col not in desired_order
]

gangnam_total_df = gangnam_total_df[final_order]

# ✅ CSV로 저장
gangnam_total_df.to_csv(output_file, index=False, encoding="utf-8-sig")
print(f"\n✅ '삽니다' 제외하고 CSV 저장 완료: {output_file}")
