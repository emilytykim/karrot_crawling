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

# ─── 2) "역삼동" 페이지 열고 카테고리만 추출 ────────────────────
try:
    driver.get("https://www.daangn.com/kr/buy-sell/?category_id=1&in=역삼동-6035")
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

    # ─── 3) 카테고리별 순회 ─────────────────────────────────
    for cat_name, cat_url in categories:
        safe = cat_name.replace("/", "_").replace("\\", "_")
        fn = f"daangn_역삼동_{safe}.csv"
        print(f"\n▶ [{cat_name}] 크롤링 시작 → {fn}")

        with open(fn, "w", newline="", encoding="utf-8-sig") as f:
            writer = csv.writer(f)
            writer.writerow(["카테고리", "상품명", "가격", "작성일자", "판매상태", "URL"])
            f.flush()

            try:
                driver.get(cat_url)
                time.sleep(2)

                # (2) 스크롤 + 더보기 (버튼이 없을 때까지)
                more_click_count = 0
                while True:
                    driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                    time.sleep(1)
                    try:
                        btn = wait.until(EC.element_to_be_clickable(
                            (By.XPATH, "//button[contains(text(),'더보기')]")
                        ))
                        driver.execute_script("arguments[0].scrollIntoView({block:'center'});", btn)
                        btn.click()
                        more_click_count += 1
                        print(f"     더보기 클릭 ({more_click_count}회)")
                        time.sleep(1)
                    except:
                        print(f"     더보기 버튼 없음 (총 {more_click_count}회 클릭)")
                        break

                # (3) 모든 상품 링크 수집
                cards = driver.find_elements(By.CSS_SELECTOR, 'a[data-gtm="search_article"]')
                print(f"   ▶ [{cat_name}] {len(cards)}개 상품 발견")
                for idx, card in enumerate(cards, 1):
                    # 상품명
                    name  = card.find_element(By.CSS_SELECTOR, 'span.lm809sh').text.strip()
                    # 가격
                    price = card.find_element(By.CSS_SELECTOR, 'span.lm809si').text.strip()
                    # 작성 시간 (time 태그)
                    time_text = card.find_element(By.TAG_NAME, 'time').text.strip()
                    # 판매완료 여부: "판매완료" 또는 "예약중" span이 있으면 그 텍스트, 없으면 "판매중"
                    try:
                        status = card.find_element(By.CSS_SELECTOR, 'span.mlbp660').text.strip()
                    except NoSuchElementException:
                        status = "판매중"

                    # CSV에 쓰기
                    writer.writerow([cat_name, name, price, time_text, status, card.get_attribute('href')])
                    f.flush()
                    print(f"     {idx}/{len(cards)} [{status}] {name}")

                print(f"✅ [{cat_name}] CSV 생성됨 → {os.path.abspath(fn)}")

            except Exception as e:
                print(f"⚠️ [{cat_name}] 카테고리 처리 중 오류: {str(e)}")
                continue

except Exception as e:
    print(f"⚠️ 전체 스크립트 실행 중 오류: {str(e)}")

finally:
    driver.quit()
    print("\n🎉 카테고리 순회 + 크롤링 완료!")

regions = [
    ("역삼동", "https://www.daangn.com/kr/buy-sell/?category_id=1&in=역삼동-6035"),
] 