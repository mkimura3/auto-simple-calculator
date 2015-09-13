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
ESTIMATE_URL='/index.html?lng=ja_JP#r=NRT&s=EC2&key=calc-7DBA9B32-1A4C-4829-AD7C-AE102ED1F10F'

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

    def get_val_and_type(self, css, driver=None):
        if driver==None : driver=self.driver
        # input
        i = driver.find_element_by_css_selector(css + ' input')
        if self.is_member(i, 'integerNumericField') : 
            v = int(i.get_attribute('value'))
        elif self.is_member(i, 'NumericField') or self.is_member(i, 'numericTextBox'):
            v = float(i.get_attribute('value'))
        else:
            v = i.get_attribute('value')
        # select
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
        # self.disable_freetier()
        # Serviceメニューの取得
        self.init_serviceMenu() 

        # 見積もりを取得する
        bill=self.get_element("table.bill") 
        estimate = self.get_estimate(bill)
        pp(estimate)
        # Regionリストの取得
        self.init_regionList()
        
        # 見積もり項目ごとに構成を取得する
        for srvc in estimate['detail']:
            m = re.match(u'^(.*)Service（(.*)）.*', srvc['name'])
            if m  :
                print m.group(0)
                sconf = self.get_awsService( m.group(1).strip() , m.group(2).strip() ) 
                pp(sconf)



    def init_serviceMenu(self):
        self.serviceTab = {}
        tabs = self.get_elements("div.servicesPanel > div.tabs > div.tab[aria-hidden=false]")
        for tab in tabs:
            self.serviceTab[ tab.text.strip() ] = tab
    
    def init_regionList(self):
        self.select_service(u'Amazon EC2')
        self.regionList = []
        # Region一覧の取得
        regions = self.get_elements("select.gwt-ListBox.CR_CHOOSE_REGION.regionListBox option")
        for region in regions :
            self.regionList.append(region.text.strip())

    def select_service(self, serviceName):
            self.serviceTab[serviceName].click()
    
    def select_region(self, region_text):
        listbox = self.get_element("select.gwt-ListBox.CR_CHOOSE_REGION.regionListBox")
        Select(listbox).select_by_visible_text(region_text)

    def get_solution(self,solution):
        sc_price_txt = self.get_text( "div.gwt-HTML.SC_Price", solution)
        # 金額 (正しい金額ではないので保存しない)
        # sc_price = float(sc_price_txt.split(' ')[-1])
        # 名前
        sc_name = self.get_text("table.SC_SOLUTION_LINE div.SC_SOLUTION_DATA", solution)
        # 含まれるもの
        sc_include = self.get_text("table.DescriptiveDetails div.SC_INCLUDES_DATA", solution)
        # 説明
        sc_desc = self.get_text("table.DescriptiveDetails div.SC_DESCRIPTION_DATA", solution)

        return {
            'name' : sc_name,
            'includes' : sc_include,
            'description' : sc_desc
        }

    def get_awsService(self, service_name, region_name):
        # 見積もりRegion名から、Regionプルダウンを特定
        region_text = ''
        for k in self.regionList:
            if ( k.find(region_name) >=0 ) : 
                region_text = k 
                break
        # TODO: regionエラー処理
        
        # EC2構成情報の取得
        if ( service_name == 'Amazon EC2' ): 
            # print service_name, region_text
            self.select_service(u'Amazon EC2')
            self.select_region(region_text)
            return self.get_ec2Service()
        # S3構成情報の取得
        elif ( service_name == 'Amazon S3' ):
            self.select_service(u'Amazon S3')
            self.select_region(region_text)
            return self.get_s3Service()
        # RDS構成情報の取得
        elif ( service_name == 'Amazon RDS' ):
            self.select_service(u'Amazon RDS')
            self.select_region(region_text)
            return self.get_rdsService()

   
    # -------------------- RDS ----------------------
    def get_rdsService(self):
        table = self.get_element('table.service.RDSService')
        # waitを短く
        self.driver.implicitly_wait(1)  
        ####
        # インスタンス
        instances = []
        rows = self.get_elements('div.Instances table.itemsTable tr.RDSOnDemandRow.itemsTableDataRow', table)
        for row in rows:
            # インスタンス説明
            desc = self.get_value("table.SF_RDS_INSTANCE_FIELD_DESCRIPTION input", row)
            # インスタンス数
            quantity = int(self.get_value("table.SF_RDS_INSTANCE_FIELD_INSTANCES input", row))
            # 使用量
            usage_val = int(self.get_value("table.SF_RDS_INSTANCE_FIELD_USAGE input.numericTextBox", row))
            s = self.get_element("table.SF_RDS_INSTANCE_FIELD_USAGE select", row)
            usage_type=self.get_selectedText(s)
            # DB エンジンおよびライセンス
            engine = self.get_selectedText( self.get_element('table.SF_RDS_INSTANCE_FIELD_ENGINE select', row))
            # インスタンスタイプ
            instance_type = self.get_selectedText( self.get_element('table.SF_RDS_INSTANCE_FIELD_CLASS select', row))
            deploy_type = self.get_selectedText( self.get_element('table.SF_RDS_INSTANCE_FIELD_DEPLOYMENT_TYPE select', row))
            # ストレージ
            storage_type = self.get_selectedText( self.get_element('table.SF_RDS_INSTANCE_FIELD_IOPS_TYPE select' , row))
            storage_size = int(self.get_value('table.SF_RDS_INSTANCE_FIELD_STORAGE input.numericTextBox', row ))
            # IOPS
            iops = int(self.get_value('table.SF_RDS_INSTANCE_FIELD_IOPS input.numericTextBox', row ))

            instance= {
                'description' : desc,
                'quantity' : quantity,
                'usageType' : usage_type,
                'usageValue' : usage_val,
                'engine' : engine,
                'type' : instance_type,
                'deployment' : deploy_type,
                'storage' : {
                    'type' : storage_type,
                    'size' : storage_size,
                    'iops' : iops
                }
            }
            instances.append(instance)
        # 追加のバックアップストレージ 
        volumes = []
        rows = self.get_elements('div.Volumes table.itemsTable tr.RDSBackupRow.itemsTableDataRow', table)
        for row in rows:
            backup_size , backup_type = self.get_val_and_type('table.SF_RDS_FIELD_BACKUP', row )
            volumes.append({
                'size' : backup_size,
                'unit' :  backup_type
            })

        # リザーブドインスタンス
        rinstances = []
        rows = self.get_elements('div.RDBReserved table.itemsTable tr.RDSReservedRow.itemsTableDataRow', table)
        for row in rows:
            # インスタンス説明
            desc = self.get_value("table.SF_RDS_INSTANCE_FIELD_DESCRIPTION input", row)
            # インスタンス数
            quantity = int(self.get_value("table.SF_RDS_INSTANCE_FIELD_INSTANCES input", row))
            # 使用量
            usage_val, usage_type  = self.get_val_and_type("table.SF_RDS_INSTANCE_FIELD_USAGE", row)
            # DB エンジンおよびライセンス
            engine = self.get_selectedText( self.get_element('table.SF_RDS_INSTANCE_FIELD_ENGINE select', row))
            # インスタンスタイプ
            instance_type = self.get_selectedText( self.get_element('table.SF_RDS_INSTANCE_FIELD_CLASS select', row ))
            deploy_type = self.get_selectedText( self.get_element('table.SF_RDS_INSTANCE_FIELD_DEPLOYMENT_TYPE select', row))
            # Offering and Term 
            offering_type = self.get_selectedText( self.get_element('table.SF_RDS_RESERVED_FIELD_PAYMENT_OPTION select', row))
            offering_term = self.get_selectedText( self.get_element('table.SF_RDS_RESERVED_FIELD_TERM select', row ))
            # ストレージ
            storage_type = self.get_selectedText( self.get_element('table.SF_RDS_INSTANCE_FIELD_IOPS_TYPE select', row ))
            storage_size = int(self.get_value('table.SF_RDS_INSTANCE_FIELD_STORAGE input.numericTextBox', row ))
            # IOPS
            iops = int(self.get_value('table.SF_RDS_INSTANCE_FIELD_IOPS input.numericTextBox', row ))

            rinstance= {
                'description' : desc,
                'quantity' : quantity,
                'usageType' : usage_type,
                'usageValue' : usage_val,
                'engine' : engine,
                'type' : instance_type,
                'deployment' : deploy_type,
                'storage' : {
                    'type' : storage_type,
                    'size' : storage_size,
                    'iops' : iops
                },
                'offeringType' : offering_type,
                'offeringTerm' : offering_term
            }
            rinstances.append(rinstance)

        return {
            'instances' : instances,
            'backupVolumes' : volumes,
            'reservedInstances' : rinstances
        }

    # --------------------- S3 ----------------------
    def get_s3Service(self):
        table = self.get_element('table.service.S3Service')
        #ストレージ:
        # 通常ストレージ
        s3_size ,s3_size_unit = self.get_val_and_type("table.SF_S3_STORAGE", table)
        # 低冗長ストレージ
        rr_size ,rr_size_unit = self.get_val_and_type("table.SF_S3_RR_STORAGE", table)
        # リクエスト
        # PUT/COPY/POST/LIST リクエスト
        req_put = int(self.get_value("table.SF_S3_PUT_COPY_POST_LIST_REQUESTS input", table))
        # GET とその他のリクエスト 
        req_get =int(self.get_value("table.SF_S3_GET_OTHER_REQUESTS input", table))
        # データ転送:
        # リージョン間データ転送送信:
        inter_region , inter_region_type = self.get_val_and_type("table.subSection:nth-child(3) div.subContent > table:nth-child(1)", table)
        # データ転送送信:
        internet_out , internet_out_type = self.get_val_and_type("table.subSection:nth-child(3) div.subContent > table:nth-child(2)", table)
        # データ転送受信:
        internet_in , internet_in_type = self.get_val_and_type("table.subSection:nth-child(3) div.subContent > table:nth-child(3)", table)

        return {
            'standardStorage': {
                'size' : s3_size,
                'unit' : s3_size_unit
            },
            'reducedRedundancy': {
                'size' : rr_size,
                'unit' : rr_size_unit
            },
            'putCopyPostListRequests' : req_put,
            'getOtherRequests' : req_get,
            "interRegion" : {
                "value" : inter_region,
                "type"  : inter_region_type
            },
            "internetSend" : {
                "value" : internet_out,
                "type"  : internet_out_type
            },
            "internetRecive" : {
                "value" : internet_in,
                "type"  : internet_in_type
            }
        }

    # --------------------- EC2 ----------------------
    def get_ec2Service(self):
        table = self.get_element('table.service.EC2Service')
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
        eip_notime, eip_notype = self.get_val_and_type("table.SF_ELASTIC_IP_ATTACHED",table)
        # Elastic IP リマップの回数:
        eip_remap, eip_retype = self.get_val_and_type("table.SF_ELASTIC_IP_REMAPS",table)
        # データ転送
        # リージョン間データ転送送信:
        interr_data, interr_type = self.get_val_and_type("table.dataTransferField:nth-child(1)",table)
        # データ転送送信:
        internet_out, internet_out_type = self.get_val_and_type("table.dataTransferField:nth-child(2)", table)
        # データ転送受信:
        internet_in, internet_in_type = self.get_val_and_type("table.dataTransferField:nth-child(3)", table)
        # VPC ピア接続のデータ転送:
        vpcpeer_data, vpcpeer_data_type = self.get_val_and_type("table.dataTransferField:nth-child(4)", table)
        # リージョン内データ転送:
        intra_region, intra_region_type = self.get_val_and_type("table.dataTransferField:nth-child(5)", table)
        # パブリック IP/Elastic IP のデータ転送:
        eip_data, eip_data_type =  self.get_val_and_type("table.dataTransferField:nth-child(6)", table)
         
        # Elastic Load Balancing
        # Elastic LB の数:
        elb_quantity = int(self.get_value("table.SF_ELB_DATA_NUMBER input", table))
        # 全 ELB によって処理されたデータ総量:
        elb_total , elb_total_type = self.get_val_and_type("table.subSection:nth-child(5) div.subContent > table:nth-child(2)", table) 

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
         
    def is_member(self, target , cname):
        return cname in target.get_attribute("class").split(" ")

    def get_estimate(self,bill):
        # ちょっと待ってから[+]をクリックする TODO:料金表示のtab部分の変化をトリガーとする
        time.sleep(4)
        btns = self.get_elements("tr.columnTreeRow.summary[aria-hidden=false] img[src$='tree-up.png']", bill)
        for btn in btns: 
            btn.click()

        # 月額合計
        total_items =[] 
        total = float(self.get_value('tr.total:not([aria-hidden]) table.value>tbody>tr>td:nth-child(2)>input',bill))
        total_items.append({
            'name' : self.get_text('tr.total:not([aria-hidden])>td:nth-child(1)>div.gwt-HTML.label'),
            'price' : total
        })
        # サポートやリザーブ分を足す
        totals = self.get_elements('tr.total[aria-hidden=false]',bill)
        for t in totals:
            #print self.get_text('tr>td>div.gwt-HTML.label',t), self.get_value('table.value>tbody>tr>td:nth-child(2)>input',t)
            v = float(self.get_value('table.value>tbody>tr>td:nth-child(2)>input',t))
            total_items.append({
                'name' : self.get_text('tr>td>div.gwt-HTML.label',t),
                'price' : v
            })
            total += v

        # 展開された見積もりを順に取得
        rows = self.get_elements("tr[aria-hidden=false]",bill)
        estimate={
            'total' : total,
            'totalItems' : total_items,
            'detail' : []
        }
        s={}
        for row in rows:
            if self.is_member(row,'summary') :
                if s : 
                    estimate['detail'].append(s)
                s={}
                # label
                s['name'] = self.get_text('td:nth-child(2)>div.label', row)
                # subTotal
                s['subTotal'] = float(self.get_value('table.value>tbody>tr>td:nth-child(2)>input', row))
                s['items'] = []
            elif self.is_member(row,'field'):
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
        if (chkbox.get_attribute('value') == 'on') : 
            chkbox.click()

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

