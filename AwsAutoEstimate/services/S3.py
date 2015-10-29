#!/usr/bin/env python
# -*- coding: utf-8 -*-

from base.AwsService import AwsService

class S3(AwsService):
    def set_serviceConfig(self, config):
        self.set_s3Service(config)

    def get_serviceConfig(self):
        ret=self.get_s3Service()
        return ret

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
        
