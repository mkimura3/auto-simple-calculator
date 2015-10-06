#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Get a detail estimate  From AWS SIMPLE MONTHLY CALCULATOR

Usage:
    get-aws-estimate.py (-u | --url) <SavedURL> (-s | --server) <SeleniumServerURL> [options]

Options:
    -h,--help           Show this screen.
    --version           Show version.
    -d <driver_type>    Selenium WebDriver Type [default: FIREFOX]
    -f <filename>       Output filename
    -p <file_prefix>    ScreenshotFile prefix name [default: aws-]
    --screen            Take Sceenshot
"""


from docopt import docopt
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import Select
from selenium.webdriver.support.events import EventFiringWebDriver
from selenium.webdriver.support.events import AbstractEventListener
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support import expected_conditions
from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import NoSuchElementException

import unittest, time, re, json, sys
from time import sleep

def pp(obj):
    if isinstance(obj, list) or isinstance(obj, dict):
        orig = json.dumps(obj, indent=4)
        print eval("u'''%s'''" % orig).encode('utf-8')
    else:
        print obj.encode('utf-8')
 
class ScreenshotListener(AbstractEventListener):
    def on_exception(self, exception, driver):
        screenshot_name = "exception.png"
        driver.get_screenshot_as_file(screenshot_name)
        print("Screenshot saved as '%s'" % screenshot_name)


class AwsEstimate():
    def __init__(self, saved_url, server_url, driver_type, file_prefix, screenshot ):
        self.saved_url = saved_url
    	self.command_executor = server_url
    	self.file_prefix = file_prefix
        self.screenshot = screenshot
	    
        if driver_type.strip() == 'FIREFOX' : 
            self.desired_capabilities=DesiredCapabilities.FIREFOX
        elif driver_type.strip() == 'CHROME' :	    
            self.desired_capabilities=DesiredCapabilities.CHROME
        else :
            raise Exception('UnKnown Webdriver Type', driver_type )

    def get_screenshot(self, name ):
        self.driver.get_screenshot_as_file( self.file_prefix + name + '.png' )

    def get_selectedText(self,select):
        return select.find_elements_by_tag_name('option')[ int(select.get_attribute('selectedIndex')) ].text

    def is_checked( self, css, driver=None ):
        element = self.get_element(css, driver)
        if element :
            chk = element.get_attribute('checked')
            return chk == u'true'
        else :
            return False

    def get_value( self, css, driver=None ):
        element = self.get_element(css, driver)
        if element :
            return element.get_attribute('value')
        else :
            return ''

    def get_text( self, css, driver=None ):
        element = self.get_element(css, driver)
        if element :
            return element.text
        else :
            return ''

    def get_element( self,css, driver=None ):
        if driver==None : driver=self.eventdriver
        try :
            ret=driver.find_element_by_css_selector(css)
        except NoSuchElementException, e: return None
        return ret

    def get_elements(self, css, driver=None):
        if driver==None : driver=self.eventdriver
        return driver.find_elements_by_css_selector(css)

    def get_val_and_type(self, css, driver=None):
        if driver==None : driver=self.eventdriver
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
        print >>sys.stderr, '# Connecting Remote server ...'
        self.driver = webdriver.Remote(
            command_executor=self.command_executor,
            desired_capabilities=self.desired_capabilities
        )
        # exception時にScreenShotを取得する
        self.eventdriver = EventFiringWebDriver(self.driver, ScreenshotListener())

        self.driver.implicitly_wait(15)
        #self.base_url = "http://calculator.s3.amazonaws.com"
        self.verificationErrors = []
        self.accept_next_alert = True
        self.wait = WebDriverWait(self.driver, 20)

    def test_aws_estimate(self):
        driver = self.eventdriver
        print >>sys.stderr, '# Accessing URL : ' + self.saved_url
        driver.get(self.saved_url)
        # 概要の取得
        print >>sys.stderr, '# Getting Solution ...'
        # 名前、含まれるもの、概要は省略される可能性あり
        sol = self.get_element("table.SolutionShowBody", self.driver)
        if sol :  
            solution = {
                'Solution' : self.get_solution(sol)
            }
            # スクリーンショット取得
            if self.screenshot : 
                self.get_screenshot('solution')
            # 詳細ボタンを押す
            self.get_element("table.Buttons > tbody > tr > td:nth-child(3) > button").click()
        else :
           solution = {} 
        
        # 無料利用枠チェック外す
        # self.disable_freetier()
        # Serviceメニューの取得
        self.init_serviceMenu() 

        # 見積もりを取得する
        print >>sys.stderr, '# Getting Estimate ...'
        self.get_element("div.billLabel").click()
        bill=self.get_element("table.bill") 
        estimate = {
            'Estimate' : self.get_estimate(bill)
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
            m = re.match(u'^(.*)Service（(.*)）.*', srvc['Name'])
            if m  :
                print >>sys.stderr, '    + ' + m.group(0)
                sc= self.get_awsService( m.group(1).strip() , m.group(2).strip() ) 
                systemconf.update(sc)
            else : # Region区別のないサービスの場合
                n = re.match(u'^(.*) (サービス|Service)', srvc['Name'])
                if n : 
                    print >>sys.stderr, '    + ' + n.group(0)
                    sc= self.get_awsService( n.group(1).strip() , None )
                    systemconf.update(sc)
        # 
        solution.update(estimate)
        solution.update({'SystemConfiguration' : systemconf })
      
        print >>sys.stderr, '# Done.' 
        return solution 


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
        if region_text :
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
        
        # EC2構成情報の取得
        if ( service_name == 'Amazon EC2' ): 
            # print service_name, region_text
            ret = self.get_ec2Service()
        # S3構成情報の取得
        elif ( service_name == 'Amazon S3' ):
            ret = self.get_s3Service()
        # Route53情報の取得
        elif ( service_name == 'Amazon Route 53' ):
            ret = self.get_r53Service()
        # CloudFront情報の取得
        elif ( service_name == u'Amazon CloudFront' ):
            ret = self.get_cloudfrontService()
        # RDS構成情報の取得
        elif ( service_name == 'Amazon RDS' ):
            ret = self.get_rdsService()
        # ElastiCache情報の取得
        elif ( service_name == 'Amazon ElastiCache' ):
            ret = self.get_elasticacheService()
        # CloudWatch情報の取得
        elif ( service_name == u'Amazon CloudWatch' ):
            ret = self.get_cloudwatchService()
        # SES情報の取得
        elif ( service_name == u'Amazon SES' ):
            ret = self.get_sesService()
        # SNS情報の取得
        elif ( service_name == u'Amazon SNS' ):
            ret = self.get_snsService()
        # DirectConnect情報の取得
        elif ( service_name == u'AWS Direct Connect' ):
            ret = self.get_directconnectService()
        # VPC情報の取得
        elif ( service_name == 'Amazon VPC' ):
            ret = self.get_vpcService()
        # 未サポート
        else :
            ret = 'NotSupportedYet'
            time.sleep(1) #画面表示までちょっと待つ
        
        # スクリーンショット取得
        if self.screenshot : 
            self.get_screenshot( service_name.split(' ')[-1]+'-'+region_text.replace(' ', '') )
       
        # Region名を追加 
        if region_text : ret['Region'] = region_text
        return { service_name : ret }

    # -------------------- ElastiCache ----------------------
    def get_elasticacheService(self):
        table = self.get_element('table.service.ElastiCacheService')
        ####
        # キャッシュクラスター: オンデマンドキャッシュノード:
        ondemandnodes = []
        rows = self.get_elements('div.Nodes table.itemsTable tr.ElastiCacheOnDemandNodeRow.itemsTableDataRow', table)
        for row in rows:
            # クラスター名
            desc = self.get_value("table.SF_EC_FIELD_DESCRIPTION input", row)
            # ノード
            quantity = int(self.get_value("table.SF_EC_FIELD_NODES input", row))
            # 使用量
            usage_val , usage_type = self.get_val_and_type("table.SF_EC_FIELD_USAGE", row)
            # ノードタイプ
            node_type = self.get_selectedText(self.get_element("table.SF_EC_FIELD_NODE_TYPE select", row))
            node = {
                'Description' : desc,
                'Quantity' : quantity,
                'Usage' : {
                    'Value' : usage_val,
                    'Type' : node_type
                },
                'NodeType' : node_type
            }
            ondemandnodes.append(node)
        #
        #キャッシュクラスター: リザーブドキャッシュノード:
        reservednodes = []
        rows = self.get_elements('div.ReservedNodes table.itemsTable tr.ElastiCacheReservedNodeRow.itemsTableDataRow', table)
        for row in rows:
            # クラスター名
            desc = self.get_value("table.SF_EC_FIELD_DESCRIPTION input", row)
            # ノード
            quantity = int(self.get_value("table.SF_EC_FIELD_NODES input", row))
            # 使用量
            usage_val , usage_type = self.get_val_and_type("table.SF_EC_FIELD_USAGE", row)
            # ノードタイプ
            node_type = self.get_selectedText(self.get_element("table.SF_EC_FIELD_NODE_TYPE select", row))
            # 提供内容
            offering_type = self.get_selectedText(self.get_element("table.SF_EC2_RESERVED_FIELD_UTILIZATION select", row))
            # 提供期間
            offering_term = self.get_selectedText(self.get_element("table.SF_EC2_RESERVED_FIELD_TERM select", row))
            
            node = {
                'Description' : desc,
                'Quantity' : quantity,
                'Usage' : {
                    'Value' : usage_val,
                    'Type' : node_type
                },
                'NodeType' : node_type,
                'OfferingType' : offering_type,
                'OfferingTerm' : offering_term
            }
            reservednodes.append(node)
        #
        return {
            'OnDemandNodes' : ondemandnodes,
            'ReservedNodes' : reservednodes
        }

        
    # -------------------- DirectConnect ----------------------
    def get_directconnectService(self):
        table = self.get_element('table.service.DirectConnectService')
        ####
        # AWS Direct Connect のポートとロケーション
        directconnects = []
        rows = self.get_elements('div.Instances table.itemsTable tr.DirectConnectInstanceRow.itemsTableDataRow', table)
        for row in rows:
            # ポートの説明
            desc = self.get_value("table.SF_DIRECT_CONNECT_FIELD_DESCRIPTION input", row)
            # ポート
            ports, port_speed = self.get_val_and_type("table.SF_DIRECT_CONNECT_FIELD_PORTS", row)
            # ポート使用量
            usage_val, usage_type = self.get_val_and_type("table.SF_DIRECT_CONNECT_FIELD_USAGE", row)
            # ロケーション
            location = self.get_selectedText(self.get_element("table.SF_DIRECT_CONNECT_FIELD_LOCATION select", row))
            # データ転送受信
            recv_val , recv_type = self.get_val_and_type("tr > td.cell:nth-child(6) > table", row)
            # データ転送送信
            send_val , send_type = self.get_val_and_type("tr > td.cell:nth-child(7) > table", row)
            directconnect = {
                'Destciption' : desc,
                'Quantity' : int(ports),
                'PortSpeed' : port_speed,
                'PortUsage' : {
                    'Value' : usage_val,
                    'Type'  : usage_type
                },
                'Location' : location,
                'DataTransferOut': {
                    'Value' : send_val,
                    'Type' : send_type
                },
                'DataTransferIn': {
                    'Value' : recv_val,
                    'Type' : recv_type
                }
            }
            directconnects.append(directconnect)
        #
        return {
            'DirectConnects' : directconnects
        }

     
    # -------------------- SNS ----------------------
    def get_snsService(self):
        table = self.get_element('table.service.SNSService')
        # リクエストと通知:
        ## リクエスト:
        request = int(self.get_value("table.SF_SNS_REQUESTS input", table))
        ## 通知:
        notify_size, notify_type = self.get_val_and_type("table.SF_SNS_NOTIFICATIONS", table)
        # データ転送:
        ## データ転送送信
        send_size , send_unit = self.get_val_and_type("table.subSection:nth-child(3) div.subContent > table:nth-child(1)", table) 
        ## データ転送受信
        recv_size , recv_unit = self.get_val_and_type("table.subSection:nth-child(3) div.subContent > table:nth-child(2)", table) 
    
        return {
            'Requests' : request,
            'Notifications' : {
                'Messages' : notify_size, 
                'Type' : notify_type
            },
            'DataTransferOut': {
                'Value' : send_size,
                'Type' : send_unit
            },
            'DataTransferIn': {
                'Value' : recv_size,
                'Type' : recv_unit
            }
        }   
 
    # -------------------- SES ----------------------
    def get_sesService(self):
        table = self.get_element('table.service.SESService')
        # メッセージ:
        ## Eメールメッセージ:
        emails = int(self.get_value("table.SF_SES_EMAIL_MESSAGES input", table))
        # 添付ファイル:
        ## データ転送送信（添付ファイル）:
        attach_size , attach_unit = self.get_val_and_type("table.subSection:nth-child(3) div.subContent > table:nth-child(1)", table) 
        # データ転送:
        ## データ転送送信:
        send_size , send_unit = self.get_val_and_type("table.subSection:nth-child(4) div.subContent > table:nth-child(1)", table) 
        ## データ転送受信:
        recv_size , recv_unit = self.get_val_and_type("table.subSection:nth-child(4) div.subContent > table:nth-child(2)", table) 
        
        return {
            'emailMessages': emails ,
            'AttachmentsOut': {
                'Value' : attach_size,
                'Type' : attach_unit
            },
            'DataTransferOut': {
                'Value' : send_size,
                'Type' : send_unit
            },
            'DataTransferIn': {
                'Value' : recv_size,
                'Type' : recv_unit
            }
        }
        
    # -------------------- CloudWatch ----------------------
    def get_cloudwatchService(self):
        table = self.get_element('table.service.CloudWatchService')
        # waitを短く
        #self.driver.implicitly_wait(1)  
        ####
        # カスタムメトリクス
        custmetrics = []
        rows = self.get_elements('div.CustomMetrics table.itemsTable tr.CloudWatchMetricsRow.itemsTableDataRow', table)
        for row in rows:
            # 説明
            desc = self.get_value("table.SF_CW_FIELD_DESCRIPTION input", row)
            # リソース数
            resources = int(self.get_value("table.SF_CW_FIELD_RESOURCES input", row))
            # カスタムメトリクス数
            metrics = int(self.get_value("table.SF_CW_FIELD_CUSTOM_METRICS input", row))
            # メトリックデータの頻度
            frequency = self.get_selectedText(self.get_element("table.SF_CW_FIELD_METRICS_FREQUENCY select",row))
            # リソースあたりのアラーム
            alarms = int(self.get_value("table.SF_CW_FIELD_ALARMS input", row))
            # 取り込まれたログのサイズ
            ingested_log = int(self.get_value("table.SF_CW_FIELD_ARCHIVED_LOGS input", row))
            # アーカイブされたログのサイズ
            archived_log = int(self.get_value("table.SF_CW_FIELD_INGESTED_LOGS input", row))
            cust = {
                'Description' : desc,
                'Resources' : resources,
                'CustomMetrics' : metrics,
                'Frequency' : frequency,
                'Alarms' : alarms,
                'IngestedLogs' : ingested_log,
                'ArchivedLogs' : archived_log
            }
            custmetrics.append(cust)

        #  アラーム
        ## EC2 インスタンス
        ec2_alarms = int(self.get_value("table.SF_CW_EC2_ALARMS input", table))
        ## Elastic Load Balancing
        elb_alarms = int(self.get_value("table.SF_CW_ELB_ALARMS input", table))
        ## EBS ボリューム
        ebs_alarms = int(self.get_value("table.SF_CW_EBS_ALARMS input", table))
        ## RDS DB インスタンス
        rds_alarms = int(self.get_value("table.SF_CW_RDS_ALARMS input", table))
        ## Auto Scaling 
        as_alarms = int(self.get_value("table.SF_CW_AS_ALARMS input", table))
        
        return {
            'CustomMetrics' : custmetrics,
            'EC2Alarms' : ec2_alarms,
            'ELBAlarms' : elb_alarms,
            'EBSAlarms' : ebs_alarms,
            'RDSAlarms' : rds_alarms,
            'AutoScalingAlarms' : as_alarms
        }
        
    # -------------------- CloudFront ----------------------
    def get_cloudfrontService(self):
        table = self.get_element('table.service.CloudFrontService')
        # データ転送送信:
        #   毎月のボリューム:
        trans_size ,trans_unit = self.get_val_and_type("div.body > table.subSection:nth-child(1) div.subContent table.amountField", table)
        # リクエスト:
        #   平均オブジェクトサイズ:
        avg_object_size = int(self.get_value("table.SF_CLOUD_FRONT_AVERAGE_OBJECT_SIZE input", table))
        #   リクエストのタイプ:
        # HTTPにチェック
        if self.is_checked("table.SF_CLOUD_FRONT_TYPE_OF_REQUESTS td.Column0 input[type='radio']") :
            request_type ='HTTP'
        else:
            request_type ='HTTPS'
        #   無効化リクエスト:
        request_invalid = int(self.get_value("table.SF_CLOUD_FRONT_INVALIDATION_REQUESTS input", table)) 
        # エッジロケーションのトラフィックディストリビューション:
        #   米国
        percent_us = int(self.get_value("table.SF_CLOUD_FRONT_TIER_US input", table)) 
        #   欧州
        percent_eu = int(self.get_value("table.SF_CLOUD_FRONT_TIER_EU input", table)) 
        #   香港、フィリピン、韓国、シンガポールおよび台湾
        percent_hk = int(self.get_value("table.SF_CLOUD_FRONT_TIER_HK input", table)) 
        #   日本
        percent_jp = int(self.get_value("table.SF_CLOUD_FRONT_TIER_JP input", table)) 
        #   南米
        percent_sa = int(self.get_value("table.SF_CLOUD_FRONT_TIER_SA input", table)) 
        #   オーストラリア
        percent_au = int(self.get_value("table.SF_CLOUD_FRONT_TIER_AU input", table)) 
        #   インド
        percent_in = int(self.get_value("table.SF_CLOUD_FRONT_TIER_IN input", table)) 

        # 専用 IP SSL 証明書:
        #   証明書の数:
        custom_ssl = int(self.get_value("table.SF_CLOUD_FRONT_CUSTOM_SSL_CERTS input", table)) 
        
        return {
            'MonthlyVolume' : {
                'Value' : trans_size,
                'Type' : trans_unit
            },
            'AverageObjectSize': avg_object_size,
            'RequestType' : request_type,
            'InvalidationRequests' : request_invalid,
            'EdgeLocationDistribution' : {
                'US': percent_us,
                'EU': percent_eu,
                'HK': percent_hk,
                'JP': percent_jp,
                'SA': percent_sa,
                'AU': percent_au,
                'IN': percent_in
            },
            'CustomCertificates' : custom_ssl
        }

    # -------------------- Route53 ----------------------
    def get_r53Service(self):
        table = self.get_element('table.service.Route53Service')
        # ホストゾーン
        #   ホストゾーン:
        hosted_zone = int(self.get_value("table.SF_ROUTE_53_HOSTED_ZONES input", table))
        #   標準的クエリ:
        std_query ,std_unit = self.get_val_and_type("table.SF_ROUTE_53_STANDARD_QUERIES", table)
        #   レイテンシーベースルーティングクエリ:
        latency_query ,latency_unit = self.get_val_and_type("table.SF_ROUTE_53_LATENCY_QUERIES", table)
        #   Geo DNS クエリ:
        geo_query ,geo_unit = self.get_val_and_type("table.SF_ROUTE_53_GEO_DNS_QUERIES", table)

        # エンドポイントの DNS フェイルオーバーヘルスチェック
        #   Basic Checks Within AWS:
        basic_internal = int(self.get_value("table.SF_ROUTE_53_INTERNAL_BASIC_CHECKS input", table))
        #   Basic Checks Outside of AWS:
        basic_external = int(self.get_value("table.SF_ROUTE_53_EXTERNAL_BASIC_CHECKS input", table))
        #   HTTPS Checks Within AWS:
        http_internal = int(self.get_value("table.SF_ROUTE_53_INTERNAL_HTTPS_CHECKS input", table))
        #   HTTPS Checks Outside of AWS:
        http_external = int(self.get_value("table.SF_ROUTE_53_EXTERNAL_HTTPS_CHECKS  input", table))
        #   String Matching Checks Within AWS:
        string_internal = int(self.get_value("table.SF_ROUTE_53_INTERNAL_STRINGMATCHING_CHECKS input", table))
        #   String Matching Checks Outside of AWS:
        string_external = int(self.get_value("table.SF_ROUTE_53_EXTERNAL_STRINGMATCHING_CHECKS input", table))
        #   Fast Interval Checks Within AWS:
        fast_internal = int(self.get_value("table.SF_ROUTE_53_INTERNAL_FASTINTERVAL_CHECKS input", table))
        #   Fast Interval Checks Outside of AWS:
        fast_external = int(self.get_value("table.SF_ROUTE_53_EXTERNAL_FASTINTERVAL_CHECKS input", table))

        return {
            'HostedZones' : hosted_zone,
            'StandardQueries' : { 
                'Value' : std_query,
                'Type' : std_unit
            },
            'LatencyQueries' : { 
                'Value' : latency_query,
                'Type' : latency_unit
            },
            'GEOQueries' : { 
                'Value' : geo_query,
                'Type' : geo_unit
            },
            'BasicChecksInternal' : basic_internal,
            'BasicChecksExternal' : basic_external,
            'HTTPChecksInternal' : http_internal,
            'HTTPChecksExternal' : http_external,
            'StringChecksInternal' : string_internal,
            'StringChecksExternal' : string_external,
            'FastintervalChecksInternal' : fast_internal,
            'FastintervalChecksExternal' : fast_external
        }

    # -------------------- VPC ----------------------
    def get_vpcService(self):
        table = self.get_element('table.service.VPNService')
        # waitを短く
        self.driver.implicitly_wait(1)  
        ####
        # インスタンス
        vpccons = []
        rows = self.get_elements('div.VPNConnections table.itemsTable tr.VPNConnectionRow.itemsTableDataRow', table)
        for row in rows:
            # VPC説明
            desc = self.get_value("table.SF_VPC_FIELD_DESCRIPTION input", row)
            # 接続数
            quantity = int(self.get_value("table.SF_VPC_FIELD_INSTANCES input", row))
            # 使用量
            usage_val,  usage_type = self.get_val_and_type('table.SF_VPC_FIELD_USAGE', row)
            # データ転送送信
            send_data,  send_type = self.get_val_and_type('tr>td.cell:nth-child(5)>table.dataTransferField.amountField', row)
            # データ転送受信
            recv_data,  recv_type = self.get_val_and_type('tr>td.cell:nth-child(6)>table.dataTransferField.amountField', row)
                 
            vpccon= {
                'Description' : desc,
                'Quantity' : quantity,
                'Usage' : {
                    'Value' : usage_val,
                    'Type' : usage_type,
                },
                'DataCenterSend' : {
                        'Value' : send_data,
                        'Type'  : send_type
                },
                'DataCenterReceive' : {
                    'Value' : recv_data,
                    'Type'  : recv_type
                }
            }
            vpccons.append(vpccon)
        return {
            'VPCConnections' : vpccons
        }

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
                'Description' : desc,
                'Quantity' : quantity,
                'Usage' : {
                    'Value' : usage_val,
                    'Type' : usage_type,
                },
                'Engine' : engine,
                'InstanceType' : instance_type,
                'Deployment' : deploy_type,
                'Storage' : {
                    'Type' : storage_type,
                    'Size' : storage_size,
                    'Iops' : iops
                }
            }
            instances.append(instance)
        # 追加のバックアップストレージ 
        volumes = []
        rows = self.get_elements('div.Volumes table.itemsTable tr.RDSBackupRow.itemsTableDataRow', table)
        for row in rows:
            backup_size , backup_type = self.get_val_and_type('table.SF_RDS_FIELD_BACKUP', row )
            volumes.append({
                'Value' : backup_size,
                'Type' : backup_type
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
                'Description' : desc,
                'Quantity' : quantity,
                'Usage' : {
                    'Value' : usage_val,
                    'Type' : usage_type,
                },
                'Engine' : engine,
                'Type' : instance_type,
                'Deployment' : deploy_type,
                'Storage' : {
                    'Type' : storage_type,
                    'Size' : storage_size,
                    'Iops' : iops
                },
                'OfferingType' : offering_type,
                'OfferingTerm' : offering_term
            }
            rinstances.append(rinstance)

        return {
            'Instances' : instances,
            'BackupVolumes' : volumes,
            'ReservedInstances' : rinstances
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
            'StandardStorage': {
                'Value' : s3_size,
                'Type' : s3_size_unit
            },
            'ReducedRedundancy': {
                'Value' : rr_size,
                'Type' : rr_size_unit
            },
            'PutCopyPostListRequests' : req_put,
            'GetOtherRequests' : req_get,
            "InterRegion" : {
                "Value" : inter_region,
                "Type"  : inter_region_type
            },
            "InternetSend" : {
                "Value" : internet_out,
                "Type"  : internet_out_type
            },
            "InternetReceive" : {
                "Value" : internet_in,
                "Type"  : internet_in_type
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
                    'Description' : desc,
                    'Quantity' : quantity,
                    'Usage' : {
                        'Value' : usage_val,
                        'Type' : usage_type,
                    },
                    'BillingOption' : billing
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
                'Description' : desc,
                'Quantity' : quantity,
                'Size' : size,
                'Iops' : iops,
                'EBSType' : ebs_type,
                'SnapshotType' : snap_type,
                'SnapshotSize' : snap_size
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
            "Instances" : instances,
            "Storages"  : storages,
            "ElasticIp" : {
                "Quantity" : eip_quantity,
                "UnAttached" : {
                    "Value" : eip_notime, 
                    "Type" : eip_notype
                },
                "Remaps" : {
                    "Value" : eip_remap, 
                    "Type" : eip_retype
                }
            },
            "DataTranfer" : {
                "InterRegion" : {
                    "Value" : interr_data,
                    "Type"  : interr_type
                },
                "IntraRegion" : {
                    "Value" : intra_region,
                    "Type"  : intra_region_type
                },
                "InternetSend" : {
                    "Value" : internet_out,
                    "Type"  : internet_out_type
                },
                "InternetReceive" : {
                    "Value" : internet_in,
                    "Type"  : internet_in_type
                },
                "VpnPeers" : {
                    "Value" : vpcpeer_data,
                    "Type"  : vpcpeer_data_type
                },
                "IntraRegionEIPELB" : {
                    "Value" : eip_data,
                    "Type"  : eip_data_type
                }
            },
            "ElasticLoadBalancing" : {
                "Quantity" : elb_quantity,
                "ELBTransfer" : {
                    "Value" : elb_total,
                    "Type"  : elb_total_type
                }
            }
        }
    

    def get_instanceType(self,row):
        EBS_DESC = u'EBS'
        MONITOR_DESC = u'詳細モニタリングあり'
        TENANCY_DESC = u'専用|ハードウェア専有'
        type_div = self.get_element('div.SF_EC2_INSTANCE_FIELD_TYPE',row)
        tlines = type_div.text.splitlines()
        # OS
        instance_os = tlines[0].split(u'、')[0].strip()
        # インスタンスタイプ
        instance_type = tlines[0].split(u'、')[1].strip()

        # デフォルト設定
        instance_ebsopt = False
        instance_monitor = False
        instance_tenancy = False
        
        if len(tlines) > 1 : #2行目に記述がある場合
            txt = tlines[1].strip()
            # EBS最適化
            if re.search(EBS_DESC , txt , re.U) : instance_ebsopt=True
            # 詳細モニタリング
            if re.search(MONITOR_DESC , txt, re.U) : instance_monitor=True
            # ハードウェア占有
            if re.search(TENANCY_DESC , txt, re.U) : instance_tenancy=True
        """ 
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
        """
        # 
        return {
                'OS': instance_os,
                'InstanceType' : instance_type,
                'EbsOptimized' : instance_ebsopt,
                'DetailedMonitor' : instance_monitor,
                'Dedicated' : instance_tenancy
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
                if ('Items' in s ) : s['Items'].append(i)
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
        #self.assertEqual([], self.verificationErrors)

if __name__ == "__main__":

    args = docopt(__doc__, version="0.1.0")

    # print >>sys.stderr, args

    ae = AwsEstimate(
        saved_url=args['<SavedURL>'], 
        server_url=args['<SeleniumServerURL>'],
        driver_type=args['-d'],
        file_prefix=args['-p'],
        screenshot=args['--screen'] )

    ae.setUp()
    solution=ae.test_aws_estimate()
    ae.tearDown()

    output=json.dumps(solution, indent=4, ensure_ascii=False ).encode('utf-8')
    
    if args['-f'] :
        filename = args['-f']
        fp=open(filename,'w')
        print >> fp, output
        fp.close()
    else:
        print output

