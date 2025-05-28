import json, time
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

#한글 동 이름
import urllib.parse

# ─── 0) 세팅 ────────────────────────────────────────────
opts  = uc.ChromeOptions()
opts.add_argument('--no-sandbox')
opts.add_argument('--disable-dev-shm-usage')
driver = uc.Chrome(options=opts)
wait   = WebDriverWait(driver, 10)

# ─── 1) 시작 페이지 열기 ─────────────────────────────────
BASE_URL = "https://www.daangn.com/kr/buy-sell/?category_id=1&in=명지동-5873"
driver.get(BASE_URL)
time.sleep(2)

# ─── 2) 동네 리스트 전체 보이기 위해 '더보기' 클릭 ────────────
more_btn = wait.until(EC.element_to_be_clickable(
    (By.CSS_SELECTOR, 'button[data-gtm="search_show_more_options"]')
))
more_btn.click()
wait.until(EC.presence_of_all_elements_located(
    (By.CSS_SELECTOR, 'a[data-gtm="search_filter"]')
))

# ─── 3) 모든 동네 링크 추출 ───────────────────────────────
# '위치' h3 바로 아래 div에서만 추출
location_section = driver.find_element(By.XPATH, "//h3[text()='위치']/following-sibling::div[1]")
links = location_section.find_elements(By.CSS_SELECTOR, 'a[data-gtm="search_filter"]')

#퍼센트 인코딩으로 저장
# regions = []
# for a in links:
#     name = a.text.strip()
#     path = a.get_attribute("href").replace("https://www.daangn.com", "")
#     regions.append({"name": name, "url": path})

#한글출력
regions = []
for a in links:
    name = a.text.strip()
    path = a.get_attribute("href").replace("https://www.daangn.com", "")
    # 퍼센트 인코딩을 한글로 디코딩
    path = urllib.parse.unquote(path)
    regions.append({"name": name, "url": path})

# ─── 4) JSON 에 저장 ────────────────────────────────────
with open("regions_bu_gangseo.json", "w", encoding="utf-8") as f:
    json.dump(regions, f, ensure_ascii=False, indent=2)

print(f"✅ {len(regions)}개 동네 저장됨 → regions_bu_gangseo.json")
driver.quit()
