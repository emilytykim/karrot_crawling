import time
import csv
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# 1) 드라이버 세팅
options = uc.ChromeOptions()
options.add_argument('--no-sandbox')
options.add_argument('--disable-dev-shm-usage')
options.add_argument('--disable-gpu')
# options.add_argument('--headless')  # 필요시 활성화
driver = uc.Chrome(options=options)
wait = WebDriverWait(driver, 10)

# 2) 시작 페이지 열기
start_url = "https://www.daangn.com/kr/buy-sell/?category_id=1&in=송도동-6543"
driver.get(start_url)
time.sleep(2)

# 3) 스크롤 & '더보기' 클릭 (최대 5회)
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
        print("❌ 더보기 없음 or 실패")
        break

# 4) 상품 링크 수집: data-gtm="search_article" 인 <a> 태그
anchors = driver.find_elements(By.CSS_SELECTOR, 'a[data-gtm="search_article"]')
print("▶ 발견된 상품 링크 개수:", len(anchors))

item_urls = []
for a in anchors:
    href = a.get_attribute("href")
    if href and "/kr/buy-sell/" in href and href not in item_urls:
        item_urls.append(href)
print("▶ 고유 상품 URL 개수:", len(item_urls))

# 5) 상세 페이지 순회 및 데이터 추출
results = []
for idx, url in enumerate(item_urls, 1):
    driver.get(url)
    time.sleep(1.2)
    try:
        title = driver.find_element(By.CSS_SELECTOR, "h1.sprinkles_display_inline_base__1byufe82a").text
    except:
        title = "N/A"
    try:
        price = driver.find_element(By.CSS_SELECTOR, "h3.jy3q4ib.sprinkles_fontWeight_bold__1byufe81z").text
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

    print(f"{idx:02}. {title} | {price} | {nickname} | {date}")
    results.append([title, price, nickname, date, url])

# 6) CSV 저장
with open("daangn_digital_송도동.csv", "w", newline="", encoding="utf-8-sig") as f:
    writer = csv.writer(f)
    writer.writerow(["상품명", "가격", "닉네임", "작성일자", "URL"])
    writer.writerows(results)

# 7) 드라이버 종료
driver.quit()
print("✅ 크롤링 & CSV 저장 완료: daangn_digital_송도동.csv")
