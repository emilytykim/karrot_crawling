from selenium.webdriver.common.by import By
import time, undetected_chromedriver as uc

driver = uc.Chrome()
driver.get("https://www.daangn.com/kr/buy-sell/?in=송도동-6543")
time.sleep(2)
cats = driver.find_elements(
    By.XPATH,
    "//h3[text()='카테고리']/following-sibling::div//a[@data-gtm='search_filter']"
)
print([a.find_element(By.TAG_NAME,"span").text for a in cats])
driver.quit()
