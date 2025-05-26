from selenium.webdriver.common.by import By
import time, json, undetected_chromedriver as uc

def extract_categories():
    driver = uc.Chrome()
    try:
        # 아무 지역이나 상관없음 (카테고리 구조는 동일)
        driver.get("https://www.daangn.com/kr/buy-sell/?in=역삼동-6035")
        time.sleep(2)
        
        # 카테고리 추출
        cats = driver.find_elements(
            By.XPATH,
            "//h3[text()='카테고리']/following-sibling::div//a[@data-gtm='search_filter']"
        )
        
        # 카테고리 정보 구성
        categories = []
        for cat in cats:
            try:
                name = cat.find_element(By.TAG_NAME, "span").text.strip()
                url = cat.get_attribute("href")
                # 전체 URL에서 path 부분만 추출
                url = url[url.find("/kr/buy-sell/"):]
                categories.append({"name": name, "url": url})
            except:
                continue
                
        # JSON 저장
        with open("categories.json", "w", encoding="utf-8") as f:
            json.dump(categories, f, ensure_ascii=False, indent=2)
            
        print(f"✅ 카테고리 {len(categories)}개 추출 완료")
        print("📝 categories.json 생성됨")
        
    finally:
        driver.quit()

if __name__ == "__main__":
    extract_categories()