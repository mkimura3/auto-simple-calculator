#!/usr/bin/env python
# -*- coding: utf-8 -*-

from base.AwsService import AwsService

class SNS(AwsService):
    def set_serviceConfig(self, config):
        self.set_snsService(config)

    def get_serviceConfig(self):
        ret=self.get_snsService()
        return ret

    def get_snsService(self):
        table = self.get_element('table.service.SNSService')
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
                'Value' : notify_size,
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

    def set_snsService(self,config):
        table = self.get_element('table.service.SNSService')
        # リクエストと通知:
        ## リクエスト:
        if 'Requests' in config:
            self.set_value('table.SF_SNS_REQUESTS input', int(config['Requests']), table)
        ## 通知:
        if 'Notifications' in config :
            self.set_val_and_type('table.SF_SNS_NOTIFICATIONS', config['Notifications'], table, int)
        # データ転送:
        ## データ転送送信
        if 'DataTransferOut' in config:
            self.set_val_and_type('table.subSection:nth-child(3) div.subContent > table:nth-child(1)', config['DataTransferOut'], table)
        ## データ転送受信
        if 'DataTransferIn' in config:
            self.set_val_and_type('table.subSection:nth-child(3) div.subContent > table:nth-child(2)', config['DataTransferIn'], table)

