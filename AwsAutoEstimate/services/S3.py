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
        ## Standard Storage:
        section = self.get_element('table.service.S3Service table.subSection:nth-child(1)')
        # Standard Storage:
        s3_size ,s3_size_unit = self.get_val_and_type("table.SF_S3_STORAGE", section)
        # PUT/COPY/POST/LIST リクエスト
        s3_req_put = int(self.get_value("table.SF_S3_PUT_COPY_POST_LIST_REQUESTS input", section))
        # GET とその他のリクエスト 
        s3_req_get =int(self.get_value("table.SF_S3_GET_OTHER_REQUESTS input", section))
        
        ## Standard - Infrequent Access Storage:
        section = self.get_element('table.service.S3Service table.subSection:nth-child(2)')
        # Infrequent Access Storage:
        ia_size ,ia_size_unit = self.get_val_and_type("table.SF_S3_IA_STORAGE", section)
        # PUT/COPY/POST/LIST リクエスト
        ia_req_put = int(self.get_value("table.SF_S3_PUT_COPY_POST_LIST_REQUESTS input", section))
        # GET とその他のリクエスト 
        ia_req_get =int(self.get_value("table.SF_S3_GET_OTHER_REQUESTS input", section))
        # Lifecycle Transitions
        ia_transitions = int(self.get_value("table.SF_S3_LIFECYCLE_TRANSITION_REQUESTS input", section))
        # Data Retrieval
        ia_retrieval ,ia_retrieval_unit = self.get_val_and_type("table.SF_S3_DATA_RETRIEVALS", section)        

        ## Reduced Redundancy Storage:
        section = self.get_element('table.service.S3Service table.subSection:nth-child(3)')
        # 低冗長化ストレージ:
        rr_size ,rr_size_unit = self.get_val_and_type("table.SF_S3_RR_STORAGE", section)
        # PUT/COPY/POST/LIST リクエスト
        rr_req_put = int(self.get_value("table.SF_S3_PUT_COPY_POST_LIST_REQUESTS input", section))
        # GET とその他のリクエスト 
        rr_req_get =int(self.get_value("table.SF_S3_GET_OTHER_REQUESTS input", section))

        # データ転送:
        section = self.get_element('table.service.S3Service table.subSection:nth-child(4)')
        # リージョン間データ転送送信:
        inter_region , inter_region_type = self.get_val_and_type("div.subContent > table:nth-child(1)", section)
        # データ転送送信:
        internet_out , internet_out_type = self.get_val_and_type("div.subContent > table:nth-child(2)", section)
        # データ転送受信:
        internet_in , internet_in_type = self.get_val_and_type("div.subContent > table:nth-child(3)", section)

        return {
            'StandardStorage': {
                'Size' : {
                    'Value' : s3_size,
                    'Type' : s3_size_unit
                },
                'PutCopyPostListRequests' : s3_req_put,
                'GetOtherRequests' : s3_req_get,
            },
            'InfrequentAccessStorage': {
                'Size' : {
                    'Value' : ia_size,
                    'Type' : ia_size_unit
                },
                'PutCopyPostListRequests' : ia_req_put,
                'GetOtherRequests' : ia_req_get,
                'LifecycleTransitions' : ia_transitions,
                'DataRetrieval' : {
                    'Value' : ia_retrieval,
                    'Type' : ia_retrieval_unit
                }
            },
            'ReducedRedundancy': {
                'Size' : {
                    'Value' : rr_size,
                    'Type' : rr_size_unit
                },
                'PutCopyPostListRequests' : rr_req_put,
                'GetOtherRequests' : rr_req_get
            },
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
        ## Standard - Infrequent Access Storage:
        section = self.get_element('table.service.S3Service table.subSection:nth-child(1)')
        if 'StandardStorage' in conf:
            s = conf['StandardStorage']
            # Standard Storage:
            self.set_val_and_type('table.SF_S3_STORAGE', s['Size'], section)
            # PUT/COPY/POST/LIST リクエスト
            self.set_value('table.SF_S3_PUT_COPY_POST_LIST_REQUESTS input', s['PutCopyPostListRequests'], section, int)
            # GET とその他のリクエスト
            self.set_value('table.SF_S3_GET_OTHER_REQUESTS input', s['GetOtherRequests'], section, int)
        ## Standard - Infrequent Access Storage:
        section = self.get_element('table.service.S3Service table.subSection:nth-child(2)')
        if 'InfrequentAccessStorage' in conf:
            s = conf['InfrequentAccessStorage']
            # Infrequent Access Storage:
            self.set_val_and_type('table.SF_S3_IA_STORAGE', s['Size'], section)
            # PUT/COPY/POST/LIST リクエスト
            self.set_value('table.SF_S3_PUT_COPY_POST_LIST_REQUESTS input', s['PutCopyPostListRequests'], section, int)
            # GET とその他のリクエスト
            self.set_value('table.SF_S3_GET_OTHER_REQUESTS input', s['GetOtherRequests'], section, int)
            # Lifecycle Transitions
            self.set_value('table.SF_S3_LIFECYCLE_TRANSITION_REQUESTS input', s['LifecycleTransitions'], section, int)
            # Data Retrieval
            self.set_val_and_type('table.SF_S3_DATA_RETRIEVALS', s['DataRetrieval'], section)
        ## Reduced Redundancy Storage
        section = self.get_element('table.service.S3Service table.subSection:nth-child(3)')
        if 'ReducedRedundancy' in conf:
            s = conf['ReducedRedundancy']
            # 低冗長化ストレージ:
            self.set_val_and_type('table.SF_S3_RR_STORAGE', s['Size'], section)
            # PUT/COPY/POST/LIST リクエスト
            self.set_value('table.SF_S3_PUT_COPY_POST_LIST_REQUESTS input', s['PutCopyPostListRequests'], section, int)
            # GET とその他のリクエスト
            self.set_value('table.SF_S3_GET_OTHER_REQUESTS input', s['GetOtherRequests'], section, int)
        # データ転送:
        section = self.get_element('table.service.S3Service table.subSection:nth-child(4)')
        # リージョン間データ転送送信:
        if 'InterRegion' in conf:
            self.set_val_and_type('div.subContent > table:nth-child(1)', conf['InterRegion'], section)
        # データ転送送信:
        if 'InternetSend' in conf:
            self.set_val_and_type('div.subContent > table:nth-child(2)', conf['InternetSend'], section)
        # データ転送受信:
        if 'InternetReceive' in conf:
            self.set_val_and_type('div.subContent > table:nth-child(3)', conf['InternetReceive'], section)
        
