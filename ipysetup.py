from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import Select
from selenium.common.exceptions import NoSuchElementException
from selenium.common.exceptions import NoAlertPresentException
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support import expected_conditions
from selenium.webdriver.support.ui import WebDriverWait

import unittest, time, re, json
from time import sleep

ESTIMATE_URL='/index.html?lng=ja_JP#r=NRT&s=EC2&key=calc-FreeTier-NGC-140321'

driver = webdriver.Remote(
command_executor='http://192.168.56.1:4444/wd/hub',
desired_capabilities=DesiredCapabilities.CHROME)

#driver.implicitly_wait(15)
base_url = "http://calculator.s3.amazonaws.com"
wait = WebDriverWait(driver, 20)
driver.get(base_url + ESTIMATE_URL)


