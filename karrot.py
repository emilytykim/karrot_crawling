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
driver = uc.Chrome(options=options)
wait = WebDriverWait(driver, 10)

# 2) 시작 페이지 열기
start_url = "https://www.daangn.com/kr/buy-sell/?category_id=1&in=송도동-6543"
driver.get(start_url)
time.sleep(2)

# 3) 스크롤 & '더보기' 클릭
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

# 4) 상품 링크 수집
anchors = driver.find_elements(By.CSS_SELECTOR, 'a[data-gtm="search_article"]')
item_urls = []
for a in anchors:
    href = a.get_attribute("href")
    if href and "/kr/buy-sell/" in href and href not in item_urls:
        item_urls.append(href)

print("▶ 고유 상품 URL 개수:", len(item_urls))

# 5) CSV 파일을 열고 헤더 먼저 쓰기
csv_file = open("daangn_partial.csv", "w", newline="", encoding="utf-8-sig")
writer = csv.writer(csv_file)
writer.writerow(["상품명", "가격", "닉네임", "작성일자", "URL"])
csv_file.flush()

# 6) 상세 페이지 순회 및 중간중간 저장
try:
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
        writer.writerow([title, price, nickname, date, url])
        csv_file.flush()

        print(f"{idx:03}/{len(item_urls)}: {title} | {price} | {nickname} | {date}")

except KeyboardInterrupt:
    print("⚠️ 중간에 중단! 현재까지 daangn_partial.csv에 저장되었습니다.")

finally:
    csv_file.close()
    driver.quit()
    print("✅ 스크립트 종료, 파일 닫음")
