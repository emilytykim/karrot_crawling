import os, json, csv, urllib.parse, requests
from datetime import datetime

CATEGORIES_FILE = "categories.json"
REGIONS_FOLDER = "regions_two"
PROGRESS_FOLDER = "crawling_progress"

os.makedirs(PROGRESS_FOLDER, exist_ok=True)

with open(CATEGORIES_FILE, "r", encoding="utf-8") as f:
    categories = json.load(f)

HEADERS = {
    "Accept": "application/json",
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
}


def fetch_json(region_in, category_id):
    url = (
        "https://www.daangn.com/kr/buy-sell/"
        f"?category_id={category_id}"
        f"&in={urllib.parse.quote(region_in)}"
        "&_data=routes%2Fkr.buy-sell._index"
    )
    resp = requests.get(url, headers=HEADERS, timeout=10, verify=False)
    resp.raise_for_status()
    return resp.json()


def load_progress(progress_file):
    if os.path.exists(progress_file):
        with open(progress_file, "r", encoding="utf-8") as f:
            return set(json.load(f))
    return set()


def save_progress(progress_file, region_name):
    processed = load_progress(progress_file)
    processed.add(region_name)
    with open(progress_file, "w", encoding="utf-8") as f:
        json.dump(list(processed), f, ensure_ascii=False, indent=2)


def crawl_region_file(region_file_path):
    district_name = os.path.splitext(os.path.basename(region_file_path))[0].split("_")[
        1
    ]
    progress_file = os.path.join(
        PROGRESS_FOLDER, f"crawling_progress_{district_name}_http.json"
    )
    os.makedirs(district_name, exist_ok=True)

    with open(region_file_path, "r", encoding="utf-8") as f:
        regions = json.load(f)

    processed = load_progress(progress_file)
    to_crawl = [r for r in regions if r["name"] not in processed]

    print(
        f"\n📍[{district_name}] 총 {len(regions)}개 동 중, 크롤링 대상: {len(to_crawl)}개 동"
    )
    for r in to_crawl:
        print(f"  - {r['name']}")

    for region in to_crawl:
        region_name = region["name"]
        print(f"\n🔄 [{region_name}] 크롤링 시작 – {datetime.now():%Y-%m-%d %H:%M:%S}")

        qs = urllib.parse.parse_qs(urllib.parse.urlparse(region["url"]).query)
        region_in = qs.get("in", [""])[0]
        if not region_in:
            print(f"❌ [{region_name}] region_in 파싱 실패: {region['url']}")
            continue

        os.makedirs(os.path.join(district_name, region_name), exist_ok=True)

        for cat in categories:
            cat_name = cat["name"].replace("/", "-")
            qs2 = urllib.parse.parse_qs(urllib.parse.urlparse(cat["url"]).query)
            category_id = qs2.get("category_id", [""])[0] or "1"

            print(
                f"▶ [{region_name}][{cat_name}] JSON 호출 (category_id={category_id})"
            )
            try:
                data = fetch_json(region_in, category_id)
            except Exception as e:
                print(f"   ⚠️ [{region_name}][{cat_name}] JSON 호출 실패: {e}")
                continue

            all_page = data.get("allPage", {})
            articles = all_page.get("fleamarketArticles", [])

            if not isinstance(articles, list) or len(articles) == 0:
                print(f"   ⏳ [{region_name}][{cat_name}] 상품 목록 없음")
                continue

            csv_path = os.path.join(
                district_name, region_name, f"daangn_{region_name}_{cat_name}.csv"
            )
            with open(csv_path, "w", newline="", encoding="utf-8-sig") as f:
                writer = csv.writer(f)
                writer.writerow(
                    ["카테고리", "상품명", "가격", "작성일자", "판매상태", "URL"]
                )
                f.flush()

                for idx, item in enumerate(articles, 1):
                    try:
                        title = item.get("title", "").strip()
                        price = item.get("price") or item.get("priceText", "")
                        created_at = item.get("createdAt", "")
                        sold_out = item.get("isSoldOut", False)
                        status = "판매완료" if sold_out else "판매중"
                        detail_url = f"https://www.daangn.com/articles/{item.get('id')}"

                        writer.writerow(
                            [cat_name, title, price, created_at, status, detail_url]
                        )
                        f.flush()
                        print(f"     {idx}/{len(articles)} [{status}] {title}")
                    except Exception as e:
                        print(f"     ⚠️ {idx}번째 상품 파싱 실패: {e}")

            print(f"   ✅ CSV 저장 완료 → {csv_path}")

        save_progress(progress_file, region_name)
        print(
            f"✅ [{region_name}] JSON 크롤링 완료 – {datetime.now():%Y-%m-%d %H:%M:%S}"
        )


if __name__ == "__main__":
    region_files = [f for f in os.listdir(REGIONS_FOLDER) if f.endswith(".json")]
    print(f"\n📂 총 {len(region_files)}개 지역 파일 순회 시작")

    for region_file in region_files:
        full_path = os.path.join(REGIONS_FOLDER, region_file)
        try:
            crawl_region_file(full_path)
        except Exception as e:
            print(f"❌ [{region_file}] 크롤링 중 오류 발생: {e}")

    print("\n🎉 모든 지역의 크롤링 완료")
