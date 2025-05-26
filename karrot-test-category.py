import csv
import os
import logging
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException

# ─── 설정 ─────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
    datefmt="%H:%M:%S"
)

options = uc.ChromeOptions()
options.add_argument('--no-sandbox')
options.add_argument('--disable-dev-shm-usage')
options.add_argument('--disable-gpu')
driver = uc.Chrome(options=options)
wait = WebDriverWait(driver, 10)

# ─── 1) “송도동” 페이지 열고 카테고리 링크 수집 ──────────────────────────
driver.get("https://www.daangn.com/kr/buy-sell/?in=송도동-6543")
# 카테고리 링크가 로드될 때까지 대기
wait.until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, 'a[data-gtm="search_filter"]')))
cats = driver.find_elements(By.CSS_SELECTOR, 'a[data-gtm="search_filter"]')

categories = []
for a in cats:
    spans = a.find_elements(By.TAG_NAME, "span")   # 없으면 []
    if not spans:
        continue
    name = spans[0].text.strip()
    href = a.get_attribute("href")
    categories.append((name, href))

logging.info(f"Found categories: {[n for n, _ in categories]}")

# ─── 2) 각 카테고리별 크롤링 & CSV 저장 ─────────────────────────────────
for cat_name, cat_url in categories:
    safe_name = cat_name.replace("/", "_")
    filename = f"daangn_송도동_{safe_name}.csv"
    logging.info(f"Starting category: {cat_name}")

    with open(filename, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.writer(f)
        writer.writerow(["동네", "카테고리", "상품명", "가격", "닉네임", "작성일자", "URL"])

        # 카테고리 페이지 열기
        driver.get(cat_url)
        wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))

        # 테스트용: 스크롤 + '더보기' 클릭 1회
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        try:
            btn = wait.until(EC.element_to_be_clickable(
                (By.XPATH, "//button[contains(text(),'더보기')]")
            ))
            driver.execute_script("arguments[0].click();", btn)
            wait.until(EC.staleness_of(btn))
        except TimeoutException:
            logging.info("더보기 버튼 없음 혹은 클릭 불가")

        # 상품 링크 수집 (테스트용: 최대 5개)
        anchors = driver.find_elements(By.CSS_SELECTOR, 'a[data-gtm="search_article"]')
        item_urls = []
        for a in anchors:
            href = a.get_attribute("href")
            if href and "/kr/buy-sell/" in href and href not in item_urls:
                item_urls.append(href)
            if len(item_urls) >= 5:
                break
        logging.info(f"▶ 테스트용으로 5개만 가져옵니다: {len(item_urls)}개")

        # 상세 페이지 순회 & 중간 저장
        for idx, url in enumerate(item_urls, start=1):
            driver.get(url)
            wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))

            try:
                title = driver.find_element(
                    By.CSS_SELECTOR,
                    "h1.sprinkles_display_inline_base__1byufe82a"
                ).text
            except:
                title = "N/A"
            try:
                price = driver.find_element(
                    By.CSS_SELECTOR,
                    "h3.jy3q4ib.sprinkles_fontWeight_bold__1byufe81z"
                ).text
            except:
                price = "N/A"
            try:
                nickname = driver.find_element(By.CSS_SELECTOR, "span._1mr23zje").text
            except:
                nickname = "N/A"
            try:
                date = driver.find_element(By.TAG_NAME, "time").text
            except:
                date = "N/A"

            writer.writerow(["송도동", cat_name, title, price, nickname, date, url])
            f.flush()
            logging.info(f"  {idx}/{len(item_urls)}: {title}")

    logging.info(f"✅ {cat_name} 완료 → {os.path.abspath(filename)}")

driver.quit()
logging.info("🎉 모든 카테고리 크롤링 완료!")
