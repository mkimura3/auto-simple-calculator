#!/usr/bin/env python
# -*- coding: utf-8 -*-

from base.AwsService import AwsService

class Route53(AwsService):
    def set_serviceConfig(self, config):
        self.set_r53Service(config)

    def get_serviceConfig(self):
        ret=self.get_r53Service()
        return ret

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
            'HTTPSChecksInternal' : http_internal,
            'HTTPSChecksExternal' : http_external,
            'StringChecksInternal' : string_internal,
            'StringChecksExternal' : string_external,
            'FastintervalChecksInternal' : fast_internal,
            'FastintervalChecksExternal' : fast_external
        }

    def set_r53Service(self,config):
        table = self.get_element('table.service.Route53Service')
        # ホストゾーン
        #   ホストゾーン:
        if 'HostedZones' in config:
            self.set_value('table.SF_ROUTE_53_HOSTED_ZONES input' , int(config['HostedZones']) , table )
        #   標準的クエリ:
        if 'StandardQueries' in config:
            self.set_val_and_type('table.SF_ROUTE_53_STANDARD_QUERIES', config['StandardQueries'], table)
        #   レイテンシーベースルーティングクエリ:
        if 'LatencyQueries' in config:
            self.set_val_and_type('table.SF_ROUTE_53_LATENCY_QUERIES', config['LatencyQueries'], table)
        #   Geo DNS クエリ:
        if 'GEOQueries' in config:
            self.set_val_and_type('table.SF_ROUTE_53_GEO_DNS_QUERIES', config['GEOQueries'], table)
        # エンドポイントの DNS フェイルオーバーヘルスチェック
        #   Basic Checks Within AWS:
        if 'BasicChecksInternal' in config:
            self.set_value('table.SF_ROUTE_53_INTERNAL_BASIC_CHECKS input', int(config['BasicChecksInternal']), table)
        #   Basic Checks Outside of AWS:
        if 'BasicChecksExternal' in config:
            self.set_value('table.SF_ROUTE_53_EXTERNAL_BASIC_CHECKS input', int(config['BasicChecksExternal']), table)
        #   HTTPS Checks Within AWS:
        if 'HTTPSChecksInternal' in config:
            self.set_value('table.SF_ROUTE_53_INTERNAL_HTTPS_CHECKS input', int(config['HTTPSChecksInternal']), table)
        #   HTTPS Checks Outside of AWS:
        if 'HTTPSChecksExternal' in config:
            self.set_value('table.SF_ROUTE_53_EXTERNAL_HTTPS_CHECKS input', int(config['HTTPSChecksExternal']), table)
        #   String Matching Checks Within AWS:
        if 'StringChecksInternal' in config:
            self.set_value('table.SF_ROUTE_53_INTERNAL_STRINGMATCHING_CHECKS input', int(config['StringChecksInternal']), table)
        #   String Matching Checks Outside of AWS:
        if 'StringChecksExternal' in config:
            self.set_value('table.SF_ROUTE_53_EXTERNAL_STRINGMATCHING_CHECKS input', int(config['StringChecksExternal']), table)
        #   Fast Interval Checks Within AWS:
        if 'FastintervalChecksInternal' in config:
            self.set_value('table.SF_ROUTE_53_INTERNAL_FASTINTERVAL_CHECKS input', int(config['FastintervalChecksInternal']), table)
        #   Fast Interval Checks Outside of AWS:
        if 'FastintervalChecksExternal' in config:
            self.set_value('table.SF_ROUTE_53_EXTERNAL_FASTINTERVAL_CHECKS input', int(config['FastintervalChecksExternal']), table)

