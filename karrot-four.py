import json, os, csv, time
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException, TimeoutException
import urllib.parse
import re
from multiprocessing import Pool, cpu_count, Manager
import math
from datetime import datetime

# ─── 캐시된 JSON 읽기 ───────────────────────────────
# with open("regions_gangnam.json","r",encoding="utf-8") as f:
#     regions = json.load(f)
with open("regions_gangseo.json","r",encoding="utf-8") as f:
    regions = json.load(f)
with open("categories.json","r",encoding="utf-8") as f:
    categories = json.load(f)

# 처리된 동네 기록을 위한 파일
PROGRESS_FILE = "crawling_progress.json"

def load_progress():
    """이전에 처리된 동네 목록을 로드"""
    if os.path.exists(PROGRESS_FILE):
        with open(PROGRESS_FILE, 'r', encoding='utf-8') as f:
            return set(json.load(f))
    return set()

def save_progress(region_name):
    """처리된 동네를 기록"""
    processed = load_progress()
    processed.add(region_name)
    with open(PROGRESS_FILE, 'w', encoding='utf-8') as f:
        json.dump(list(processed), f, ensure_ascii=False, indent=2)

class KarrotCrawler:
    def __init__(self, process_id):
        self.process_id = process_id
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
        
        # 프로세스별 고유한 사용자 데이터 디렉토리 설정
        opts.add_argument(f'--user-data-dir=./chrome_data_{process_id}')
        
        # 드라이버 초기화 시도
        max_retries = 3
        for attempt in range(max_retries):
            try:
                # 기존 드라이버가 있다면 종료
                try:
                    self.driver.quit()
                except:
                    pass
                
                print(f"🔄 프로세스 {process_id}: Chrome 드라이버 초기화 시도 {attempt + 1}/{max_retries}")
                
                # 새로운 드라이버 생성
                self.driver = uc.Chrome(options=opts)
                self.wait = WebDriverWait(self.driver, 15)
                
                # 쿠키 및 캐시 삭제
                self.driver.delete_all_cookies()
                
                # 먼저 당근마켓 메인 페이지로 이동
                print(f"🌐 프로세스 {process_id}: 당근마켓 메인 페이지로 이동 시도...")
                self.driver.get("https://www.daangn.com")
                time.sleep(5)
                
                # 메인 페이지가 제대로 로드되었는지 확인
                try:
                    self.wait.until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, 'button[data-gtm="gnb_location"]'))
                    )
                    print(f"✅ 프로세스 {process_id}: 당근마켓 메인 페이지 로드 성공")
                    return
                        
                except Exception as e:
                    print(f"⚠️ 프로세스 {process_id}: 페이지 로드 실패: {str(e)}")
                    if attempt < max_retries - 1:
                        print(f"🔄 프로세스 {process_id}: 재시도...")
                        time.sleep(5)
                        continue
                    raise Exception("페이지 로드 실패")
                    
            except Exception as e:
                print(f"⚠️ 프로세스 {process_id}: 드라이버 초기화 실패 (시도 {attempt + 1}/{max_retries}): {str(e)}")
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
                print(f"⚠️ 프로세스 {self.process_id}: 페이지 로드 실패 (시도 {attempt + 1}/{max_retries}): {str(e)}")
                if attempt < max_retries - 1:
                    # 드라이버 재초기화 시도
                    try:
                        self.driver.quit()
                    except:
                        pass
                    time.sleep(5)
                    self.__init__(self.process_id)  # 드라이버 재초기화
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
        
        # 새로운 URL 형식으로 조합
        full_url = f"https://www.daangn.com/kr/buy-sell/?category_id={cat_id}&in={urllib.parse.quote(region_in)}"
        print(f"\n▶ 프로세스 {self.process_id}: [{region_name}][{cat['name']}] 크롤링 시작")
        
        # 안전하게 페이지 로드
        if not self.safe_get(full_url):
            print(f"⚠️ 프로세스 {self.process_id}: [{region_name}][{cat['name']}] 페이지 로드 실패, 다음으로 넘어갑니다.")
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
                        print(f"     프로세스 {self.process_id}: 더보기 클릭 ({more_click_count}/5)")
                        time.sleep(1)
                    except:
                        print(f"     프로세스 {self.process_id}: 더보기 버튼 없음 (총 {more_click_count}회 클릭)")
                        break

                # (3) 모든 상품 카드 수집
                cards = self.driver.find_elements(By.CSS_SELECTOR, 'a[data-gtm="search_article"]')
                print(f"   ▶ 프로세스 {self.process_id}: [{cat['name']}] {len(cards)}개 상품 발견")
                
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
                        print(f"     프로세스 {self.process_id}: {idx}/{len(cards)} [{status}] {name}")
                    except Exception as e:
                        print(f"     ⚠️ 프로세스 {self.process_id}: {idx}번째 상품 처리 실패: {str(e)}")
                        continue

                print(f"✅ 프로세스 {self.process_id}: [{region_name}][{cat['name']}] → {region_name}/{fn}")

            except Exception as e:
                print(f"⚠️ 프로세스 {self.process_id}: [{region_name}][{cat['name']}] 카테고리 처리 중 오류: {str(e)}")

    def close(self):
        self.driver.quit()

def process_region(args):
    """한 동네의 모든 카테고리를 처리하는 함수"""
    region, process_id = args
    region_name = region["name"]
    
    # 이미 처리된 동네인지 확인
    if region_name in load_progress():
        print(f"⏭️ 프로세스 {process_id}: {region_name}은(는) 이미 처리되었습니다. 건너뜁니다.")
        return
    
    print(f"\n🔄 프로세스 {process_id}: {region_name} 처리 시작 - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    crawler = KarrotCrawler(process_id)
    try:
        for cat in categories:
            crawler.process_category(region, cat)
        # 모든 카테고리 처리가 완료되면 진행상황 저장
        save_progress(region_name)
        print(f"✅ 프로세스 {process_id}: {region_name} 처리 완료 - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    except Exception as e:
        print(f"⚠️ 프로세스 {process_id}: {region_name} 처리 중 오류 발생: {str(e)}")
    finally:
        crawler.close()

if __name__ == '__main__':
    # 처리할 동네 목록 출력
    print(f"\n📋 처리할 동네 목록 ({len(regions)}개):")
    for region in regions:
        print(f"  - {region['name']}")
    
    # 이미 처리된 동네 확인
    processed = load_progress()
    if processed:
        print(f"\n⏭️ 이미 처리된 동네 ({len(processed)}개):")
        for name in processed:
            print(f"  - {name}")
    
    # 처리되지 않은 동네만 필터링
    regions_to_process = [r for r in regions if r["name"] not in processed]
    print(f"\n🔄 처리할 동네 수: {len(regions_to_process)}개")
    
    if not regions_to_process:
        print("\n✨ 모든 동네가 이미 처리되었습니다!")
        exit()
    
    # 각 프로세스에 고유 ID 부여
    process_args = [(region, i) for i, region in enumerate(regions_to_process)]
    
    # 병렬 처리
    num_processes = 4
    with Pool(num_processes) as pool:
        pool.map(process_region, process_args)
    
    print("\n🎉 모든 동네×카테고리 크롤링 완료!") 