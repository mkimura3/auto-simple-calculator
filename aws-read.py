# -*- coding: utf-8 -*-
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

def pp(obj):
    if isinstance(obj, list) or isinstance(obj, dict):
        orig = json.dumps(obj, indent=4)
        print eval("u'''%s'''" % orig).encode('utf-8')
    else:
        print obj
 

ESTIMATE_URL='/index.html?lng=ja_JP#r=NRT&s=EC2&key=calc-FreeTier-NGC-140321'

class AwsTest(unittest.TestCase):
    def setUp(self):
        self.driver = webdriver.Remote(
        command_executor='http://192.168.56.1:4444/wd/hub',
        desired_capabilities=DesiredCapabilities.CHROME)

        self.driver.implicitly_wait(15)
        self.base_url = "http://calculator.s3.amazonaws.com"
        self.verificationErrors = []
        self.accept_next_alert = True
        self.wait = WebDriverWait(self.driver, 20)

    def test_aws_estimate(self):
        driver = self.driver
        driver.get(self.base_url + ESTIMATE_URL)
        # 詳細ボタン
        driver.find_element_by_css_selector("table.Buttons > tbody > tr > td:nth-child(3) > button").click()
        # 無料利用枠チェック外す
        self.disable_freetier() 
        # 見積もりを取得する
        bill=driver.find_element_by_css_selector("table.bill") 
        self.get_estimate(bill)


    def get_estimate(self,bill):
        def is_member(target , cname):
            return cname in target.get_attribute("class").split(" ")

        driver = self.driver
        # ちょっと待ってから[+]をクリックする
        time.sleep(5)
        btns = bill.find_elements_by_css_selector("tr.columnTreeRow.summary[aria-hidden=false] img[src$='tree-up.png']")
        for btn in btns: 
            btn.click()
        # 月額合計
        total = bill.find_element_by_css_selector('tr.total:not([aria-hidden]) table.value>tbody>tr>td:nth-child(2)>input').get_attribute('value')
        # 展開された見積もりを順に取得
        rows = bill.find_elements_by_css_selector("tr[aria-hidden=false]")
        estimate={
            'total' : total,
            'detail' : []
        }
        s={}
        for row in rows:
            if is_member(row,'summary') :
                if s : estimate['detail'].append(s)
                s={}
                # label
                s['name'] = row.find_element_by_css_selector('td:nth-child(2)>div.label').text
                # subTotal
                s['subTotal'] = row.find_element_by_css_selector('table.value>tbody>tr>td:nth-child(2)>input').get_attribute('value')
                s['items'] = []
            elif is_member(row,'field'):
                i = {}
                # sublabel
                i['name'] = row.find_element_by_css_selector('td:nth-child(1)>div.label').text
                # price
                i['price'] = row.find_element_by_css_selector('table.value>tbody>tr>td:nth-child(2)>input').get_attribute('value')
                s['items'].append(i)

        pp(estimate)
         

    def disable_freetier(self):
        # 無料利用枠チェック外す
        driver = self.driver
        chkbox=driver.find_element_by_css_selector("#gwt-uid-2")
        if (chkbox.get_attribute('value') == 'on') : chkbox.click()

    def is_element_present(self, how, what):
        try: self.driver.find_element(by=how, value=what)
        except NoSuchElementException, e: return False
        return True

    def is_alert_present(self):
        try: self.driver.switch_to_alert()
        except NoAlertPresentException, e: return False
        return True

    def close_alert_and_get_its_text(self):
        try:
            alert = self.driver.switch_to_alert()
            alert_text = alert.text
            if self.accept_next_alert:
                alert.accept()
            else:
                alert.dismiss()
            return alert_text
        finally: self.accept_next_alert = True

    def tearDown(self):
        self.driver.quit()
        self.assertEqual([], self.verificationErrors)

if __name__ == "__main__":
    unittest.main()

