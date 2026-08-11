import aiohttp
import asyncio
import json
from typing import Dict, Any, Optional
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.firefox.service import Service
import pickle
import os
import logging
import time
import logging
import tempfile
import os
logger = logging.getLogger("work-selenium")

class VKSessionManager:
    """Менеджер сессий VK с использованием Selenium для получения кук"""

    COOKIES_FILE = "vk_cookies.pkl"

    def __init__(self, headless: bool = False):
        self.headless = headless
        self.cookies: Dict[str, str] = {}
        self.driver = None

    def _setup_driver(self) -> webdriver.Firefox:
        """Настройка Firefox драйвера"""
        options = Options()

        if self.headless:
            options.add_argument('--headless')

        driver = webdriver.Firefox(options=options)
        return driver

    def check_registration_number_result(self, number:str) -> dict:
        result = {}
        result_checking = False
        not_founded = False
        driver = self._setup_driver()
        try:
            driver.get("https://id.vk.ru/restore/#/resetPassword")
            time.sleep(3)

            number_field =  driver.find_element(By.XPATH, "//input[@name='phone' and @type='tel']")
            number_field.clear()
            number_field.send_keys(number)
            number_check_button = driver.find_element(By.XPATH,"//button[@data-test-id='nextButton' and @type='button']")
            number_check_button.click()
            error_message = driver.find_element(By.XPATH,  "//div[contains(., 'Такого аккаунта нет') or contains(., 'No such account') or contains(., 'Account not found.')]")
            if error_message:
                result_checking = True
        except:
            not_founded=  True

        result["result_checking"] = result_checking
        result["not_founded"] = not_founded
        return result

    def check_registration_email_result(self, email:str) -> bool:

        result_checking = False
        driver = self._setup_driver()
        try:
            driver.get("https://id.vk.ru/restore/#/resetPassword")
            time.sleep(3)
            radiogroup = driver.find_element(By.XPATH, "//div[@role='radiogroup']")
            items = radiogroup.find_elements(By.XPATH, ".//label")

            for item in items:
               if item.text.lower() == "почта" or item.text.lower() == "email":
                 item.click()
                 break

            email_field = driver.find_element(By.XPATH, "//input[@type='text' and name='login' and placeholder='Почта'] or //input[@type='text' \
                and name='login' and placeholder='Email']")
            email_field.clear()
            email_field.send_keys(email)

            number_check_button = driver.find_element(By.XPATH,"//button[@data-test-id='nextButton' and @type='button']")
            number_check_button.click()
            error_message = driver.find_element(By.XPATH,  "//div[contains(., 'Такого аккаунта нет') or contains(., 'No such account') or contains(., 'Account not found.')]")
            if error_message:
                 result_checking = True
        except:
            pass

        return result_checking

    def get_browser_restore_session_id_and_cookies(self):

        driver = self._setup_driver()

        driver.get("https://id.vk.ru/restore/#/resetPassword")
        time.sleep(3)

        selenium_cookies = driver.get_cookies()

        cookies = {}
        for cookie in selenium_cookies:
            cookies[cookie['name']] = cookie['value']

        restore_session_id = driver.execute_script("""
                // 1. Проверяем глобальные переменные
                if (window.restore_session_id) return window.restore_session_id;
                if (window.restoreSessionId) return window.restoreSessionId;

                // 2. Проверяем localStorage
                try {
                    var id = localStorage.getItem('restore_session_id');
                    if (id) return id;
                } catch(e) {}

                // 3. Проверяем sessionStorage
                try {
                    var id = sessionStorage.getItem('restore_session_id');
                    if (id) return id;
                } catch(e) {}

                // 4. Ищем в переменных внутри скриптов
                var scripts = document.getElementsByTagName('script');
                for (var i = 0; i < scripts.length; i++) {
                    var text = scripts[i].textContent || scripts[i].innerText;
                    if (text) {
                        var match = text.match(/restore_session_id["'\\s:]+([^"'\\s,}]+)/);
                        if (match) return match[1];
                    }
                }
                return null;
            """)
        try:
            element = driver.find_element(By.XPATH, "//input[@name='restore_session_id']")
            restore_session_id = element.get_attribute("value")
        except:
            pass

        driver.quit()
        return  {

                'cookies': cookies,
                'restore_session_id': restore_session_id
            }
