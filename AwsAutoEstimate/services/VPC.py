#!/usr/bin/env python
# -*- coding: utf-8 -*-

from base.AwsService import AwsService
from selenium.webdriver.common.action_chains import ActionChains

class VPC(AwsService):
    def set_serviceConfig(self, config):
        self.set_vpcService(config)

    def get_serviceConfig(self):
        ret=self.get_vpcService()
        return ret

    def get_vpcService(self):
        table = self.get_element('table.service.VPNService')
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

    def set_vpcService(self,config):
        # インスタンス
        if 'VPCConnections' in config:
            for vconf in config['VPCConnections']:
                self.add_vpc(vconf)

    def add_vpc(self, vconf):
        # 追加ボタンを押す 
        btn = self.get_element("div.VPNConnections table.itemsTable tr.footer div.gwt-PushButton > img[src$='add.png']")
        ActionChains(self.driver).move_to_element(btn).click(btn).perform()
        # 追加された行
        row = self.get_element('div.VPNConnections table>tbody>tr:nth-last-child(2)')
        # VPC説明
        if 'Description' in vconf:
            self.set_value('table.SF_VPC_FIELD_DESCRIPTION input', vconf['Description'], row)
        # 接続数
        if 'Quantity' in vconf:
            self.set_value('table.SF_VPC_FIELD_INSTANCES input', int(vconf['Quantity']), row)
        # 使用量
        if 'Usage' in vconf:
            self.set_val_and_type('table.SF_VPC_FIELD_USAGE', vconf['Usage'], row, int)
        # データ転送送信
        if 'DataCenterSend' in vconf:
            self.set_val_and_type('tr>td.cell:nth-child(5)>table.dataTransferField.amountField', vconf['DataCenterSend'], row)
        # データ転送受信
        if 'DataCenterReceive' in vconf:
            self.set_val_and_type('tr>td.cell:nth-child(6)>table.dataTransferField.amountField', vconf['DataCenterReceive'], row)


