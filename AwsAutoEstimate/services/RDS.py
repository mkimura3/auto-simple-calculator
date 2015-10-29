#!/usr/bin/env python
# -*- coding: utf-8 -*-

from base.AwsService import AwsService
from selenium.webdriver.common.action_chains import ActionChains

class RDS(AwsService):
    def set_serviceConfig(self, config):
        self.set_rdsService(config)

    def get_serviceConfig(self):
        ret=self.get_rdsService()
        return ret

    def get_rdsService(self):
        table = self.get_element('table.service.RDSService')
        # waitを短く
        self.driver.implicitly_wait(1)
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
        ## データ転送
        # リージョン間データ転送送信:
        interr_data, interr_type = self.get_val_and_type("table.dataTransferField:nth-child(1)",table)
        # データ転送送信:
        internet_out, internet_out_type = self.get_val_and_type("table.dataTransferField:nth-child(2)", table)
        # データ転送受信:
        internet_in, internet_in_type = self.get_val_and_type("table.dataTransferField:nth-child(3)", table)
        # リージョン内データ転送:
        intra_region, intra_region_type = self.get_val_and_type("table.dataTransferField:nth-child(4)", table)

        return {
            'Instances' : instances,
            'BackupVolumes' : volumes,
            'ReservedInstances' : rinstances,
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
                }
            }
        }

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

