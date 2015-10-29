#!/usr/bin/env python
# -*- coding: utf-8 -*-

from base.AwsService import AwsService

class SES(AwsService):
    def set_serviceConfig(self, config):
        self.set_sesService(config)

    def get_serviceConfig(self):
        ret=self.get_sesService()
        return ret

    def get_sesService(self):
        table = self.get_element('table.service.SESService')
        # メッセージ:
        ## Eメールメッセージ:
        emails = int(self.get_value("table.SF_SES_EMAIL_MESSAGES input", table))
        # 添付ファイル:
        ## データ転送送信（添付ファイル）:
        attach_size , attach_unit = self.get_val_and_type("table.subSection:nth-child(3) div.subContent > table:nth-child(1)", table)
        # データ転送:
        ## データ転送送信:
        send_size , send_unit = self.get_val_and_type("table.subSection:nth-child(4) div.subContent > table:nth-child(1)", table)
        ## データ転送受信:
        recv_size , recv_unit = self.get_val_and_type("table.subSection:nth-child(4) div.subContent > table:nth-child(2)", table)

        return {
            'emailMessages': emails ,
            'AttachmentsOut': {
                'Value' : attach_size,
                'Type' : attach_unit
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

    def set_sesService(self,config):
        table = self.get_element('table.service.SESService')
        # メッセージ:
        ## Eメールメッセージ:
        if 'emailMessages' in config:
            self.set_value('table.SF_SES_EMAIL_MESSAGES input', int(config['emailMessages']), table)
        # 添付ファイル:
        ## データ転送送信（添付ファイル）:
        if 'AttachmentsOut' in config:
            self.set_val_and_type('table.subSection:nth-child(3) div.subContent > table:nth-child(1)', config['AttachmentsOut'], table)
        # データ転送:
        ## データ転送送信:
        if 'DataTransferOut' in config:
            self.set_val_and_type('table.subSection:nth-child(4) div.subContent > table:nth-child(1)', config['DataTransferOut'], table)
        ## データ転送受信:
        if 'DataTransferIn' in config:
            self.set_val_and_type('table.subSection:nth-child(4) div.subContent > table:nth-child(2)', config['DataTransferIn'], table)


