import aiohttp
import asyncio
import json
from typing import Dict, Any, Optional
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.firefox import firefox_profile
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
from schemas.object_search import Protocol, get_version_protocol
import random

logger = logging.getLogger("work-selenium")

class VKSessionManager:
    """Менеджер сессий VK с использованием Selenium для получения кук"""

    COOKIES_FILE = "vk_cookies.pkl"

    def __init__(self, headless: bool = False,  proxys:  Dict[str, Dict]= {}):
        self.proxys = proxys
        self.headless = headless
        self.cookies: Dict[str, str] = {}
        self.driver = None

    def _setup_driver(self) -> webdriver.Firefox:
        """Настройка Firefox драйвера"""
        options = Options()
        profile = webdriver.FirefoxProfile()

        if self.headless:
            options.add_argument('--headless')

        if self.proxys:
            idx = random.randint(0, len(self.proxys)-1)
            random_key = list(self.proxys.keys())[idx]
            best_proxy =  self.proxys[random_key]
            for proxy_info in self.proxys.values():
                if proxy_info.get("count_of_calls",0) < best_proxy.get("count_of_calls",0):
                    best_proxy = proxy_info
            if best_proxy:
                best_proxy["count_of_calls"]+=1
            PROXY_HOST = best_proxy.get("hostname")
            PROXY_PORT = best_proxy.get("port")
            PROXY_PROTOCOL:Optional[Protocol] = best_proxy.get("protocol")

            if  not PROXY_HOST is None and not PROXY_PORT is None and not PROXY_PROTOCOL is None:

                VERSION_PROTOCOL = get_version_protocol(PROXY_PROTOCOL)
                profile = webdriver.FirefoxProfile()
                profile.set_preference('network.proxy.type', 1)
                profile.set_preference('network.proxy.socks', PROXY_HOST)
                profile.set_preference('network.proxy.socks_port', PROXY_PORT)
                profile.set_preference('network.proxy.socks_version', VERSION_PROTOCOL)
                profile.set_preference('network.proxy.socks_remote_dns', True)
                profile.update_preferences()


                #options.profile = profile
            logger.info(f"Осуществляется поиск от след проки {PROXY_HOST}:{PROXY_PORT} {VERSION_PROTOCOL}")
        driver = webdriver.Firefox(options=options)
        return driver

    def check_registration_number_result(self, number: str) -> dict:
        result = {}
        registration = False
        not_defined = False
        driver = self._setup_driver()
        try:
            driver.get("https://id.vk.ru/restore/#/resetPassword")
            time.sleep(3)

            number_field = driver.find_element(By.XPATH, "//input[@name='phone' and @type='tel']")
            number_field.clear()
            time.sleep(1)
            number_field.send_keys(number)

            number_check_button = driver.find_element(By.XPATH, "//button[@data-test-id='nextButton' and @type='button']")
            number_check_button.click()

            wait = WebDriverWait(driver, 10)

            try:
                error_message = wait.until(
                    EC.presence_of_element_located(
                        (By.XPATH, "//div[contains(., 'Такого аккаунта нет') or contains(., 'No such account') or contains(., 'Account not found.')]")
                    )
                )
                registration = False
            except:
                registration = True

        except Exception as e:
            logger.error(str(e))
            not_defined = True
            registration = False
        finally:
            driver.quit()

        result["registration"] = registration
        result["not_defined"] = not_defined
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
            time.sleep(1)
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
