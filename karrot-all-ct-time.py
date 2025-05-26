import time, csv, json, os
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException

class KarrotCrawler:
    def __init__(self):
        options = uc.ChromeOptions()
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        self.driver = uc.Chrome(options=options)
        self.wait = WebDriverWait(self.driver, 10)
        
    def process_category(self, category_name, category_url):
        """카테고리별 처리"""
        safe_name = category_name.replace("/", "_").replace("\\", "_")
        fn = f"daangn_{safe_name}.csv"
        
        print(f"\n▶ [{category_name}] 크롤링 시작 → {fn}")
        
        try:
            # 전체 URL 구성 (categories.json에는 path만 저장됨)
            full_url = f"https://www.daangn.com{category_url}"
            self.driver.get(full_url)
            time.sleep(2)
            
            # 더보기 버튼 클릭 (최대 5회)
            more_click_count = 0
            while more_click_count < 5:
                try:
                    self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                    time.sleep(1)
                    btn = self.wait.until(EC.element_to_be_clickable(
                        (By.XPATH, "//button[contains(text(),'더보기')]")
                    ))
                    self.driver.execute_script("arguments[0].scrollIntoView({block:'center'});", btn)
                    btn.click()
                    more_click_count += 1
                    print(f"     더보기 클릭 ({more_click_count}/5회)")
                    time.sleep(1)
                except:
                    print(f"     더보기 버튼 없음 (총 {more_click_count}회 클릭)")
                    break
            
            # 상품 카드 찾기
            cards = self.driver.find_elements(By.CSS_SELECTOR, "a[data-gtm='search_article']")
            print(f"   ▶ [{category_name}] {len(cards)}개 상품 발견")
            
            # CSV 파일에 저장
            with open(fn, "w", newline="", encoding="utf-8-sig") as f:
                writer = csv.writer(f)
                writer.writerow(["카테고리","상품명","가격","작성일자","판매상태","URL"])
                
                for idx, card in enumerate(cards, 1):
                    try:
                        # 상품명
                        name = card.find_element(By.CSS_SELECTOR, "span.lm809sh").text.strip()
                        # 가격
                        price = card.find_element(By.CSS_SELECTOR, "span.lm809si").text.strip()
                        # 시간
                        time_text = card.find_element(By.TAG_NAME, "time").text.strip()
                        # 판매상태
                        try:
                            status = card.find_element(By.CSS_SELECTOR, "span.mlbp660").text.strip()
                        except NoSuchElementException:
                            status = "판매중"
                        
                        # CSV에 쓰기
                        writer.writerow([
                            category_name, name, price, time_text, status, 
                            card.get_attribute("href")
                        ])
                        f.flush()
                        print(f"     {idx}/{len(cards)} [{status}] {name}")
                        
                    except Exception as e:
                        print(f"     ⚠️ {idx}번째 상품 처리 실패: {str(e)}")
                        continue
            
            print(f"✅ [{category_name}] CSV 생성됨 → {os.path.abspath(fn)}")
            
        except Exception as e:
            print(f"⚠️ [{category_name}] 카테고리 처리 중 오류: {str(e)}")

    def close(self):
        self.driver.quit()

def main():
    with open("categories.json", "r", encoding="utf-8") as f:
        categories = json.load(f)
    crawler = KarrotCrawler()
    try:
        for cat in categories:
            crawler.process_category(cat["name"], cat["url"])
    finally:
        crawler.close()
        print("\n🎉 카테고리 순회 + 크롤링 완료!")

if __name__ == "__main__":
    main() 