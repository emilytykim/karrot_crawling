import time, csv, os
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# ─── 1) 드라이버 세팅 ─────────────────────────────────────────
driver = uc.Chrome()
wait   = WebDriverWait(driver, 10)

# ─── 2) “송도동” 페이지 열고 카테고리만 추출 ────────────────────
driver.get("https://www.daangn.com/kr/buy-sell/?in=송도동-6543")
time.sleep(2)

cats = driver.find_elements(
    By.XPATH,
    "//h3[text()='카테고리']/following-sibling::div//a[@data-gtm='search_filter']"
)
categories = [(a.find_element(By.TAG_NAME,"span").text.strip(),
               a.get_attribute("href")) for a in cats]
print("▶ 카테고리 인식:", [c[0] for c in categories])

# ─── 3) 카테고리별 테스트 순회 ─────────────────────────────────
for cat_name, cat_url in categories:
    safe = cat_name.replace("/", "_")
    fn   = f"daangn_송도동_{safe}.csv"
    print(f"\n▶ [{cat_name}] 테스트 시작 → {fn}")

    with open(fn, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.writer(f)
        writer.writerow(["카테고리","상품명","가격","닉네임","작성일자","URL"])
        f.flush()

        driver.get(cat_url)
        time.sleep(2)

        # (2) 스크롤 + 더보기 (최대 5회)
        for _ in range(5):
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(1)
            try:
                btn = wait.until(EC.element_to_be_clickable(
                    (By.XPATH, "//button[contains(text(),'더보기')]")
                ))
                btn.click()
                time.sleep(1)
            except:
                break

        # (3) 최대 5개 상품 링크만
        anchors = driver.find_elements(By.CSS_SELECTOR, 'a[data-gtm="search_article"]')
        urls = []
        for a in anchors:
            href = a.get_attribute("href")
            if href and "/kr/buy-sell/" in href and href not in urls:
                urls.append(href)
            if len(urls) >= 5:
                break
        print(f"   ▶ [{cat_name}] 5개 링크 수집 완료")

        # (4) 상세 크롤링 + 즉시 저장
        for idx, url in enumerate(urls, 1):
            driver.get(url)
            time.sleep(1)
            def get_text(sel):
                try:    return driver.find_element(By.CSS_SELECTOR, sel).text
                except: return "N/A"

            title    = get_text("h1.sprinkles_display_inline_base__1byufe82a")
            price    = get_text("h3.jy3q4ib.sprinkles_fontWeight_bold__1byufe81z")
            nickname = get_text("span._1mr23zje")
            date     = get_text("time")

            writer.writerow([cat_name, title, price, nickname, date, url])
            f.flush()
            print(f"     {idx}/5 크롤링: {title}")

    print(f"✅ [{cat_name}] 테스트 CSV 생성됨 → {os.path.abspath(fn)}")

driver.quit()
print("\n🎉 카테고리 순회 + 5개 테스트 완료!")
