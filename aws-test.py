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

import unittest, time, re

class AwsTest(unittest.TestCase):
    def setUp(self):
        self.driver = webdriver.Remote(
           command_executor='http://192.168.56.1:4444/wd/hub',
           desired_capabilities=DesiredCapabilities.CHROME)
	
        # self.driver = webdriver.Firefox()
        self.driver.implicitly_wait(10)
        self.base_url = "http://calculator.s3.amazonaws.com"
        self.verificationErrors = []
        self.accept_next_alert = True
	self.wait = WebDriverWait(self.driver, 20)

    def test_aws(self):
        driver = self.driver
        driver.get(self.base_url + "/index.html?lng=ja_JP#")
	# 無料利用枠チェック外す
	chkbox=driver.find_element_by_css_selector("#gwt-uid-2")
	if (chkbox.get_attribute('value') == 'on') : chkbox.click()
	# サービスタブ選択
        driver.find_element_by_css_selector("div.restLabel").click()
	# Tokyoリージョン選択
	region = driver.find_element_by_css_selector("select.CR_CHOOSE_REGION")
	Select(region).select_by_visible_text(u'アジアパシフィック（日本）')
	# EC2選択
	awsservices={}
	srvstabs=driver.find_elements_by_css_selector("div.tabPanel.servicesPanel > div.tabs > div.gwt-HTML.tab")
	for service in srvstabs:
		awsservices[service.text] = service
	awsservices['Amazon EC2'].click()

        # EC2インスタンス追加
	btn = btn=driver.find_element_by_css_selector("div.Instances tr.footer div.gwt-PushButton > img[src$='add.png']")
	ActionChains(self.driver).move_to_element(btn).click(btn).perform()
        # インスタンス説明
        driver.find_element_by_css_selector("div.Instances table>tbody>tr:nth-last-child(2)  table.SF_EC2_INSTANCE_FIELD_DESCRIPTION input").clear()
        driver.find_element_by_css_selector("div.Instances table>tbody>tr:nth-last-child(2)  table.SF_EC2_INSTANCE_FIELD_DESCRIPTION input").send_keys("server1")
        # インスタンス数
        driver.find_element_by_css_selector("div.Instances table>tbody>tr:nth-last-child(2)  table.SF_EC2_INSTANCE_FIELD_INSTANCES input").clear()
        driver.find_element_by_css_selector("div.Instances table>tbody>tr:nth-last-child(2)  table.SF_EC2_INSTANCE_FIELD_INSTANCES input").send_keys("2")
        # 使用量
        driver.find_element_by_css_selector("div.Instances table>tbody>tr:nth-last-child(2)  table.SF_EC2_INSTANCE_FIELD_USAGE input").clear()
        driver.find_element_by_css_selector("div.Instances table>tbody>tr:nth-last-child(2)  table.SF_EC2_INSTANCE_FIELD_USAGE input").send_keys("90")
        Select(driver.find_element_by_css_selector("div.Instances table>tbody>tr:nth-last-child(2)  table.SF_EC2_INSTANCE_FIELD_USAGE select")).select_by_visible_text(u"使用率/月")
        # タイプ
	btn=driver.find_element_by_css_selector("div.Instances table>tbody>tr:nth-last-child(2) > td:nth-child(5) div.gwt-PushButton > img.gwt-Image")
	ActionChains(driver).move_to_element(btn).click(btn).perform()
	self.wait.until( expected_conditions.presence_of_element_located((By.CSS_SELECTOR , 'table.Types > tbody > tr:nth-child(2)')) )
        # EBS最適化
        driver.find_element_by_css_selector("table.SF_EC2_INSTANCE_FIELD_EBS_OPTIMIZED input[type='checkbox']").click()
        # タイプ:OS
        lbls = driver.find_elements_by_css_selector("fieldset.SelectorDialogOS label")
	osset = {}
	for os in lbls:
		osset[os.text.strip()] = os
	osset[u'Windows および Web SQL Server'].click()
	# タイプ:Instance type
	itypes = driver.find_elements_by_css_selector('table.Types td:nth-child(2) div.gwt-Label')
        types = {}
	for i , itype in enumerate(itypes):
		types[itype.text.strip()] = str(i+2)

	driver.find_element_by_css_selector("table.Types > tbody > tr:nth-child(" + types['m4.4xlarge'] + ") > td label").click()
		
        # タイプ:詳細オプションを開く
	btn = driver.find_element_by_css_selector("table.InstanceTypeSelectorBody > tbody > tr:nth-child(3) > td > fieldset > table > tbody > tr > td:nth-child(1) > button")
	if ( btn.text == u'表示'): btn.click()
        # タイプ:詳細モニタリング
        driver.find_element_by_css_selector("table.SF_EC2_INSTANCE_FIELD_MONITORING input").click()
        # ハードウェア占有
        driver.find_element_by_css_selector("table.SF_EC2_INSTANCE_FIELD_TENANCY input").click()
        # 閉じて保存
	driver.find_element_by_css_selector('table.Buttons > tbody > tr > td:nth-child(3) > table > tbody > tr > td:nth-child(3) > button').click()
        # EBS
	btn=driver.find_element_by_css_selector("div.Volumes tr.footer div.gwt-PushButton > img[src$='add.png']")
	ActionChains(driver).move_to_element(btn).click(btn).perform()
        # EBS説明
        driver.find_element_by_css_selector("div.Volumes table>tbody>tr:nth-last-child(2)>td:nth-child(2) input").clear()
        driver.find_element_by_css_selector("div.Volumes table>tbody>tr:nth-last-child(2)>td:nth-child(2) input").send_keys("ebs-server1")
        # EBS:Volume数
        driver.find_element_by_css_selector("div.Volumes table>tbody>tr:nth-last-child(2)>td:nth-child(3) input").clear()
        driver.find_element_by_css_selector("div.Volumes table>tbody>tr:nth-last-child(2)>td:nth-child(3) input").send_keys("2")
        # EBS:Volumeタイプ
        Select(driver.find_element_by_css_selector("div.Volumes table>tbody>tr:nth-last-child(2) table.SF_EC2_EBS_FIELD_TYPE select")).select_by_visible_text(u"プロビジョンド IOPS（SSD）")
        # EBS:GB
        driver.find_element_by_css_selector("div.Volumes table>tbody>tr:nth-last-child(2) table.SF_EC2_EBS_FIELD_STORAGE input").clear()
        driver.find_element_by_css_selector("div.Volumes table>tbody>tr:nth-last-child(2) table.SF_EC2_EBS_FIELD_STORAGE input").send_keys("20")
        # EBS:IOPS
        driver.find_element_by_css_selector("div.Volumes table>tbody>tr:nth-last-child(2) table.SF_EC2_EBS_FIELD_AVERAGE_IOPS input").clear()
        driver.find_element_by_css_selector("div.Volumes table>tbody>tr:nth-last-child(2) table.SF_EC2_EBS_FIELD_AVERAGE_IOPS input").send_keys("200")
        # EBS:Snapshot
        driver.find_element_by_css_selector("div.Volumes table>tbody>tr:nth-last-child(2) table.SF_EC2_EBS_FIELD_SNAPSHOT_STORAGE input").clear()
        driver.find_element_by_css_selector("div.Volumes table>tbody>tr:nth-last-child(2) table.SF_EC2_EBS_FIELD_SNAPSHOT_STORAGE input").send_keys("200")
        Select(driver.find_element_by_css_selector("div.Volumes table>tbody>tr:nth-last-child(2) table.SF_EC2_EBS_FIELD_SNAPSHOT_STORAGE select")).select_by_visible_text(u"月次スナップショットの変化率")
        # ElasticIP:数
        driver.find_element_by_css_selector("table.SF_ELASTIC_IP_NUMBER input").clear()
        driver.find_element_by_css_selector("table.SF_ELASTIC_IP_NUMBER input").send_keys("1")
        # リージョン間データ転送送信
        driver.find_element_by_css_selector("table.dataTransferField:nth-child(1) input").clear()
        driver.find_element_by_css_selector("table.dataTransferField:nth-child(1) input").send_keys("123")
        # データ転送送信
        driver.find_element_by_css_selector("table.dataTransferField:nth-child(2) input").clear()
        driver.find_element_by_css_selector("table.dataTransferField:nth-child(2) input").send_keys("234")
        # ELB:数
        driver.find_element_by_css_selector("table.SF_ELB_DATA_NUMBER input").clear()
        driver.find_element_by_css_selector("table.SF_ELB_DATA_NUMBER input").send_keys("2")
        # ELB:データ転送量
        driver.find_element_by_css_selector("table.subSection:nth-child(5) div.subContent > table:nth-child(2) input").clear()
        driver.find_element_by_css_selector("table.subSection:nth-child(5) div.subContent > table:nth-child(2) input").send_keys("456")
        Select(driver.find_element_by_css_selector("table.subSection:nth-child(5) div.subContent > table:nth-child(2) select")).select_by_visible_text(u"GB/週")
        # お見積り
        driver.find_element_by_css_selector("div.billLabel").click()
        driver.find_element_by_css_selector("button.saveButton").click()
        driver.find_element_by_css_selector("input.SC_SOLUTION_Input").clear()
        driver.find_element_by_css_selector("input.SC_SOLUTION_Input").send_keys(u"ソリューションテスト100")
        driver.find_element_by_css_selector("textarea.SC_INCLUDES_Input").clear()
        driver.find_element_by_css_selector("textarea.SC_INCLUDES_Input").send_keys(u"含まれている1")
        driver.find_element_by_css_selector("textarea.SC_DESCRIPTION_Input").clear()
        driver.find_element_by_css_selector("textarea.SC_DESCRIPTION_Input").send_keys(u"概要説明1\n概要2")
        # waiting for save
	driver.find_element_by_css_selector("table.Buttons > tbody > tr > td > table > tbody > tr > td:nth-child(3) > button").click()
	estimate = self.wait.until( expected_conditions.presence_of_element_located((By.ID,'saveURL')))
	print estimate.text
	estimate.click()

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
