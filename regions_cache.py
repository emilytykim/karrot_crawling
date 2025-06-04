import json, time
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchWindowException, TimeoutException
import urllib.parse
import random
import argparse

def create_chrome_options():
    opts = uc.ChromeOptions()
    
    # 기본 설정
    opts.add_argument('--no-sandbox')
    opts.add_argument('--disable-dev-shm-usage')
    opts.add_argument('--disable-gpu')
    opts.add_argument('--disable-extensions')
    opts.add_argument('--disable-popup-blocking')
    opts.add_argument('--start-maximized')
    opts.add_argument('--disable-blink-features=AutomationControlled')
    opts.add_argument('--disable-notifications')
    opts.add_argument('--disable-infobars')
    opts.add_argument('--disable-web-security')
    opts.add_argument('--disable-features=IsolateOrigins,site-per-process')
    opts.add_argument('--window-size=1920,1080')
    
    # 랜덤 User-Agent 설정
    user_agents = [
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Safari/537.36',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Safari/537.36',
        'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Safari/537.36'
    ]
    opts.add_argument(f'--user-agent={random.choice(user_agents)}')
    
    return opts

def wait_random(min_seconds=5, max_seconds=10):
    wait_time = random.uniform(min_seconds, max_seconds)
    print(f"⏳ {wait_time:.1f}초 대기 중...")
    time.sleep(wait_time)

def main():
    # 명령줄 인자 파서 설정
    parser = argparse.ArgumentParser(description='당근마켓 지역 정보 수집기')
    parser.add_argument('--region', type=str, required=True, help='수집할 지역명 (예: bundang)')
    parser.add_argument('--url', type=str, required=True, help='당근마켓 지역 URL (예: https://www.daangn.com/kr/buy-sell/?category_id=1&in=서현동-4502)')
    args = parser.parse_args()

    max_retries = 3
    retry_count = 0

    while retry_count < max_retries:
        driver = None
        try:
            print(f"\n🔄 시도 {retry_count + 1}/{max_retries} 시작...")
            
            # 매 시도마다 새로운 ChromeOptions 생성
            opts = create_chrome_options()
            
            # 브라우저 초기화
            print("🌐 브라우저 초기화 중...")
            driver = uc.Chrome(options=opts, version_main=137)
            wait = WebDriverWait(driver, 30)

            # 시작 페이지 열기
            print("🌐 페이지 로드 중...")
            driver.get(args.url)
            wait_random(10, 15)
            
            # ─── 2) 동네 리스트 전체 보이기 위해 '더보기' 클릭 ────────────
            try:
                print("🔍 '더보기' 버튼 찾는 중...")
                more_btn = wait.until(EC.element_to_be_clickable(
                    (By.CSS_SELECTOR, 'button[data-gtm="search_show_more_options"]')
                ))
                wait_random(5, 8)
                print("🖱️ '더보기' 버튼 클릭...")
                more_btn.click()
                wait_random(5, 8)
                
                print("🔍 동네 목록 로딩 중...")
                wait.until(EC.presence_of_all_elements_located(
                    (By.CSS_SELECTOR, 'a[data-gtm="search_filter"]')
                ))

                # ─── 3) 모든 동네 링크 추출 ───────────────────────────────
                print("📝 동네 정보 수집 중...")
                location_section = driver.find_element(By.XPATH, "//h3[text()='위치']/following-sibling::div[1]")
                links = location_section.find_elements(By.CSS_SELECTOR, 'a[data-gtm="search_filter"]')

                regions = []
                for a in links:
                    name = a.text.strip()
                    path = a.get_attribute("href").replace("https://www.daangn.com", "")
                    path = urllib.parse.unquote(path)
                    regions.append({"name": name, "url": path})

                # ─── 4) JSON 에 저장 ────────────────────────────────────
                output_file = f"regions/regions_{args.region}.json"
                with open(output_file, "w", encoding="utf-8") as f:
                    json.dump(regions, f, ensure_ascii=False, indent=2)

                print(f"✅ {len(regions)}개 동네 저장됨 → {output_file}")
                break

            except (NoSuchWindowException, TimeoutException) as e:
                print(f"❌ 브라우저 오류: {str(e)}")
                retry_count += 1
                continue

        except Exception as e:
            print(f"❌ 치명적인 오류: {str(e)}")
            retry_count += 1
            continue

        finally:
            if driver:
                try:
                    print("🔒 브라우저 종료 중...")
                    driver.quit()
                except:
                    pass
            wait_random(3, 5)

    if retry_count == max_retries:
        print("\n❌ 최대 재시도 횟수를 초과했습니다. 스크립트를 종료합니다.")

if __name__ == "__main__":
    main()
