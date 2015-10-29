#!/usr/bin/env python
# -*- coding: utf-8 -*-

from base.AwsService import AwsService
from selenium.webdriver.common.action_chains import ActionChains

class ElastiCache(AwsService):
    def set_serviceConfig(self, config):
        self.set_elasticacheService(config)

    def get_serviceConfig(self):
        ret=self.get_elasticacheService()
        return ret

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
                    'Type' : usage_type
                },
                'NodeType' : node_type
            }
            ondemandnodes.append(node)
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
                    'Type' : usage_type
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

    def set_elasticacheService(self, config):
        table = self.get_element('table.service.ElastiCacheService')
        # キャッシュクラスター: オンデマンドキャッシュノード:
        if 'OnDemandNodes' in config :
            for caconf in config['OnDemandNodes']:
                self.add_cacheCluster(caconf)
        #キャッシュクラスター: リザーブドキャッシュノード:
        if 'ReservedNodes' in config :
            for caconf in config['ReservedNodes']:
                self.add_cacheCluster(caconf,reserved=True)

    def add_cacheCluster(self, conf, reserved=False):
        divname = 'div.ReservedNodes' if reserved else 'div.Nodes'
        # 追加ボタンを押す 
        btn = self.get_element(divname + " tr.footer div.gwt-PushButton > img[src$='add.png']")
        ActionChains(self.driver).move_to_element(btn).click(btn).perform()
        # 追加された行
        row = self.get_element(divname + ' table>tbody>tr:nth-last-child(2)')
        # クラスター名
        if 'Description' in conf:
            self.set_value('table.SF_EC_FIELD_DESCRIPTION input', conf['Description'], row)
        # ノード数
        if 'Quantity' in conf:
            self.set_value('table.SF_EC_FIELD_NODES input', int(conf['Quantity']), row)
        # 使用量
        if 'Usage' in conf:
            self.set_val_and_type('table.SF_EC_FIELD_USAGE', conf['Usage'], row, int)
        # ノードタイプ
        if 'NodeType' in conf:
            self.set_select('table.SF_EC_FIELD_NODE_TYPE select', conf['NodeType'], row)
        # Reservedの場合
        if reserved :
            # 提供内容
            if 'OfferingType' in conf:
                self.set_select('table.SF_EC2_RESERVED_FIELD_UTILIZATION select', conf['OfferingType'], row)
            # 提供期間
            if 'OfferingTerm' in conf:
                self.set_select('table.SF_EC2_RESERVED_FIELD_TERM select', conf['OfferingTerm'], row)

