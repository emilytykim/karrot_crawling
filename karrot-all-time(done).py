import json, os, csv, time
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException, TimeoutException, WebDriverException
import urllib.parse
import re

# ─── 서울시 구 리스트 ───────────────────────────────
SEOUL_DISTRICTS = [
    "강남구", "강동구", "강북구", "강서구", "관악구", "광진구", "구로구", "금천구",
    "노원구", "도봉구", "동대문구", "동작구", "마포구", "서대문구", "서초구", "성동구",
    "성북구", "송파구", "양천구", "영등포구", "용산구", "은평구", "종로구", "중구", "중랑구"
]

# ─── 캐시된 JSON 읽기 ───────────────────────────────
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
        opts.add_argument('--disable-gpu')
        opts.add_argument('--window-size=1920,1080')
        opts.add_argument('--ignore-certificate-errors')
        opts.add_argument('--allow-running-insecure-content')
        opts.add_argument('--disable-web-security')
        opts.add_argument('--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
        self.driver = uc.Chrome(options=opts)
        self.wait   = WebDriverWait(self.driver, 15)

    def safe_get(self, url, max_retries=3):
        """안전하게 페이지 로드 (재시도 로직 포함)"""
        for attempt in range(max_retries):
            try:
                self.driver.get(url)
                time.sleep(2)
                return True
            except WebDriverException as e:
                print(f"⚠️ 페이지 로드 실패 (시도 {attempt + 1}/{max_retries}): {str(e)}")
                if attempt < max_retries - 1:
                    time.sleep(2)
                    continue
                return False
        return False

    def get_district_dongs(self, district):
        """구 이름으로 동네 정보 수집"""
        print(f"\n▶ [{district}] 동네 정보 수집 시작")
        
        # 홈페이지로 이동
        if not self.safe_get("https://www.daangn.com/kr/"):
            print(f"⚠️ [{district}] 홈페이지 로드 실패")
            return []

        try:
            # 검색창 찾기
            search_input = self.wait.until(
                EC.presence_of_element_located((By.CSS_SELECTOR, 'input[type="search"]'))
            )
            search_input.clear()
            search_input.send_keys(district)
            time.sleep(1)  # 자동완성 대기

            # 자동완성 리스트의 첫 번째 항목 클릭
            first_item = self.wait.until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, 'ul li a'))
            )
            href = first_item.get_attribute("href")
            first_item.click()
            time.sleep(2)

            # '위치' 섹션의 더보기 클릭
            more_btn = self.wait.until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, 'button[data-gtm="search_show_more_options"]'))
            )
            more_btn.click()
            time.sleep(1)

            # '위치' 섹션의 모든 동네 링크 추출
            location_section = self.wait.until(
                EC.presence_of_element_located((By.XPATH, "//h3[text()='위치']/following-sibling::div[1]"))
            )
            links = location_section.find_elements(By.CSS_SELECTOR, 'a[data-gtm="search_filter"]')
            
            dongs = []
            for a in links:
                try:
                    name = a.text.strip()
                    path = a.get_attribute("href").replace("https://www.daangn.com", "")
                    # 퍼센트 인코딩을 한글로 디코딩
                    path = urllib.parse.unquote(path)
                    dongs.append({"name": name, "url": path})
                except:
                    continue

            print(f"✅ [{district}] {len(dongs)}개 동네 발견")
            return dongs

        except Exception as e:
            print(f"⚠️ [{district}] 동네 정보 수집 실패: {str(e)}")
            return []

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
                # (2) 스크롤 + 더보기 (최대 5번)
                click_count = 0
                for _ in range(5):  # 최대 5번 시도
                    self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                    time.sleep(1)
                    try:
                        btn = self.wait.until(EC.element_to_be_clickable(
                            (By.XPATH, "//button[contains(text(),'더보기')]")
                        ))
                        self.driver.execute_script("arguments[0].scrollIntoView({block:'center'});", btn)
                        btn.click()
                        click_count += 1
                        print(f"     더보기 클릭 ({click_count}/5)")
                        time.sleep(1)
                    except:
                        if click_count == 0:
                            print("     더보기 버튼 없음")
                        else:
                            print(f"     더보기 버튼 없음 (총 {click_count}회 클릭)")
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

    def run_all_seoul(self):
        """서울시 전체 구 순회"""
        for district in SEOUL_DISTRICTS:
            # 구의 모든 동네 정보 수집
            dongs = self.get_district_dongs(district)
            if not dongs:
                continue

            # 각 동네별로 카테고리 순회
            for dong in dongs:
                for cat in categories:
                    self.process_category(dong, cat)

    def close(self):
        try:
            self.driver.quit()
        except:
            pass

crawler = KarrotCrawler()
try:
    crawler.run_all_seoul()
finally:
    crawler.close()
    print("\n🎉 서울시 전체 구×동네×카테고리 크롤링 완료!") 