#!/usr/bin/env python
# -*- coding: utf-8 -*-

from base.AwsService import AwsService

class CloudFront(AwsService):
    def set_serviceConfig(self, config):
        self.set_cloudFrontService(config)

    def get_serviceConfig(self):
        ret=self.get_cloudFrontService()
        return ret

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

    def set_cloudfrontService(self,config):
        table = self.get_element('table.service.CloudFrontService')
        # データ転送送信:
        #   毎月のボリューム:
        if 'MonthlyVolume' in config:
            self.set_val_and_type('div.body > table.subSection:nth-child(1) div.subContent table.amountField', config['MonthlyVolume'], table )
        # リクエスト:
        #   平均オブジェクトサイズ:
        if 'AverageObjectSize' in config:
            self.set_value('table.SF_CLOUD_FRONT_AVERAGE_OBJECT_SIZE input', int(config['AverageObjectSize']), table)
        #   リクエストのタイプ:
        if 'RequestType' in config:
            if config['RequestType'] == 'HTTP' :
                rd_http = self.get_element("table.SF_CLOUD_FRONT_TYPE_OF_REQUESTS td.Column0 input[type='radio']",table)
                rd_http.click()
            elif config['RequestType'] == 'HTTPS':
                rd_ssl  = self.get_element("table.SF_CLOUD_FRONT_TYPE_OF_REQUESTS td.Column1 input[type='radio']",table)
                rd_ssl.click()
        #   無効化リクエスト:
        if 'InvalidationRequests' in config:
            self.set_value('table.SF_CLOUD_FRONT_INVALIDATION_REQUESTS input', int(config['InvalidationRequests']), table)
        # エッジロケーションのトラフィックディストリビューション:
        if 'EdgeLocationDistribution' in config:
            edge = config['EdgeLocationDistribution']
            #   米国
            self.set_value('table.SF_CLOUD_FRONT_TIER_US input', int(edge['US']), table)
            #   欧州
            self.set_value('table.SF_CLOUD_FRONT_TIER_EU input', int(edge['EU']), table)
            #   香港、フィリピン、韓国、シンガポールおよび台湾
            self.set_value('table.SF_CLOUD_FRONT_TIER_HK input', int(edge['HK']), table)
            #   日本
            self.set_value('table.SF_CLOUD_FRONT_TIER_JP input', int(edge['JP']), table)
            #   南米
            self.set_value('table.SF_CLOUD_FRONT_TIER_SA input', int(edge['SA']), table)
            #   オーストラリア
            self.set_value('table.SF_CLOUD_FRONT_TIER_AU input', int(edge['AU']), table)
            #   インド
            self.set_value('table.SF_CLOUD_FRONT_TIER_IN input', int(edge['IN']), table)
        # 専用 IP SSL 証明書:
        #   証明書の数:
        if 'CustomCertificates' in config:
            self.set_value('table.SF_CLOUD_FRONT_CUSTOM_SSL_CERTS input', int(config['CustomCertificates']), table)

