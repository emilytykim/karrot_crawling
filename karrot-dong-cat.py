import json, os, csv, time
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException, TimeoutException
import urllib.parse
import re

# ─── 캐시된 JSON 읽기 ───────────────────────────────
# with open("regions_gangnam.json","r",encoding="utf-8") as f:
#     regions = json.load(f)
with open("regions_gangnam_remaining.json","r",encoding="utf-8") as f:
    regions = json.load(f)
with open("categories.json","r",encoding="utf-8") as f:
    categories = json.load(f)

class KarrotCrawler:
    def __init__(self):
        # Chrome 옵션 설정
        opts = uc.ChromeOptions()
        opts.add_argument('--no-sandbox')
        opts.add_argument('--disable-dev-shm-usage')
        opts.add_argument('--disable-blink-features=AutomationControlled')
        opts.add_argument('--disable-infobars')
        opts.add_argument('--disable-extensions')
        opts.add_argument('--start-maximized')
        opts.add_argument('--disable-gpu')
        opts.add_argument('--window-size=1920,1080')
        opts.add_argument('--ignore-certificate-errors')
        opts.add_argument('--allow-running-insecure-content')
        opts.add_argument('--disable-web-security')
        opts.add_argument('--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
        
        # 추가 옵션
        opts.add_argument('--disable-popup-blocking')
        opts.add_argument('--disable-notifications')
        opts.add_argument('--disable-default-apps')
        opts.add_argument('--disable-save-password-bubble')
        opts.add_argument('--disable-translate')
        opts.add_argument('--disable-features=IsolateOrigins,site-per-process')
        
        # 캐시 및 쿠키 초기화 옵션 추가
        opts.add_argument('--incognito')  # 시크릿 모드
        opts.add_argument('--disable-application-cache')
        opts.add_argument('--disable-cache')
        opts.add_argument('--disable-offline-load-stale-cache')
        opts.add_argument('--disk-cache-size=0')
        
        # 드라이버 초기화 시도
        max_retries = 3
        for attempt in range(max_retries):
            try:
                # 기존 드라이버가 있다면 종료
                try:
                    self.driver.quit()
                except:
                    pass
                
                # 새로운 드라이버 생성
                self.driver = uc.Chrome(options=opts)
                self.wait = WebDriverWait(self.driver, 15)
                
                # 쿠키 및 캐시 삭제
                self.driver.delete_all_cookies()
                
                # 역삼동 페이지로 직접 이동
                self.driver.get("https://www.daangn.com/kr/buy-sell/?in=행운동-344")
                time.sleep(5)
                
                # 페이지가 제대로 로드되었는지 확인
                try:
                    self.wait.until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, 'button[data-gtm="gnb_location"]'))
                    )
                    print("✅ 행운동 페이지 로드 성공")
                    return
                except:
                    print("⚠️ 행운동 페이지 로드 실패, 재시도...")
                    continue
                    
            except Exception as e:
                print(f"⚠️ 드라이버 초기화 실패 (시도 {attempt + 1}/{max_retries}): {str(e)}")
                if attempt < max_retries - 1:
                    time.sleep(5)
                    continue
                raise Exception("드라이버 초기화 실패")

    def safe_get(self, url, max_retries=3):
        """안전하게 페이지 로드 (재시도 로직 포함)"""
        for attempt in range(max_retries):
            try:
                # 현재 URL 확인
                current_url = self.driver.current_url
                if current_url != url:
                    self.driver.get(url)
                    time.sleep(5)
                
                # 페이지가 제대로 로드되었는지 확인
                self.wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))
                return True
            except Exception as e:
                print(f"⚠️ 페이지 로드 실패 (시도 {attempt + 1}/{max_retries}): {str(e)}")
                if attempt < max_retries - 1:
                    # 드라이버 재초기화 시도
                    try:
                        self.driver.quit()
                    except:
                        pass
                    time.sleep(5)
                    self.__init__()  # 드라이버 재초기화
                    continue
                return False
        return False

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
        
        # 안전하게 페이지 로드
        if not self.safe_get(full_url):
            print(f"⚠️ [{region_name}][{cat['name']}] 페이지 로드 실패, 다음으로 넘어갑니다.")
            return

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