#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Create Estimate Using AWS SIMPLE MONTHLY CALCULATOR

Usage:
    create-aws-estimate.py (-f | --file) <SystemConfigFile> (-s | --server) <SeleniumServerURL> [options]

Options:
    -h,--help           Show this screen.
    --version           Show version.
    -d <driver_type>    Selenium WebDriver Type [default: FIREFOX]
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


class AwsSystemConfig():
    RETRY = 3 
    ec2InstanceTypes = {} 
    
    def __init__(self, system_conf, server_url, driver_type, file_prefix, screenshot ):
        self.system_conf = system_conf
    	self.command_executor = server_url
    	self.file_prefix = file_prefix
        self.screenshot = screenshot
        self.start_url = "http://calculator.s3.amazonaws.com/index.html?lng=ja_JP"
	    
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

    def set_textbox( self, css, value, driver=None):
        element = self.get_element(css, driver)
        element.clear()
        element.send_keys(value)

    def set_value( self, css, value, driver=None, value_type=None):
        if value_type: 
            v = value_type(value)
        else:
            v = value
        element = self.get_element(css, driver)
        element.clear()
        element.send_keys([str(v), Keys.ENTER])
    
    def set_checkbox( self, css, value, driver=None):
        chkbox = self.get_element(css, driver)
        chk = chkbox.get_attribute('checked')
        if value : 
            # True
            if (chk!=u'true') : chkbox.click()
        else :
            # False
            if (chk==u'true') : chkbox.click()

    def set_select( self, css, value, driver=None):
        s = self.get_element(css, driver)
        Select(s).select_by_visible_text(value)

    def set_val_and_type(self, css, values, driver=None, value_type=None):
        if driver==None : driver=self.eventdriver
        # input
        if 'Value' in values :
            if value_type: 
                v = value_type(values['Value'])
            else:
                v = values['Value']
            i = driver.find_element_by_css_selector(css + ' input')
            i.send_keys([str(v), Keys.ENTER])
        # select
        if 'Type' in values :
            s = driver.find_element_by_css_selector(css + ' select')
            Select(s).select_by_visible_text(values['Type'])

    def setUp(self):
        print >>sys.stderr, '# Connecting Remote server ...'
        self.driver = webdriver.Remote(
            command_executor=self.command_executor,
            desired_capabilities=self.desired_capabilities
        )
        # exception時にScreenShotを取得する
        self.eventdriver = EventFiringWebDriver(self.driver, ScreenshotListener())

        self.driver.implicitly_wait(15)
        self.driver.set_window_size(1024,768)
        self.verificationErrors = []
        self.accept_next_alert = True
        self.wait = WebDriverWait(self.driver, 20)

    def create_aws_estimate(self):
        driver = self.eventdriver
        print >>sys.stderr, '# Accessing URL : ' + self.start_url
        driver.get(self.start_url)
        time.sleep(1) #画面表示までちょっと待つ
        # 無料利用枠チェック外す
        self.disable_freetier()
        # Serviceメニューの取得
        #self.init_serviceMenu() 
        # Regionリストの取得
        self.init_regionList()
        # サービス項目ごとに構成を設定する
        print >>sys.stderr, '# Setting SystemConfiguration ...'
        system_conf = self.system_conf
        for k ,v in system_conf['SystemConfiguration'].items():
            print >>sys.stderr, '    + ' + k
            self.set_awsService( k, v )
        # 保存して共有 
        print >>sys.stderr, '# Done.' 
        saved_url = self.get_estimate_url( system_conf['Solution'] )
        return saved_url

    def init_serviceMenu(self):
        self.serviceTab = {}
        tabs = self.get_elements("div.servicesPanel > div.tabs > div.tab[aria-hidden=false]")
        for i,tab in enumerate(tabs):
            self.serviceTab[ tab.text.strip() ] = i+1

    def init_regionList(self):
        self.select_service(u'Amazon EC2')
        self.regionList = []
        # Region一覧の取得
        regions = self.get_elements("select.gwt-ListBox.CR_CHOOSE_REGION.regionListBox option")
        for region in regions :
            self.regionList.append(region.text.strip())

    def select_service(self, serviceName):
        tabs = self.get_elements("div.servicesPanel > div.tabs > div.tab[aria-hidden=false]")
        for tab in tabs:
            if serviceName ==  tab.text.strip() :    
                tab.click()
                break
        #i = self.serviceTab[serviceName]
        #self.get_element('div.servicesPanel > div.tabs > div.tab[aria-hidden=false]:nth-child(%d)' % (i)).click()
        
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

    def set_awsService(self, service_name, service_conf):
        region_text = ''
        # Regionの指定があるとき
        if 'Region' in service_conf:
            region_text=service_conf['Region']
        
        # 該当サービスを表示
        self.select_service(service_name)
        # Region選択
        self.select_region(region_text)
        
        # EC2構成情報の設定
        if ( service_name == 'Amazon EC2' ): 
            ret = self.set_ec2Service(service_conf)
        # S3構成情報の設定
        elif ( service_name == 'Amazon S3' ):
            ret = self.set_s3Service(service_conf)
        # Route53情報の設定
        elif ( service_name == 'Amazon Route 53' ):
            ret = self.set_r53Service()
        # CloudFront情報の設定
        elif ( service_name == u'Amazon CloudFront' ):
            ret = self.set_cloudfrontService()
        # RDS構成情報の設定
        elif ( service_name == 'Amazon RDS' ):
            ret = self.set_rdsService(service_conf)
        # ElastiCache情報の設定
        elif ( service_name == 'Amazon ElastiCache' ):
            ret = self.set_elasticacheService()
        # CloudWatch情報の設定
        elif ( service_name == u'Amazon CloudWatch' ):
            ret = self.set_cloudwatchService()
        # SES情報の設定
        elif ( service_name == u'Amazon SES' ):
            ret = self.set_sesService()
        # SNS情報の設定
        elif ( service_name == u'Amazon SNS' ):
            ret = self.set_snsService()
        # DirectConnect情報の設定
        elif ( service_name == u'AWS Direct Connect' ):
            ret = self.set_directconnectService()
        # VPC情報の設定
        elif ( service_name == 'Amazon VPC' ):
            ret = self.set_vpcService()
        # 未サポート
        else :
            print >>sys.stderr, service_name + ':' + region_text  + ':NotSupportedYet'
            time.sleep(1) #画面表示までちょっと待つ
        
        # スクリーンショット取得
        if self.screenshot : 
            self.get_screenshot( service_name.split(' ')[-1]+'-'+region_text.replace(' ', '') )
        
        return

    # -------------------- ElastiCache ----------------------
    def set_elasticacheService(self):
        table = self.get_element('table.service.ElastiCacheService')
        """
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
        """

        
    # -------------------- DirectConnect ----------------------
    def set_directconnectService(self):
        table = self.get_element('table.service.DirectConnectService')
        """
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
        """

     
    # -------------------- SNS ----------------------
    def set_snsService(self):
        table = self.get_element('table.service.SNSService')
        """
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
        """
 
    # -------------------- SES ----------------------
    def set_sesService(self):
        table = self.get_element('table.service.SESService')
        """
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
        """
        
    # -------------------- CloudWatch ----------------------
    def set_cloudwatchService(self):
        table = self.get_element('table.service.CloudWatchService')
        """
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
        """
        
    # -------------------- CloudFront ----------------------
    def set_cloudfrontService(self):
        table = self.get_element('table.service.CloudFrontService')
        """
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
        """

    # -------------------- Route53 ----------------------
    def set_r53Service(self):
        table = self.get_element('table.service.Route53Service')
        """
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
        """

    # -------------------- VPC ----------------------
    def set_vpcService(self):
        table = self.get_element('table.service.VPNService')
        """
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
        """

    # -------------------- RDS ----------------------
    def set_rdsService(self,conf):
        table = self.get_element('table.service.RDSService')
        region = conf['Region']
        # インスタンス
        if 'Instances' in conf : 
            for rdsconf in conf['Instances']:
                self.add_rdsInstance(rdsconf)
        # 追加のバックアップストレージ
        if 'BackupVolumes' in conf:
            for vconf in conf['BackupVolumes']:
                self.add_rdsVolume(vconf) 
        # リザーブドインスタンス
        if 'ReservedInstances' in conf :
            for rdsconf in conf['ReservedInstances']:
                self.add_rdsInstance(rdsconf,reserved=True)
        ## データ転送
        if 'DataTranfer' in conf:
            v = conf['DataTranfer']
            # リージョン間データ転送送信:
            if 'InterRegion' in v :
                self.set_val_and_type("table.dataTransferField:nth-child(1)", v['InterRegion'], table)
            # データ転送送信:
            if 'InternetSend' in v :
                self.set_val_and_type("table.dataTransferField:nth-child(2)", v['InternetSend'], table)
            # データ転送受信:
            if 'InternetReceive' in v: 
                self.set_val_and_type("table.dataTransferField:nth-child(3)", v['InternetReceive'], table)
            # リージョン内データ転送:
            if 'IntraRegion' in v:
                self.set_val_and_type("table.dataTransferField:nth-child(4)", v['IntraRegion'], table) 

    def add_rdsVolume(self, vconf):
        # 追加ボタンを押す 
        btn = self.get_element("div.Volumes table.itemsTable tr.footer div.gwt-PushButton > img[src$='add.png']")
        ActionChains(self.driver).move_to_element(btn).click(btn).perform()
        # 追加された行
        row = self.get_element('div.Volumes table>tbody>tr:nth-last-child(2)')
        self.set_val_and_type("table.SF_RDS_FIELD_BACKUP", vconf, row, int)
        
    def add_rdsInstance(self, rdsconf, reserved=False):
        divname = 'div.RDBReserved' if reserved else 'div.Instances'
        # 追加ボタンを押す 
        btn = self.get_element(divname + " tr.footer div.gwt-PushButton > img[src$='add.png']")
        ActionChains(self.driver).move_to_element(btn).click(btn).perform()
        # 追加された行
        row = self.get_element(divname + ' table>tbody>tr:nth-last-child(2)')
        # TODO: 組み合わせエラー時の処理
        # インスタンス説明
        if 'Description' in rdsconf:
            self.set_value("table.SF_RDS_INSTANCE_FIELD_DESCRIPTION input", rdsconf['Description'], row)
        # インスタンス数
        if 'Quantity' in rdsconf:
            self.set_value("table.SF_RDS_INSTANCE_FIELD_INSTANCES input", rdsconf['Quantity'], row, int)
        # 使用量
        if 'Usage' in rdsconf:
            self.set_val_and_type("table.SF_RDS_INSTANCE_FIELD_USAGE", rdsconf['Usage'], row, int)
        # DB エンジンおよびライセンス
        if 'Engine' in rdsconf:
            self.set_select('table.SF_RDS_INSTANCE_FIELD_ENGINE select', rdsconf['Engine'], row)
        # インスタンスタイプ
        if 'InstanceType' in rdsconf:
            self.set_select('table.SF_RDS_INSTANCE_FIELD_CLASS select', rdsconf['InstanceType'], row)
        # デプロイメント
        if 'Deployment' in rdsconf:
            self.set_select('table.SF_RDS_INSTANCE_FIELD_DEPLOYMENT_TYPE select', rdsconf['Deployment'], row)
        # ストレージ
        if 'Storage' in rdsconf:
            v = rdsconf['Storage']
            # タイプ
            self.set_select('table.SF_RDS_INSTANCE_FIELD_IOPS_TYPE select', v['Type'], row)
            # サイズ 
            self.set_value('table.SF_RDS_INSTANCE_FIELD_STORAGE input.numericTextBox', v['Size'], row, int)
            # IOPS
            self.set_value('table.SF_RDS_INSTANCE_FIELD_IOPS input.numericTextBox', v['Iops'], row, int)
        # Reservedの場合
        if reserved :
            if 'OfferingType' in rdsconf:
                self.set_select('table.SF_RDS_RESERVED_FIELD_PAYMENT_OPTION select', rdsconf['OfferingType'], row)
            if 'OfferingTerm' in rdsconf:
                self.set_select('table.SF_RDS_RESERVED_FIELD_TERM select', rdsconf['OfferingTerm'], row)
        #
    # --------------------- S3 ----------------------
    def set_s3Service(self, conf):
        table = self.get_element('table.service.S3Service')
        #ストレージ:
        # 通常ストレージ
        if 'StandardStorage' in conf:
            self.set_val_and_type('table.SF_S3_STORAGE', conf['StandardStorage'], table)
        # 低冗長ストレージ
        if 'ReducedRedundancy' in conf:
            self.set_val_and_type('table.SF_S3_RR_STORAGE', conf['ReducedRedundancy'], table)
        # リクエスト
        # PUT/COPY/POST/LIST リクエスト
        if 'PutCopyPostListRequests' in conf:
            self.set_value('table.SF_S3_PUT_COPY_POST_LIST_REQUESTS input', conf['PutCopyPostListRequests'], table, int)
        # GET とその他のリクエスト 
        if 'GetOtherRequests' in conf:
            self.set_value('table.SF_S3_GET_OTHER_REQUESTS input', conf['GetOtherRequests'], table, int)
        # データ転送:
        # リージョン間データ転送送信:
        if 'InterRegion' in conf:
            self.set_val_and_type('table.subSection:nth-child(3) div.subContent > table:nth-child(1)', conf['InterRegion'], table)
        # データ転送送信:
        if 'InternetSend' in conf:
            self.set_val_and_type('table.subSection:nth-child(3) div.subContent > table:nth-child(2)', conf['InternetSend'], table)
        # データ転送受信:
        if 'InternetReceive' in conf:
            self.set_val_and_type('table.subSection:nth-child(3) div.subContent > table:nth-child(3)', conf['InternetReceive'], table)
        
    # --------------------- EC2 ----------------------
    def set_ec2Service(self, conf):
        table = self.get_element('table.service.EC2Service')
        region = conf['Region']
        # Instance
        if 'Instances' in conf : 
            for ec2conf in conf['Instances']:
                self.add_ec2Instance(ec2conf,region)
        # EBS
        if 'Storages' in conf :
            for ebsconf in conf['Storages']:
                self.add_ebsVolume(ebsconf)
        # Elastic IP
        if 'ElasticIp' in conf :
            v = conf['ElasticIp']
            # 追加 Elastic IP の数
            if 'Quantity' in v :
                self.set_value("table.SF_ELASTIC_IP_NUMBER input", v['Quantity'], table, int)  
            # Elastic IP をアタッチしていない時間:
            if 'UnAttached' in v :
                self.set_val_and_type("table.SF_ELASTIC_IP_ATTACHED", v['UnAttached'], table, int)
            # Elastic IP リマップの回数:
            if 'Remaps' in v :
                self.set_val_and_type("table.SF_ELASTIC_IP_REMAPS", v['Remaps'], table, int)
        # データ転送
        if 'DataTranfer' in conf :
            v = conf['DataTranfer']
            # リージョン間データ転送送信:
            if 'InterRegion' in v :
                self.set_val_and_type("table.dataTransferField:nth-child(1)", v['InterRegion'], table)
            # データ転送送信:
            if 'InternetSend' in v :
                self.set_val_and_type("table.dataTransferField:nth-child(2)", v['InternetSend'], table)
            # データ転送受信:
            if 'InternetReceive' in v :
                self.set_val_and_type("table.dataTransferField:nth-child(3)", v['InternetReceive'], table)
            # VPC ピア接続のデータ転送:
            if 'VpnPeers' in v :
                self.set_val_and_type("table.dataTransferField:nth-child(4)", v['VpnPeers'], table)
            # リージョン内データ転送:
            if 'IntraRegion' in v :
                self.set_val_and_type("table.dataTransferField:nth-child(5)", v['IntraRegion'], table)
            # パブリック IP/Elastic IP のデータ転送:
            if 'IntraRegionEIPELB' in v :
                self.set_val_and_type("table.dataTransferField:nth-child(6)", v['IntraRegionEIPELB'], table) 
        # Elastic Load Balancing
        if 'ElasticLoadBalancing' in conf : 
            v = conf['ElasticLoadBalancing']
            # Elastic LB の数:
            if 'Quantity' in v :
                self.set_value("table.SF_ELB_DATA_NUMBER input", v['Quantity'], table, int)
            # 全 ELB によって処理されたデータ総量:
            if 'ELBTransfer' in v :
                self.set_val_and_type("table.subSection:nth-child(5) div.subContent > table:nth-child(2)", v['ELBTransfer'], table)
        
    def set_instanceType(self, ec2conf, row, region):
        self.driver.implicitly_wait(1)
        for i in range(self.RETRY): #RETRY
            # インスタンスタイプウインドウを開く
            type_div = self.get_element('div.SF_EC2_INSTANCE_FIELD_TYPE',row)
            type_div.click()
            # InstanceType一覧を取得 
            itypes = self.get_elements('div.InstanceTypeSelectorDialog table.Types > tbody > tr > td:nth-child(2) div.gwt-Label')
            if len(itypes) > 2 : 
                if region in self.ec2InstanceTypes : # キャッシュ利用
                    pass
                else: # Region別にインスタンスタイプデータをキャッシュする
                    types = {}
                    for i , itype in enumerate(itypes):
                        types[itype.text.strip()] = str(i+2)
                    self.ec2InstanceTypes[region] = types
                    break
            else: # ダイアログを開きなおす
                self.get_element('table.Buttons > tbody > tr > td:nth-child(3) > table > tbody > tr > td:nth-child(3) > button').click()
                
        # インスタンスタイプ
        if 'InstanceType' in ec2conf:
            # InstanceType設定
            cssstr = "div.InstanceTypeSelectorDialog table.Types > tbody > tr:nth-child(" + self.ec2InstanceTypes[region][ec2conf['InstanceType']] + ") > td label"
            self.get_element(cssstr).click()
        # OS
        if 'OS' in ec2conf:
            # OS一覧を取得
            lbls = self.get_elements("div.InstanceTypeSelectorDialog fieldset.SelectorDialogOS label")
            osset = {}
            for os in lbls:
                osset[os.text.strip()] = os
            # OS設定
            osset[ ec2conf['OS'] ].click()
        # EBS最適化
        if 'EbsOptimized' in ec2conf:
            self.set_checkbox("table.SF_EC2_INSTANCE_FIELD_EBS_OPTIMIZED input[type='checkbox']", ec2conf['EbsOptimized'] )
        # 詳細オプションを展開する
        btn = self.get_element("table.InstanceTypeSelectorBody > tbody > tr:nth-child(3) > td > fieldset > table > tbody > tr > td:nth-child(1) > button")
        if ( btn.text == u'表示'): btn.click()
        # 詳細モニタリング
        if 'DetailedMonitor' in ec2conf:
            self.set_checkbox("table.SF_EC2_INSTANCE_FIELD_MONITORING input[type='checkbox']", ec2conf['DetailedMonitor'] )
        # ハードウェア占有
        if 'Dedicated' in ec2conf:
            self.set_checkbox("table.SF_EC2_INSTANCE_FIELD_TENANCY input[type='checkbox']", ec2conf['Dedicated'] )
        # ダイアログを閉じる
        time.sleep(0.1)
        self.get_element('table.Buttons > tbody > tr > td:nth-child(3) > table > tbody > tr > td:nth-child(3) > button').click()
        self.driver.implicitly_wait(15)
 
    def set_instanceBilling(self, billing , row):
        # 料金計算オプションウィンドウを開く
        type_div = self.get_element('div.SF_COMMON_FIELD_BILLING',row).click()
        # 料金計算オプション 一覧を取得する
        ptypes = self.get_elements('div.InstanceBillingSelectorDialog table.Types > tbody > tr > td:nth-child(2) div.gwt-HTML')
        paytypes = {}
        for i , ptype in enumerate(ptypes):
            paytypes[ptype.text.strip()] = str(i+1)
        # 料金計算オプション 選択
        cssstr = "div.InstanceBillingSelectorDialog table.Types > tbody > tr:nth-child(" + paytypes[billing.strip()] + ") > td label"
        self.get_element(cssstr).click()
        # 料金計算オプション:閉じて保存 
        time.sleep(0.1)
        self.get_element("table.ContentContainer.InstanceSelectorContent > tbody > tr:nth-child(2) > td > table > tbody > tr > td:nth-child(3) > table > tbody > tr > td:nth-child(3) > button").click()

    def add_ec2Instance(self, ec2conf, region):
        # 追加ボタンを押す 
        btn = self.get_element("div.Instances tr.footer div.gwt-PushButton > img[src$='add.png']")
        ActionChains(self.driver).move_to_element(btn).click(btn).perform()
        # 追加された行
        row = self.get_element('table.service.EC2Service div.Instances table>tbody>tr:nth-last-child(2)')
        # インスタンス説明
        if 'Description' in ec2conf:
            self.set_value("table.SF_EC2_INSTANCE_FIELD_DESCRIPTION input", ec2conf['Description'], row)
        # インスタンス数
        if 'Quantity' in ec2conf:
            self.set_value("table.SF_EC2_INSTANCE_FIELD_INSTANCES input", ec2conf['Quantity'], row, int)
        # 使用料
        if 'Usage' in ec2conf:
           self.set_val_and_type("table.SF_EC2_INSTANCE_FIELD_USAGE", ec2conf['Usage'], row, int) 
        # Instanceタイプ ダイヤログの設定
        self.set_instanceType(ec2conf,row,region)
        # 料金計算オプション ダイヤログの設定
        if 'BillingOption' in ec2conf:
            self.set_instanceBilling( ec2conf['BillingOption'] , row)
    
    def add_ebsVolume(self, ebsconf):
        # 追加ボタンを押す 
        btn = self.get_element("table.service.EC2Service div.Volumes tr.footer div.gwt-PushButton > img[src$='add.png']")
        ActionChains(self.driver).move_to_element(btn).click(btn).perform()
        # 追加された行
        row = self.get_element("table.service.EC2Service div.Volumes table>tbody>tr.EBSVolumeRow:nth-last-child(2)")
        # Volume 説明
        if 'Description' in ebsconf:
            self.set_value("tr > td:nth-child(2) input.gwt-TextBox", ebsconf['Description'], row)
        # Volume 数
        if 'Quantity' in ebsconf:
            self.set_value("tr > td:nth-child(3) input.gwt-TextBox", ebsconf['Quantity'], row, int)
        # Volume タイプ
        if 'EBSType' in ebsconf:
            self.set_select('table.SF_EC2_EBS_FIELD_TYPE select', ebsconf['EBSType'], row)
        # Volume サイズ
        if 'Size' in ebsconf:
            self.set_value('table.SF_EC2_EBS_FIELD_STORAGE input', ebsconf['Size'], row, int)
        # Volume IOPS
        if 'Iops' in ebsconf:
            self.set_value('table.SF_EC2_EBS_FIELD_AVERAGE_IOPS input', ebsconf['Iops'], row, int)
        # Snapshot 
        if 'Snapshot' in ebsconf:
            self.set_val_and_type('table.SF_EC2_EBS_FIELD_SNAPSHOT_STORAGE', ebsconf['Snapshot'], row)

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
        estimate = self.wait.until( expected_conditions.presence_of_element_located((By.ID,'saveURL')))
        print >>sys.stderr, 'saved Url: ' +  estimate.get_attribute('href')
        return estimate.get_attribute('href')
             
    def is_member(self, target , cname):
        return cname in target.get_attribute("class").split(" ")

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

    print >>sys.stderr, args

    filename = args['<SystemConfigFile>']
    fp=open(filename,'r')
    text=fp.read()
    fp.close()
    sysconf=json.loads(text)

    output=json.dumps(sysconf, indent=4, ensure_ascii=False ).encode('utf-8')
    print output    
 
    ac = AwsSystemConfig(
        system_conf=sysconf, 
        server_url=args['<SeleniumServerURL>'],
        driver_type=args['-d'],
        file_prefix=args['-p'],
        screenshot=args['--screen'] )

    ac.setUp()
    url=ac.create_aws_estimate()
    ac.tearDown()

    print url

