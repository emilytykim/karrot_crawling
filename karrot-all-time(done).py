import json, os, csv, time
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException, TimeoutException
import urllib.parse
import re

# ─── 캐시된 JSON 읽기 ───────────────────────────────
with open("regions_gangnam_remaining.json","r",encoding="utf-8") as f:
    regions = json.load(f)
with open("categories.json","r",encoding="utf-8") as f:
    categories = json.load(f)

class KarrotCrawler:
    def __init__(self):
        opts = uc.ChromeOptions()
        opts.add_argument('--no-sandbox')
        opts.add_argument('--disable-dev-shm-usage')
        opts.add_argument('--disable-blink-features=AutomationControlled')
        opts.add_argument('--disable-infobars')
        opts.add_argument('--disable-extensions')
        opts.add_argument('--start-maximized')
        self.driver = uc.Chrome(options=opts)
        self.wait   = WebDriverWait(self.driver, 15)  # 타임아웃 15초로 증가

    def process_category(self, region, cat):
        """한 동네에서 한 카테고리 크롤링"""
        cat_name = cat["name"].replace("/", "-")  # 슬래시를 하이픈으로 변경
        region_name = region["name"]
        # region["url"]에서 in=... 부분만 추출 (한글)
        m = re.search(r"in=([^&]+)", region["url"])
        if m:
            region_in = m.group(1)
        else:
            region_in = ""
        # cat["url"]에서 category_id 추출
        m2 = re.search(r"category_id=(\d+)", cat["url"])
        cat_id = m2.group(1) if m2 else "1"
        # in=... 부분만 region의 한글로 교체 (인코딩해서)
        cat_url = re.sub(r"in=[^&]+", f"in={urllib.parse.quote(region_in)}", cat["url"])
        full_url = "https://www.daangn.com" + cat_url
        print(f"\n▶ [{region_name}][{cat['name']}] 크롤링 시작")
        self.driver.get(full_url)
        time.sleep(2)

        # 동네별 폴더 생성
        os.makedirs(region_name, exist_ok=True)
        fn = f"daangn_{region_name}_{cat_name}.csv"
        with open(os.path.join(region_name, fn), "w", newline="", encoding="utf-8-sig") as f:
            w = csv.writer(f)
            w.writerow(["카테고리","상품명","가격","작성일자","판매상태","URL"])
            f.flush()

            try:
                # (2) 스크롤 + 더보기 (버튼이 없을 때까지)
                more_click_count = 0
                while more_click_count < 5:  # 최대 5회로 제한
                    self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                    time.sleep(1)
                    try:
                        btn = self.wait.until(EC.element_to_be_clickable(
                            (By.XPATH, "//button[contains(text(),'더보기')]")
                        ))
                        self.driver.execute_script("arguments[0].scrollIntoView({block:'center'});", btn)
                        btn.click()
                        more_click_count += 1
                        print(f"     더보기 클릭 ({more_click_count}/5)")
                        time.sleep(1)
                    except:
                        print(f"     더보기 버튼 없음 (총 {more_click_count}회 클릭)")
                        break

                # (3) 모든 상품 카드 수집
                cards = self.driver.find_elements(By.CSS_SELECTOR, 'a[data-gtm="search_article"]')
                print(f"   ▶ [{cat['name']}] {len(cards)}개 상품 발견")
                
                for idx, card in enumerate(cards, 1):
                    try:
                        name  = card.find_element(By.CSS_SELECTOR, 'span.lm809sh').text.strip()
                        price = card.find_element(By.CSS_SELECTOR, 'span.lm809si').text.strip()
                        time_ = card.find_element(By.TAG_NAME, 'time').text.strip()
                        try:
                            status = card.find_element(By.CSS_SELECTOR,'span.mlbp660').text.strip()
                        except NoSuchElementException:
                            status = "판매중"
                        
                        w.writerow([cat["name"], name, price, time_, status, card.get_attribute("href")])
                        f.flush()
                        print(f"     {idx}/{len(cards)} [{status}] {name}")
                    except Exception as e:
                        print(f"     ⚠️ {idx}번째 상품 처리 실패: {str(e)}")
                        continue

                print(f"✅ [{region_name}][{cat['name']}] → {region_name}/{fn}")

            except Exception as e:
                print(f"⚠️ [{region_name}][{cat['name']}] 카테고리 처리 중 오류: {str(e)}")

    def close(self):
        self.driver.quit()

crawler = KarrotCrawler()
try:
    for region in regions:
        for cat in categories:
            crawler.process_category(region, cat)
finally:
    crawler.close()
    print("\n🎉 모든 동네×카테고리 크롤링 완료!") 