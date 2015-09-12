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
        # 概要の取得
        solution = driver.find_element_by_css_selector("table.SolutionShowBody")
        pp( self.get_solution(solution) )

        # 詳細ボタンを押す
        driver.find_element_by_css_selector("table.Buttons > tbody > tr > td:nth-child(3) > button").click()
        # 無料利用枠チェック外す
        self.disable_freetier()

        # 見積もりを取得する
        bill=driver.find_element_by_css_selector("table.bill") 
        pp ( self.get_estimate(bill) )

        # Serviceメニューの取得
        self.init_serviceMenu() 
       
        # EC2構成情報の取得
        self.select_service('Amazon EC2') 
        ec2tbl = driver.find_element_by_css_selector('table.service.EC2Service')
        self.get_ec2Service(ec2tbl)


    def init_serviceMenu(self):
        self.serviceTab = {}
        tabs = self.driver.find_elements_by_css_selector("div.servicesPanel > div.tabs > div.tab[aria-hidden=false]")
        for tab in tabs:
            self.serviceTab[ tab.text.strip() ] = tab

    def select_service(self, serviceName):
            self.serviceTab[serviceName].click()

    def get_solution(self,solution):
        sc_price_txt = solution.find_element_by_css_selector("div.gwt-HTML.SC_Price").text
        # 金額
        sc_price = float(sc_price_txt.split(' ')[-1])
        # 名前
        sc_name = solution.find_element_by_css_selector("table.SC_SOLUTION_LINE div.SC_SOLUTION_DATA").text
        # 含まれるもの
        sc_include = solution.find_element_by_css_selector("table.DescriptiveDetails div.SC_INCLUDES_DATA").text
        # 説明
        sc_desc = solution.find_element_by_css_selector("table.DescriptiveDetails div.SC_DESCRIPTION_DATA").text
        return {
                'price' : sc_price,
                'name' : sc_name,
                'includes' : sc_include,
                'description' : sc_desc
            }

    def get_ec2Service(self,table):
        # EC2タブの選択
        # インスタンス行取得
        rows = table.find_elements_by_css_selector('div.Instances table.itemsTable tr.EC2InstanceRow.itemsTableDataRow')
        for row in rows:
            # インスタンス説明
            desc = row.find_element_by_css_selector("table.SF_EC2_INSTANCE_FIELD_DESCRIPTION input").get_attribute('value')
            # インスタンス数
            instances = int(row.find_element_by_css_selector("table.SF_EC2_INSTANCE_FIELD_INSTANCES input").get_attribute('value'))
            # 使用料
            usage_val = int(row.find_element_by_css_selector("table.SF_EC2_INSTANCE_FIELD_USAGE input.numericTextBox").get_attribute('value'))
            s = row.find_element_by_css_selector("table.SF_EC2_INSTANCE_FIELD_USAGE select")
            usage_type=s.find_elements_by_tag_name('option')[ int(s.get_attribute('selectedIndex')) ].text
            # 選択されている設定を取得
            pp(self.get_instanceType(row))
            # 料金計算オプション


    def get_instanceType(self,row):
        driver = self.driver
        type_div = row.find_element_by_css_selector('div.SF_EC2_INSTANCE_FIELD_TYPE')
        tlines = type_div.text.splitlines()
        # OS
        instance_os = tlines[0].split(u'、')[0].strip()
        # インスタンスタイプ
        instance_type = tlines[0].split(u'、')[1].strip()
        # インスタンスタイプを開く
        type_div.click()
        # タイプリストが展開されるまで待つ
        self.wait.until( expected_conditions.presence_of_element_located((By.CSS_SELECTOR , 'table.Types > tbody > tr:nth-child(2)')) )
        # EBS最適化
        optstr = driver.find_element_by_css_selector("table.SF_EC2_INSTANCE_FIELD_EBS_OPTIMIZED input[type='checkbox']").get_attribute('checked')
        instance_ebsopt = True if optstr==u'true' else False
        # 詳細モニタリング
        monstr = driver.find_element_by_css_selector("table.SF_EC2_INSTANCE_FIELD_MONITORING input[type='checkbox']").get_attribute('checked')
        instance_monitor = True if monstr==u'true' else False
        # ハードウェア占有
        tenastr = driver.find_element_by_css_selector("table.SF_EC2_INSTANCE_FIELD_TENANCY input[type='checkbox']").get_attribute('checked')
        instance_tenancy = True if tenastr==u'true' else False
        # ダイアログを閉じる
        driver.find_element_by_css_selector('table.Buttons > tbody > tr > td:nth-child(3) > table > tbody > tr > td:nth-child(3) > button').click()
        # 
        return {
                'os': instance_os,
                'type' : instance_type,
                'ebs_optimized' : instance_ebsopt,
                'detailed_monitor' : instance_monitor,
                'dedicated' : instance_tenancy
            }
         
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
        total = float(bill.find_element_by_css_selector('tr.total:not([aria-hidden]) table.value>tbody>tr>td:nth-child(2)>input').get_attribute('value'))
        # 展開された見積もりを順に取得
        rows = bill.find_elements_by_css_selector("tr[aria-hidden=false]")
        estimate={
            'total' : total,
            'detail' : []
        }
        s={}
        for row in rows:
            if is_member(row,'summary') :
                if s : 
                    estimate['detail'].append(s)
                s={}
                # label
                s['name'] = row.find_element_by_css_selector('td:nth-child(2)>div.label').text
                # subTotal
                s['subTotal'] = float(row.find_element_by_css_selector('table.value>tbody>tr>td:nth-child(2)>input').get_attribute('value'))
                s['items'] = []
            elif is_member(row,'field'):
                i = {}
                # sublabel
                i['name'] = row.find_element_by_css_selector('td:nth-child(1)>div.label').text
                # price
                i['price'] = float(row.find_element_by_css_selector('table.value>tbody>tr>td:nth-child(2)>input').get_attribute('value'))
                s['items'].append(i)
        # 見積もり合計値のチェック
        self.check_estimate(estimate)
        return estimate

    def check_estimate(self, estimate):
        # subTotalの合計が月額合計と等しいか
        assert round(estimate['total'],2)== round(sum([ a['subTotal'] for a in estimate['detail'] ] ),2)

        #各subTotalが項目合計と等しいか
        for field in estimate['detail']:
            print field['name'], field['subTotal']  
            assert round(field['subTotal'],2) == round(sum([ a['price']  for a in field['items'] ]),2)
                

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

