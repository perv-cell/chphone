from selenium import webdriver
from selenium.webdriver.common.by import By
import time

# Запуск Firefox через geckodriver (если драйвер в PATH)
driver = webdriver.Firefox()

# Открытие сайта

driver.get("https://id.vk.ru/restore/#/resetPassword")
time.sleep(5)

# Находим radiogroup
radiogroup = driver.find_element(By.XPATH, "//div[@role='radiogroup']")

# Находим все label внутри radiogroup
items = radiogroup.find_elements(By.XPATH, ".//label")

for item in items:
    if item.text.lower() == "почта" or item.text.lower() == "email":
        item.click()
        break

email_field = driver.find_element(By.XPATH, "//input[@type='text' and name='login' and placeholder='Почта'] or //input[@type='text' \
and name='login' and placeholder='Email']")
email_field.clear()
email_field.send_keys("email")

number_check_button = driver.find_element(By.XPATH,"//button[@data-test-id='nextButton' and @type='button']")
number_check_button.click()

try:
    error_message = driver.find_element(By.XPATH,  "//div[contains(., 'Такого аккаунта нет') or contains(., 'No such account') or contains(., 'Account not found.')]")
    if error_message:
        result_checking = True
except:
    pass

"Такого аккаунта нет"
time.sleep(5)
"""
try:
    error_message = driver.find_element(By.XPATH,  "//div[contains(., 'Такого аккаунта нет') or contains(., 'No such account') or contains(., 'Account not found.')]")
    if error_message:
        print("номер не зареган")
except:
    print("не удалось найти элемент ")
# Закрытие браузера"""
driver.quit()
