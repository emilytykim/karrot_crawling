import time
import csv
import json
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# 카테고리 정보 로드
with open("categories.json", "r", encoding="utf-8") as f:
    categories = json.load(f)
    # 카테고리 ID를 키로 하는 딕셔너리 생성
    category_dict = {cat["url"].split("category_id=")[1].split("&")[0]: cat["name"] for cat in categories}

def crawl_category(category):
    """한 카테고리 크롤링"""
    category_id = category["url"].split("category_id=")[1].split("&")[0]
    category_name = category["name"]
    
    # 시작 URL 설정
    start_url = f"https://www.daangn.com/kr/buy-sell/?category_id={category_id}&in=장수읍-2687"
    print(f"\n▶ {category_name} 카테고리 크롤링 시작...")
    
    driver.get(start_url)
    time.sleep(2)

    # 스크롤 & '더보기' 클릭
    for i in range(5):
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(1.5)
        try:
            btn = wait.until(EC.element_to_be_clickable(
                (By.XPATH, "//button[contains(text(), '더보기')]")
            ))
            driver.execute_script("arguments[0].scrollIntoView({block:'center'});", btn)
            driver.execute_script("arguments[0].click();", btn)
            print(f"✅ {i+1}번째 더보기 클릭")
            time.sleep(1.5)
        except:
            break

    # 상품 링크 수집
    anchors = driver.find_elements(By.CSS_SELECTOR, 'a[data-gtm="search_article"]')
    item_urls = []
    for a in anchors:
        href = a.get_attribute("href")
        if href and "/kr/buy-sell/" in href and href not in item_urls:
            item_urls.append(href)

    print(f"▶ {category_name} 고유 상품 URL 개수: {len(item_urls)}")

    # 상세 페이지 순회 및 저장
    for idx, url in enumerate(item_urls, 1):
        driver.get(url)
        time.sleep(1.2)

        # 데이터 추출
        try:    title = driver.find_element(By.CSS_SELECTOR, "h1.sprinkles_display_inline_base__1byufe82a").text
        except: title = "N/A"
        try:    price = driver.find_element(By.CSS_SELECTOR, "h3.jy3q4ib.sprinkles_fontWeight_bold__1byufe81z").text
        except: price = "N/A"
        try:    nickname = driver.find_element(By.CSS_SELECTOR, "span._1mr23zje").text
        except: nickname = "N/A"
        try:    date = driver.find_element(By.TAG_NAME, "time").text
        except: date = "N/A"

        # 즉시 쓰기 & flush
        writer.writerow(["장수읍", category_name, title, price, nickname, date, url])
        csv_file.flush()

        print(f"{idx:03}/{len(item_urls)}: {title} | {price} | {nickname} | {date}")

# 1) 드라이버 세팅
options = uc.ChromeOptions()
options.add_argument('--no-sandbox')
options.add_argument('--disable-dev-shm-usage')
options.add_argument('--disable-gpu')
driver = uc.Chrome(options=options)
wait = WebDriverWait(driver, 10)

# CSV 파일 열기
csv_file = open("daangn_장수읍.csv", "w", newline="", encoding="utf-8-sig")
writer = csv.writer(csv_file)
writer.writerow(["동네", "카테고리", "상품명", "가격", "닉네임", "작성일자", "URL"])
csv_file.flush()

try:
    # 모든 카테고리 순회 (디지털기기 제외)
    for category in categories:
        category_id = category["url"].split("category_id=")[1].split("&")[0]
        if category_id == "1":  # 디지털기기 카테고리 건너뛰기
            print(f"⏭️ 디지털기기 카테고리 건너뛰기")
            continue
            
        try:
            crawl_category(category)
        except Exception as e:
            print(f"⚠️ {category['name']} 카테고리 처리 중 오류: {str(e)}")
            continue

except KeyboardInterrupt:
    print("⚠️ 중간에 중단! 현재까지 daangn_partial.csv에 저장되었습니다.")

finally:
    csv_file.close()
    driver.quit()
    print("✅ 스크립트 종료, 파일 닫음")