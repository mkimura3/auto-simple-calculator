#!/usr/bin/env python
# -*- coding: utf-8 -*-

from base.AwsService import AwsService
from selenium.webdriver.common.action_chains import ActionChains

class CloudWatch(AwsService):
    def set_serviceConfig(self, config):
        self.set_cloudwatchService(config)

    def get_serviceConfig(self):
        ret=self.get_cloudwatchService()
        return ret

    def get_cloudwatchService(self):
        table = self.get_element('table.service.CloudWatchService')
        # カスタムメトリクス
        custmetrics = []
        rows = self.get_elements('div.CustomMetrics table.itemsTable tr.CloudWatchMetricsRow.itemsTableDataRow', table)
        for row in rows:
            # 説明
            desc = self.get_value("table.SF_CW_FIELD_DESCRIPTION input", row)
            # リソース数
            resources = int(self.get_value("table.SF_CW_FIELD_RESOURCES input", row))
            # カスタムメトリクス数
            metrics = int(self.get_value("table.SF_CW_FIELD_CUSTOM_METRICS input", row))
            # メトリックデータの頻度
            frequency = self.get_selectedText(self.get_element("table.SF_CW_FIELD_METRICS_FREQUENCY select",row))
            # リソースあたりのアラーム
            alarms = int(self.get_value("table.SF_CW_FIELD_ALARMS input", row))
            # 取り込まれたログのサイズ
            ingested_log = int(self.get_value("table.SF_CW_FIELD_ARCHIVED_LOGS input", row))
            # アーカイブされたログのサイズ
            archived_log = int(self.get_value("table.SF_CW_FIELD_INGESTED_LOGS input", row))
            cust = {
                'Description' : desc,
                'Resources' : resources,
                'CustomMetrics' : metrics,
                'Frequency' : frequency,
                'Alarms' : alarms,
                'IngestedLogSize' : ingested_log,
                'ArchivedLogSize' : archived_log
            }
            custmetrics.append(cust)
        #  アラーム
        ## EC2 インスタンス
        ec2_alarms = int(self.get_value("table.SF_CW_EC2_ALARMS input", table))
        ## Elastic Load Balancing
        elb_alarms = int(self.get_value("table.SF_CW_ELB_ALARMS input", table))
        ## EBS ボリューム
        ebs_alarms = int(self.get_value("table.SF_CW_EBS_ALARMS input", table))
        ## RDS DB インスタンス
        rds_alarms = int(self.get_value("table.SF_CW_RDS_ALARMS input", table))
        ## Auto Scaling 
        as_alarms = int(self.get_value("table.SF_CW_AS_ALARMS input", table))

        return {
            'CustomMetrics' : custmetrics,
            'EC2Alarms' : ec2_alarms,
            'ELBAlarms' : elb_alarms,
            'EBSAlarms' : ebs_alarms,
            'RDSAlarms' : rds_alarms,
            'AutoScalingAlarms' : as_alarms
        }

    def set_cloudwatchService(self, conf):
        table = self.get_element('table.service.CloudWatchService')
        if 'CustomMetrics' in conf:
            for cm in conf['CustomMetrics']:
                self.add_cloudwatchMetric(cm)
        ## アラーム:
        ## EC2 インスタンス
        if 'EC2Alarms' in conf:
            self.set_value('table.SF_CW_EC2_ALARMS input', conf['EC2Alarms'], table, int)
        ## Elastic Load Balancing
        if 'ELBAlarms' in conf:
            self.set_value('table.SF_CW_ELB_ALARMS input', conf['ELBAlarms'], table, int)
        ## EBS ボリューム
        if 'EBSAlarms' in conf:
            self.set_value('table.SF_CW_EBS_ALARMS input', conf['EBSAlarms'], table, int)
        ## RDS DB インスタンス
        if 'RDSAlarms' in conf:
            self.set_value('table.SF_CW_RDS_ALARMS input', conf['RDSAlarms'], table, int)
        ## Auto Scaling 
        if 'AutoScalingAlarms' in conf:
            self.set_value('table.SF_CW_AS_ALARMS input', conf['AutoScalingAlarms'], table, int)

    def add_cloudwatchMetric(self, metric):
        # 追加ボタンを押す 
        btn = self.get_element("div.CustomMetrics table.itemsTable tr.footer div.gwt-PushButton > img[src$='add.png']")
        ActionChains(self.driver).move_to_element(btn).click(btn).perform()

        # 追加された行
        row = self.get_element('div.CustomMetrics table>tbody>tr:nth-last-child(2)')
        # 説明
        if 'Destciption' in metric:
            self.set_value('table.SF_CW_FIELD_DESCRIPTION input', metric['Destciption'], row)
        # AWS リソース
        if 'Resources' in metric:
            self.set_value('table.SF_CW_FIELD_RESOURCES input', metric['Resources'], row, int)
        # カスタムメトリクス数
        if 'CustomMetrics' in metric:
            self.set_value('table.SF_CW_FIELD_CUSTOM_METRICS input', metric['CustomMetrics'], row, int)
        # メトリックデータの頻度
        if 'Frequency' in metric:
            self.set_select('table.SF_CW_FIELD_METRICS_FREQUENCY select', metric['Frequency'], row)
        # リソースあたりのアラーム
        if 'Alarms' in metric:
            self.set_value('table.SF_CW_FIELD_ALARMS input', metric['Alarms'], row, int)
        # 取り込まれたログのサイズ
        if 'IngestedLogSize' in metric :
            self.set_value('table.SF_CW_FIELD_ARCHIVED_LOGS input', metric['IngestedLogSize'] , row, int)
        # アーカイブされたログのサイズ
        if 'ArchivedLogSize' in metric:
            self.set_value('table.SF_CW_FIELD_INGESTED_LOGS input', metric['ArchivedLogSize'] , row, int)

