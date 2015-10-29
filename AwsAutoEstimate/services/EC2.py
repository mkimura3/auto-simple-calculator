#!/usr/bin/env python
# -*- coding: utf-8 -*-

from base.AwsService import AwsService
from selenium.webdriver.common.action_chains import ActionChains
import re
from time import sleep

class EC2(AwsService):
    ec2InstanceTypes = {}

    def set_serviceConfig(self, config):
        self.set_ec2Service(config)

    def get_serviceConfig(self):
        ret=self.get_ec2Service()
        return ret
        
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
        sleep(0.1)
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
        sleep(0.1)
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
                'Snapshot' : {
                    'Type' : snap_type,
                    'Value' : snap_size
                }
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
        # 
        return {
                'OS': instance_os,
                'InstanceType' : instance_type,
                'EbsOptimized' : instance_ebsopt,
                'DetailedMonitor' : instance_monitor,
                'Dedicated' : instance_tenancy
            }

