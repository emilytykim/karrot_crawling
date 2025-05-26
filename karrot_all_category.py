import time, csv, os
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException

# ─── 1) 드라이버 세팅 ─────────────────────────────────────────
options = uc.ChromeOptions()
options.add_argument('--no-sandbox')
options.add_argument('--disable-dev-shm-usage')
driver = uc.Chrome(options=options)
wait = WebDriverWait(driver, 15)  # Increased timeout to 15 seconds

def safe_get_text(selector, timeout=5):
    """안전하게 텍스트 추출 (타임아웃 처리)"""
    try:
        element = WebDriverWait(driver, timeout).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, selector))
        )
        return element.text.strip()
    except:
        return "N/A"

# ─── 2) "송도동" 페이지 열고 카테고리만 추출 ────────────────────
try:
    driver.get("https://www.daangn.com/kr/buy-sell/?in=송도동-6543")
    time.sleep(2)

    # 카테고리 섹션 찾기
    category_section = wait.until(
        EC.presence_of_element_located((By.XPATH, "//h3[text()='카테고리']/following-sibling::div"))
    )
    
    # 카테고리 링크 추출
    cats = category_section.find_elements(By.CSS_SELECTOR, 'a[data-gtm="search_filter"]')
    categories = []
    
    for a in cats:
        try:
            name = a.find_element(By.TAG_NAME, "span").text.strip()
            href = a.get_attribute("href")
            if name and href and "category_id" in href:  # 실제 카테고리만 필터링
                categories.append((name, href))
        except:
            continue

    print("▶ 카테고리 인식:", [c[0] for c in categories])

    # ─── 3) 카테고리별 테스트 순회 ─────────────────────────────────
    for cat_name, cat_url in categories:
        safe = cat_name.replace("/", "_").replace("\\", "_")
        fn = f"daangn_송도동_{safe}.csv"
        print(f"\n▶ [{cat_name}] 테스트 시작 → {fn}")

        with open(fn, "w", newline="", encoding="utf-8-sig") as f:
            writer = csv.writer(f)
            writer.writerow(["카테고리", "상품명", "가격", "닉네임", "작성일자", "URL"])
            f.flush()

            try:
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
                        driver.execute_script("arguments[0].scrollIntoView({block:'center'});", btn)
                        btn.click()
                        time.sleep(1)
                    except:
                        break

                # (3) 최대 5개 상품 링크만
                anchors = driver.find_elements(By.CSS_SELECTOR, 'a[data-gtm="search_article"]')
                urls = []
                for a in anchors:
                    try:
                        href = a.get_attribute("href")
                        if href and "/kr/buy-sell/" in href and href not in urls:
                            urls.append(href)
                        if len(urls) >= 5:
                            break
                    except:
                        continue

                print(f"   ▶ [{cat_name}] {len(urls)}개 링크 수집 완료")

                # (4) 상세 크롤링 + 즉시 저장
                for idx, url in enumerate(urls, 1):
                    try:
                        driver.get(url)
                        time.sleep(1)

                        title = safe_get_text("h1.sprinkles_display_inline_base__1byufe82a")
                        price = safe_get_text("h3.jy3q4ib.sprinkles_fontWeight_bold__1byufe81z")
                        nickname = safe_get_text("span._1mr23zje")
                        date = safe_get_text("time")

                        writer.writerow([cat_name, title, price, nickname, date, url])
                        f.flush()
                        print(f"     {idx}/{len(urls)} 크롤링: {title}")

                    except Exception as e:
                        print(f"     ⚠️ {idx}번째 상품 크롤링 실패: {str(e)}")
                        continue

                print(f"✅ [{cat_name}] 테스트 CSV 생성됨 → {os.path.abspath(fn)}")

            except Exception as e:
                print(f"⚠️ [{cat_name}] 카테고리 처리 중 오류: {str(e)}")
                continue

except Exception as e:
    print(f"⚠️ 전체 스크립트 실행 중 오류: {str(e)}")

finally:
    driver.quit()
    print("\n🎉 카테고리 순회 + 테스트 완료!")
