import os, json, csv, urllib.parse, requests
from datetime import datetime

with open("regions/regions_gwangmyeong.json", "r", encoding="utf-8") as f:
    regions = json.load(f)
with open("categories.json", "r", encoding="utf-8") as f:
    categories = json.load(f)

DISTRICT_NAME = "Gwangmyeong"
PROGRESS_FILE = "crawling_progress/crawling_progress_gwangmyeong_http.json"

def load_progress():
    if os.path.exists(PROGRESS_FILE):
        with open(PROGRESS_FILE, 'r', encoding='utf-8') as f:
            return set(json.load(f))
    return set()

def save_progress(region_name):
    processed = load_progress()
    processed.add(region_name)
    with open(PROGRESS_FILE, 'w', encoding='utf-8') as f:
        json.dump(list(processed), f, ensure_ascii=False, indent=2)

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
    # 개발 테스트용으로만 verify=False 사용
    resp = requests.get(url, headers=HEADERS, timeout=10, verify=False)
    resp.raise_for_status()
    return resp.json()

if __name__ == "__main__":
    os.makedirs(DISTRICT_NAME, exist_ok=True)
    processed = load_progress()
    to_crawl = [r for r in regions if r["name"] not in processed]

    print(f"📋 총 {len(regions)}개 동 중, HTTP 크롤링 대상: {len(to_crawl)}개 동")
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

        os.makedirs(os.path.join(DISTRICT_NAME, region_name), exist_ok=True)

        for cat in categories:
            cat_name = cat["name"].replace("/", "-")
            qs2 = urllib.parse.parse_qs(urllib.parse.urlparse(cat["url"]).query)
            category_id = qs2.get("category_id", [""])[0] or "1"

            print(f"▶ [{region_name}][{cat_name}] JSON 호출 (category_id={category_id})")
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
                DISTRICT_NAME,
                region_name,
                f"daangn_{region_name}_{cat_name}.csv"
            )
            with open(csv_path, "w", newline="", encoding="utf-8-sig") as f:
                writer = csv.writer(f)
                writer.writerow(["카테고리", "상품명", "가격", "작성일자", "판매상태", "URL"])
                f.flush()

                for idx, item in enumerate(articles, 1):
                    try:
                        title      = item.get("title", "").strip()
                        price      = item.get("price") or item.get("priceText", "")
                        created_at = item.get("createdAt", "")
                        sold_out   = item.get("isSoldOut", False)
                        status     = "판매완료" if sold_out else "판매중"
                        detail_url = f"https://www.daangn.com/articles/{item.get('id')}"

                        writer.writerow([cat_name, title, price, created_at, status, detail_url])
                        f.flush()
                        print(f"     {idx}/{len(articles)} [{status}] {title}")
                    except Exception as e:
                        print(f"     ⚠️ {idx}번째 상품 파싱 실패: {e}")

            print(f"   ✅ CSV 저장 완료 → {csv_path}")

        save_progress(region_name)
        print(f"✅ [{region_name}] JSON 크롤링 완료 – {datetime.now():%Y-%m-%d %H:%M:%S}")

    print("\n🎉 모든 동×카테고리 HTTP 크롤링 완료 (광명시)")
