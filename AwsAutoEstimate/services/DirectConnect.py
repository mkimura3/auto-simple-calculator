#!/usr/bin/env python
# -*- coding: utf-8 -*-

from base.AwsService import AwsService
from selenium.webdriver.common.action_chains import ActionChains

class DirectConnect(AwsService):
    def set_serviceConfig(self, config):
        self.set_directconnectService(config)

    def get_serviceConfig(self):
        ret=self.get_directconnectService()
        return ret

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
                'Usage' : {
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

    def set_directconnectService(self, conf):
        table = self.get_element('table.service.DirectConnectService')
        # AWS Direct Connect のポートとロケーション
        if 'DirectConnects' in conf:
            for dconf in conf['DirectConnects']:
                self.add_directconnect(dconf)

    def add_directconnect(self, dconf):
        # 追加ボタンを押す 
        btn = self.get_element("div.Instances table.itemsTable tr.footer div.gwt-PushButton > img[src$='add.png']")
        ActionChains(self.driver).move_to_element(btn).click(btn).perform()
        # 追加された行
        row = self.get_element('div.Instances table>tbody>tr:nth-last-child(2)')
        # ポートの説明
        if 'Destciption' in dconf:
            self.set_value('table.SF_DIRECT_CONNECT_FIELD_DESCRIPTION input', dconf['Destciption'], row)
        # ポート
        if 'Quantity' in dconf:
            self.set_value('table.SF_DIRECT_CONNECT_FIELD_PORTS input', dconf['Quantity'], row, int)
        # ポート速度
        if 'PortSpeed' in dconf:
            self.set_select('table.SF_DIRECT_CONNECT_FIELD_PORTS select', dconf['PortSpeed'], row)
        # ポート使用量
        if 'Usage' in dconf:
            self.set_val_and_type('table.SF_DIRECT_CONNECT_FIELD_USAGE', dconf['Usage'], row, int)
        # ロケーション
        if 'Location' in dconf:
            self.set_select('table.SF_DIRECT_CONNECT_FIELD_LOCATION select', dconf['Location'], row)
        # データ転送受信
        if 'DataTransferIn' in dconf:
            self.set_val_and_type('tr > td.cell:nth-child(6) > table', dconf['DataTransferIn'], row)
        # データ転送送信
        if 'DataTransferOut' in dconf:
            self.set_val_and_type('tr > td.cell:nth-child(7) > table', dconf['DataTransferOut'], row)


