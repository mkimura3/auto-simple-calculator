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

    def get_selectedText(self,select):
        return select.find_elements_by_tag_name('option')[ int(select.get_attribute('selectedIndex')) ].text

    def is_checked( self, css, driver=None ):
        if driver==None : driver=self.driver
        chk = driver.find_element_by_css_selector(css).get_attribute('checked')
        return chk == u'true' 

    def get_value( self, css, driver=None ):
        if driver==None : driver=self.driver
        return driver.find_element_by_css_selector(css).get_attribute('value')

    def get_text( self, css, driver=None ):
        if driver==None : driver=self.driver
        return driver.find_element_by_css_selector(css).text

    def get_element( self,css, driver=None ):
        if driver==None : driver=self.driver
        return driver.find_element_by_css_selector(css)

    def get_elements(self, css, driver=None):
        if driver==None : driver=self.driver
        return driver.find_elements_by_css_selector(css)

    def get_int_and_type(self, css, driver=None):
        if driver==None : driver=self.driver
        v = int(driver.find_element_by_css_selector(css + ' input').get_attribute('value'))
        s = driver.find_element_by_css_selector(css + ' select')
        t = self.get_selectedText(s)
        return (v,t)

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
        solution = self.get_element("table.SolutionShowBody")
        pp( self.get_solution(solution) )

        # 詳細ボタンを押す
        self.get_element("table.Buttons > tbody > tr > td:nth-child(3) > button").click()
        # 無料利用枠チェック外す
        self.disable_freetier()

        # 見積もりを取得する
        bill=self.get_element("table.bill") 
        pp ( self.get_estimate(bill) )

        # Serviceメニューの取得
        self.init_serviceMenu() 
       
        # EC2構成情報の取得
        self.select_service('Amazon EC2') 
        self.get_ec2Service()

    def init_serviceMenu(self):
        self.serviceTab = {}
        tabs = self.get_elements("div.servicesPanel > div.tabs > div.tab[aria-hidden=false]")
        for tab in tabs:
            self.serviceTab[ tab.text.strip() ] = tab

    def select_service(self, serviceName):
            self.serviceTab[serviceName].click()

    def get_solution(self,solution):
        sc_price_txt = self.get_text( "div.gwt-HTML.SC_Price", solution)
        # 金額
        sc_price = float(sc_price_txt.split(' ')[-1])
        # 名前
        sc_name = self.get_text("table.SC_SOLUTION_LINE div.SC_SOLUTION_DATA", solution)
        # 含まれるもの
        sc_include = self.get_text("table.DescriptiveDetails div.SC_INCLUDES_DATA", solution)
        # 説明
        sc_desc = self.get_text("table.DescriptiveDetails div.SC_DESCRIPTION_DATA", solution)

        return {
                'price' : sc_price,
                'name' : sc_name,
                'includes' : sc_include,
                'description' : sc_desc
            }

    def get_ec2Service(self):
        # Region一覧の取得
        listbox = self.get_element("select.gwt-ListBox.CR_CHOOSE_REGION.regionListBox")
        regions = self.get_elements("select.gwt-ListBox.CR_CHOOSE_REGION.regionListBox option")
        for region in regions :
            Select(listbox).select_by_visible_text(region.text)
            ec2tbl = self.get_element('table.service.EC2Service')
            print region.text, "----------------------"
            pp( self.get_ec2Service_region(ec2tbl) )
             
    def get_ec2Service_region(self,table):
        # waitを短く
        self.driver.implicitly_wait(1)
        instances = []
        ####
        # インスタンス
        rows = self.get_elements('div.Instances table.itemsTable tr.EC2InstanceRow.itemsTableDataRow', table)
        for row in rows:
            # インスタンス説明
            desc = self.get_value("table.SF_EC2_INSTANCE_FIELD_DESCRIPTION input", row)
            # インスタンス数
            quantity = int(self.get_value("table.SF_EC2_INSTANCE_FIELD_INSTANCES input", row))
            # 使用料
            usage_val = int(self.get_value("table.SF_EC2_INSTANCE_FIELD_USAGE input.numericTextBox", row))
            s = self.get_element("table.SF_EC2_INSTANCE_FIELD_USAGE select", row)
            usage_type=self.get_selectedText(s)
            # 料金計算オプション
            billing = self.get_text("div.SF_COMMON_FIELD_BILLING.instanceBillingField", row)
            # インスタンスタイプ設定を取得
            instance = self.get_instanceType(row)
            #
            instance.update( {
                    'description' : desc,
                    'quantity' : quantity,
                    'usageType' : usage_type,
                    'usageValue' : usage_val,
                    'billingOption' : billing
                })
            instances.append(instance)
        ####
        # EBS
        storages = []
        rows = self.get_elements("div.Volumes tr.EBSVolumeRow.itemsTableDataRow", table)
        for row in rows:
            # Volume 説明
            desc = self.get_value("tr td:nth-child(2) input.gwt-TextBox.input", row)
            # Volume 数
            quantity = int(self.get_value("tr td:nth-child(3) input.gwt-TextBox.input", row))
            # Volume サイズ
            size = int(self.get_value("tr td:nth-child(5) input.gwt-TextBox.input", row))
            # Volume IOPS
            iops = int(self.get_value("tr td:nth-child(6) input.gwt-TextBox.input", row))
            # Volume タイプ
            s = self.get_element("tr td:nth-child(4) select", row)
            ebs_type = self.get_selectedText(s)
            # Snapshot 
            s = self.get_element("tr td:nth-child(7) select", row)
            snap_type = self.get_selectedText(s)
            snap_size = float( self.get_value("tr td:nth-child(7) input.gwt-TextBox.numericTextBox",row) )
            storages.append({
                'description' : desc,
                'quantity' : quantity,
                'size' : size,
                'iops' : iops,
                'type' : ebs_type,
                'snapshotType' : snap_type,
                'snapshotSize' : snap_size
            })

        # Elastic IP
        # 追加 Elastic IP の数
        eip_quantity = int(self.get_value("table.SF_ELASTIC_IP_NUMBER input", table))
        # Elastic IP をアタッチしていない時間:
        eip_notime, eip_notype = self.get_int_and_type("table.SF_ELASTIC_IP_ATTACHED",table)
        # Elastic IP リマップの回数:
        eip_remap, eip_retype = self.get_int_and_type("table.SF_ELASTIC_IP_REMAPS",table)
        # データ転送
        # リージョン間データ転送送信:
        interr_data, interr_type = self.get_int_and_type("table.dataTransferField:nth-child(1)",table)
        # データ転送送信:
        internet_out, internet_out_type = self.get_int_and_type("table.dataTransferField:nth-child(2)", table)
        # データ転送受信:
        internet_in, internet_in_type = self.get_int_and_type("table.dataTransferField:nth-child(3)", table)
        # VPC ピア接続のデータ転送:
        vpcpeer_data, vpcpeer_data_type = self.get_int_and_type("table.dataTransferField:nth-child(4)", table)
        # リージョン内データ転送:
        intra_region, intra_region_type = self.get_int_and_type("table.dataTransferField:nth-child(5)", table)
        # パブリック IP/Elastic IP のデータ転送:
        eip_data, eip_data_type =  self.get_int_and_type("table.dataTransferField:nth-child(6)", table)
         
        # Elastic Load Balancing
        # Elastic LB の数:
        elb_quantity = int(self.get_value("table.SF_ELB_DATA_NUMBER input", table))
        # 全 ELB によって処理されたデータ総量:
        elb_total , elb_total_type = self.get_int_and_type("table.subSection:nth-child(5) div.subContent > table:nth-child(2)", table) 

        #wait秒数をもとに戻す
        self.driver.implicitly_wait(15)

        return {
            "instances" : instances,
            "storages"  : storages,
            "elasticIp" : {
                "quantity" : eip_quantity,
                "unAttached" : {
                    "value" : eip_notime, 
                    "type" : eip_notype
                }
            },
            "dataTranfer" : {
                "interRegion" : {
                    "value" : interr_data,
                    "type"  : interr_type
                },
                "intraRegion" : {
                    "value" : intra_region,
                    "type"  : intra_region_type
                },
                "internetSend" : {
                    "value" : internet_out,
                    "type"  : internet_out_type
                },
                "internetRecive" : {
                    "value" : internet_in,
                    "type"  : internet_in_type
                },
                "vpnPeers" : {
                    "value" : vpcpeer_data,
                    "type"  : vpcpeer_data_type
                },
                "intraRegionEipElb" : {
                    "value" : eip_data,
                    "type"  : eip_data_type
                }
            },
            "elasticLoadBalancing" : {
                "quantity" : elb_quantity,
                "elbTransfer" : {
                    "value" : elb_total,
                    "type"  : elb_total_type
                }
            }
        }
    

    def get_instanceType(self,row):
        #driver = self.driver
        #type_div = row.find_element_by_css_selector('div.SF_EC2_INSTANCE_FIELD_TYPE')
        type_div = self.get_element('div.SF_EC2_INSTANCE_FIELD_TYPE',row)
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
        instance_ebsopt = self.is_checked("table.SF_EC2_INSTANCE_FIELD_EBS_OPTIMIZED input[type='checkbox']")
        # 詳細モニタリング
        instance_monitor = self.is_checked("table.SF_EC2_INSTANCE_FIELD_MONITORING input[type='checkbox']")
        # ハードウェア占有
        instance_tenancy = self.is_checked("table.SF_EC2_INSTANCE_FIELD_TENANCY input[type='checkbox']")
        # ダイアログを閉じる
        self.get_element('table.Buttons > tbody > tr > td:nth-child(3) > table > tbody > tr > td:nth-child(3) > button').click()
        # 
        return {
                'os': instance_os,
                'type' : instance_type,
                'ebsOptimized' : instance_ebsopt,
                'detailedMonitor' : instance_monitor,
                'dedicated' : instance_tenancy
            }
         
    def get_estimate(self,bill):
        def is_member(target , cname):
            return cname in target.get_attribute("class").split(" ")

        driver = self.driver
        # ちょっと待ってから[+]をクリックする
        time.sleep(5)
        btns = self.get_elements("tr.columnTreeRow.summary[aria-hidden=false] img[src$='tree-up.png']", bill)
        for btn in btns: 
            btn.click()
        # 月額合計
        total = float(self.get_value('tr.total:not([aria-hidden]) table.value>tbody>tr>td:nth-child(2)>input',bill))
        # 展開された見積もりを順に取得
        rows = self.get_elements("tr[aria-hidden=false]",bill)
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
                s['name'] = self.get_text('td:nth-child(2)>div.label', row)
                # subTotal
                s['subTotal'] = float(self.get_value('table.value>tbody>tr>td:nth-child(2)>input', row))
                s['items'] = []
            elif is_member(row,'field'):
                i = {}
                # sublabel
                i['name'] = self.get_text('td:nth-child(1)>div.label', row)
                # price
                i['price'] = float(self.get_value('table.value>tbody>tr>td:nth-child(2)>input',row))
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
        chkbox=self.get_element("#gwt-uid-2")
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

