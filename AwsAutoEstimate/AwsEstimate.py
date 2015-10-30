#!/usr/bin/env python
# -*- coding: utf-8 -*-
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions

from base.AwsService import AwsService

from services.EC2 import EC2
from services.S3 import S3
from services.CloudFront import CloudFront
from services.CloudWatch import CloudWatch
from services.DirectConnect import DirectConnect
from services.ElastiCache import ElastiCache
from services.RDS import RDS
from services.Route53 import Route53
from services.SES import SES
from services.SNS import SNS
from services.VPC import VPC

import unittest, time, re, json, sys
from time import sleep

def pp(obj):
    if isinstance(obj, list) or isinstance(obj, dict):
        orig = json.dumps(obj, indent=4)
        print eval("u'''%s'''" % orig).encode('utf-8')
    else:
        print obj.encode('utf-8')

class AwsEstimate(AwsService):
    def __init__(self, server_url, driver_type, file_prefix=''):
        if driver_type.strip() == 'FIREFOX' :
            self.desired_capabilities=DesiredCapabilities.FIREFOX
        elif driver_type.strip() == 'CHROME' :
            self.desired_capabilities=DesiredCapabilities.CHROME
        else :
            raise Exception('UnKnown Webdriver Type', driver_type )
        
        print >>sys.stderr, '# Connecting Remote server ...'
        driver = webdriver.Remote(
            command_executor=server_url,
            desired_capabilities=self.desired_capabilities
        )
        super(AwsEstimate,self).__init__(driver,file_prefix)
        #
        self.driver.implicitly_wait(15)
        self.driver.set_window_size(1024,768)
   
    def tearDown(self):
        self.driver.quit()

    def getEstimate(self, saved_url, screenshot=False):
        self.screenshot=screenshot
        driver = self.eventdriver
        # 見積もりに移動
        print >>sys.stderr, '# Accessing URL : ' + saved_url
        driver.get(saved_url)
        # 見積もり概要の取得
        solution = self.getSolution()
        # TODO: 無料利用枠のチェック

        # 見積もりを取得する
        estimate = {
            'Estimate' : self.get_estimate_detail()
        }
        # スクリーンショット取得
        if self.screenshot :
            self.get_screenshot('estimate')
        # Regionリストの取得
        self.init_regionList()
        # 見積もり項目ごとに構成を取得する
        print >>sys.stderr, '# Getting SystemConfiguration ...'
        systemconf = {}
        for srvc in estimate['Estimate']['Detail']:
            # AWS Supportの場合
            sup = re.match(u'^AWS サポート（(.*)）', srvc['Name'])
            if sup:
                print >>sys.stderr, '    + ' + srvc['Name']
                systemconf.update({
                    "AWS Support" : {
                        "Plan": sup.group(1).strip()
                    }
                })
                continue
            #
            m = re.match(u'^(.*)(サービス|Service)（(.*)）.*', srvc['Name'])
            if m  : # Regionありのサービスの場合
                print >>sys.stderr, '    + ' + m.group(0)
                sc= self.get_awsService( m.group(1).strip() , m.group(3).strip() )
                systemconf.update(sc)
            else : # Region区別のないサービスの場合
                n = re.match(u'^(.*) (サービス|Service)', srvc['Name'])
                if n :
                    print >>sys.stderr, '    + ' + n.group(0)
                    sc= self.get_awsService( n.group(1).strip() , None )
                    systemconf.update(sc)
        #
        ret = {}
        ret.update(solution) 
        ret.update(estimate)
        ret.update({'SystemConfiguration' : systemconf })
        #
        print >>sys.stderr, '# Done.'
        return ret



    def getSolution(self):
        solution = {}
        print >>sys.stderr, '# Getting Solution ...'
        # 名前、含まれるもの、概要は省略される可能性あり
        sol = self.get_element("table.SolutionShowBody",self.driver)
        if sol :
            solution = {
                'Solution' : self.get_solution_item(sol)
            }
            # スクリーンショット取得
            if self.screenshot :
                self.get_screenshot('solution')
            # 詳細ボタンを押す
            self.get_element("table.Buttons > tbody > tr > td:nth-child(3) > button").click()
        #
        return solution

    def get_solution_item(self,solution):
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
            'Name' : sc_name,
            'Includes' : sc_include,
            'Description' : sc_desc
        }

    def select_service(self, serviceName):
        #self.serviceTab[serviceName].click()
        tabs = self.get_elements("div.servicesPanel > div.tabs > div.tab[aria-hidden=false]")
        for tab in tabs:
            if serviceName ==  tab.text.strip() :
                tab.click()
                break
    
    def init_regionList(self):
        self.select_service(u'Amazon EC2')
        self.regionList = []
        # Region一覧の取得
        regions = self.get_elements("select.gwt-ListBox.CR_CHOOSE_REGION.regionListBox option")
        for region in regions :
            self.regionList.append(region.text.strip())

    def select_region(self, region_text):
        if region_text :
            self.set_select('select.gwt-ListBox.CR_CHOOSE_REGION.regionListBox', region_text)

    def get_estimate_detail(self, waiting=True):
        print >>sys.stderr, '# Getting Estimate ...'
        # 見積もりに移動
        self.get_element("div.billLabel").click()
        bill=self.get_element("table.bill")
        # ちょっと待ってから[+]をクリックする 
        if waiting : time.sleep(3)
        btns = self.get_elements("tr.columnTreeRow.summary[aria-hidden=false] img[src$='tree-up.png']", bill)
        for btn in btns:
            btn.click()
        # 月額合計
        total_items =[]
        total = float(self.get_value('tr.total:not([aria-hidden]) table.value>tbody>tr>td:nth-child(2)>input',bill))
        total_items.append({
            'Name' : self.get_text('tr.total:not([aria-hidden])>td:nth-child(1)>div.gwt-HTML.label'),
            'Price' : total
        })
        # サポートやリザーブ分を足す
        totals = self.get_elements('tr.total[aria-hidden=false]',bill)
        for t in totals:
            #print self.get_text('tr>td>div.gwt-HTML.label',t), self.get_value('table.value>tbody>tr>td:nth-child(2)>input',t)
            v = float(self.get_value('table.value>tbody>tr>td:nth-child(2)>input',t))
            total_items.append({
                'Name' : self.get_text('tr>td>div.gwt-HTML.label',t),
                'Price' : v
            })
            total += v
        # 展開された見積もりを順に取得
        rows = self.get_elements("tr[aria-hidden=false]",bill)
        estimate={
            'Total' : total,
            'TotalItems' : total_items,
            'Detail' : []
        }
        s={}
        for row in rows:
            if self.is_member(row,'summary') :
                if s :
                    estimate['Detail'].append(s)
                    s={}
                # label
                s['Name'] = self.get_text('td:nth-child(2)>div.label', row)
                # subTotal
                s['SubTotal'] = float(self.get_value('table.value>tbody>tr>td:nth-child(2)>input', row))
                s['Items'] = []
            elif self.is_member(row,'field'):
                i = {}
                # sublabel
                i['Name'] = self.get_text('td:nth-child(1)>div.label', row)
                # price
                i['Price'] = float(self.get_value('table.value>tbody>tr>td:nth-child(2)>input',row))
                if 'Items' in s  : s['Items'].append(i)
        #
        if s : estimate['Detail'].append(s)
        # 見積もり合計値のチェック
        self.check_estimate(estimate)
        return estimate

    def check_estimate(self, estimate):
        # subTotalの合計が月額合計と等しいか
        assert round(estimate['Total'],2)== round(sum([ a['SubTotal'] for a in estimate['Detail'] ] ),2)

        #各subTotalが項目合計と等しいか
        for field in estimate['Detail']:
            #print field['Name'], field['SubTotal']  
            assert round(field['SubTotal'],2) == round(sum([ a['Price']  for a in field['Items'] ]),2)

    def get_awsService(self, service_name, region_name):
        # 見積もりRegion名から、Regionプルダウンを特定
        region_text = ''
        if region_name :
            for k in self.regionList:
                if ( k.find(region_name) >=0 ) :
                    region_text = k
                    break
            # TODO: regionエラー処理

        # 該当サービスを表示
        self.select_service(service_name)
        # Region選択
        self.select_region(region_text)
        # Serive情報の取得
        service = self.serviceInstance(service_name)
        if service :
            ret = service.get_serviceConfig()
        else :  # 未サポート
            ret = 'NotSupportedYet'
            time.sleep(1) #画面表示までちょっと待つ
        # スクリーンショット取得
        if self.screenshot :
            self.get_screenshot( service_name.split(' ')[-1]+'-'+region_text.replace(' ', '') )
        # Region名を追加 
        if region_text : ret['Region'] = region_text
        #
        return { service_name : ret }

    def createEstimate(self, system_conf, screenshot=False):
        self.screenshot = screenshot
        start_url = "http://calculator.s3.amazonaws.com/index.html?lng=ja_JP"
        driver = self.eventdriver
        print >>sys.stderr, '# Accessing URL : ' + start_url
        driver.get(start_url)
        time.sleep(1) #画面表示までちょっと待つ
        # 無料利用枠チェック外す
        self.disable_freetier()
        # Serviceメニューの取得
        #self.init_serviceMenu() 
        # Regionリストの取得
        self.init_regionList()
        # サービス項目ごとに構成を設定する
        print >>sys.stderr, '# Setting SystemConfiguration ...'
        for k ,v in system_conf['SystemConfiguration'].items():
            print >>sys.stderr, '    + ' + k
            self.set_awsService( k, v )
        # Supportは最後に設定する
        ret = self.set_supportService(system_conf['SystemConfiguration'])
        # 見積もりを取得する
        estimate_detail = self.get_estimate_detail(False)
        
        # 保存して共有 
        print >>sys.stderr, '# Done.'
        saved_url = self.get_estimate_url( system_conf['Solution'] )
        return {
            'SavedURL' : saved_url,
            'Estimate' : estimate_detail
        }

    def get_estimate_url(self,solution):
        # 見積もりタブに移動
        self.get_element('div.billLabel').click()
        # 保存して共有ボタンを押す
        self.get_element('button.saveButton').click()
        # 名前
        if 'Name' in solution:
            self.set_value('div.SolutionSaveDialog input.SC_SOLUTION_Input' , solution['Name'])
        # 含まれるもの
        if 'Includes' in solution:
            self.set_textbox('div.SolutionSaveDialog textarea.SC_INCLUDES_Input', solution['Includes'])
        # 説明
        if 'Description' in solution:
            self.set_textbox('div.SolutionSaveDialog textarea.SC_DESCRIPTION_Input', solution['Description'])
        # URL取得
        self.get_element("div.SolutionSaveDialog table.Buttons > tbody > tr > td > table > tbody > tr > td:nth-child(3) > button").click()
        wait = WebDriverWait(self.driver, 20)
        estimate = wait.until( expected_conditions.presence_of_element_located((By.ID,'saveURL')))
        print >>sys.stderr, 'saved Url: ' +  estimate.get_attribute('href')
        return estimate.get_attribute('href')

    def set_awsService(self, service_name, service_conf):
        # Support設定は最後に行うためここではスキップ
        if ( service_name == 'AWS Support' ):
            return

        region_text = ''
        # Regionの指定があるとき
        if 'Region' in service_conf:
            region_text=service_conf['Region']

        # 該当サービスを表示
        self.select_service(service_name)
        # Region選択
        self.select_region(region_text)
        # Serive情報の取得
        service = self.serviceInstance(service_name)
        if service :
            ret = service.set_serviceConfig(service_conf)
        else :  # 未サポート
            print >>sys.stderr, service_name + ':' + region_text  + ':NotSupportedYet'
            ret = 'NotSupportedYet'
            time.sleep(1) #画面表示までちょっと待つ

        # スクリーンショット取得
        if self.screenshot :
            self.get_screenshot( service_name.split(' ')[-1]+'-'+region_text.replace(' ', '') )

        return

    def set_supportService(self, sysconf):
        # 該当サービスを表示
        self.select_service('AWS Support')
        # 
        table = self.get_element('table.service.PremiumSupportService')
        plans = self.get_elements('table.gwt-RadioButton.msgRadioButton',table)
        # デフォルトの選択
        self.get_element("input[type='radio']",plans[0] ).click()
        if 'AWS Support' in sysconf :
            conf = sysconf['AWS Support']
            if 'Plan' in conf:
                for plan in plans:
                    i = plan.text.strip().find( conf['Plan'] )
                    if i >= 0 :
                        time.sleep(0.1)
                        self.get_element("input[type='radio']",plan).click()
                        break

    def disable_freetier(self):
        # 無料利用枠チェック外す
        chkbox=self.get_element("#gwt-uid-2")
        if (chkbox.get_attribute('value') == 'on') :
            chkbox.click()
    
    def serviceInstance( self, service_name ):
        service = None
        # EC2
        if ( service_name == 'Amazon EC2' ):
            service = EC2(self.driver, self.file_prefix)
        # S3
        elif ( service_name == 'Amazon S3' ):
            service = S3(self.driver, self.file_prefix)
        # Route53
        elif ( service_name == 'Amazon Route 53' ):
            service = Route53(self.driver, self.file_prefix)
        # CloudFront
        elif ( service_name == u'Amazon CloudFront' ):
            service = CloudFront(self.driver, self.file_prefix)
        # RDS
        elif ( service_name == 'Amazon RDS' ):
            service = RDS(self.driver, self.file_prefix)
        # ElastiCache
        elif ( service_name == 'Amazon ElastiCache' ):
            service = ElastiCache(self.driver, self.file_prefix)
        # CloudWatch
        elif ( service_name == u'Amazon CloudWatch' ):
            service = CloudWatch(self.driver, self.file_prefix)
        # SES
        elif ( service_name == u'Amazon SES' ):
            service = SES(self.driver, self.file_prefix)
        # SNS
        elif ( service_name == u'Amazon SNS' ):
            service = SNS(self.driver, self.file_prefix)
        # DirectConnect
        elif ( service_name == u'AWS Direct Connect' ):
            service = DirectConnect(self.driver, self.file_prefix)
        # VPC
        elif ( service_name == 'Amazon VPC' ):
            service = VPC(self.driver, self.file_prefix)
        #
        return service

if __name__ == "__main__":
    # TODO : Docoptsの設定
   
    # get
    saved_url = 'http://calculator.s3.amazonaws.com/index.html?lng=ja_JP#r=NRT&s=RDS&key=calc-8003D1CC-2CE9-4824-90A0-F56EC75CB69E' 
    estimate = AwsEstimate('http://192.168.56.1:4444/wd/hub','FIREFOX')
    estimate_json = estimate.getEstimate( saved_url, False ) 
    pp(estimate_json)
    get_total = estimate_json['Estimate']['Total']
    estimate.tearDown()
    estimate = None
    # create
    estimate = AwsEstimate('http://192.168.56.1:4444/wd/hub','FIREFOX')
    ret = estimate.createEstimate(estimate_json)
    pp(ret)
    create_total = ret['Estimate']['Total']
    assert get_total == create_total
    estimate.tearDown()
    estimate = None


