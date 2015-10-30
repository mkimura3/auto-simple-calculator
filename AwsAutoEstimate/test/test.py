#!/usr/bin/env python
# -*- coding: utf-8 -*-
import sys, json
sys.path.append('../')
from AwsEstimate import AwsEstimate
def pp(obj):
    if isinstance(obj, list) or isinstance(obj, dict):
        orig = json.dumps(obj, indent=4)
        print eval("u'''%s'''" % orig).encode('utf-8')
    else:
        print obj.encode('utf-8')

def estimate_test(testset, server_url):
    for testdata in testset:
        # get
        estimate = AwsEstimate(server_url,'FIREFOX')
        estimate_json = estimate.getEstimate( testdata['saved_url'] , False )
        pp(estimate_json)
        print '-- Assert getEstimate: ' + testdata['comment']
        assert testdata['total'] == estimate_json['Estimate']['Total']
        # create
        ret = estimate.createEstimate(estimate_json)
        pp(ret)
        estimate.tearDown()
        estimate = None
        print '-- Assert createEstimate: ' + testdata['comment']
        assert testdata['total'] == ret['Estimate']['Total']

if __name__ == "__main__":
    server_url = 'http://192.168.56.1:4444/wd/hub'
    testset = [
        { 
            'comment' : 'EC2',
            'saved_url' : 'http://calculator.s3.amazonaws.com/index.html?lng=ja_JP#r=NRT&s=EC2&key=calc-587725AF-E201-40AF-A958-9546EC6F731A',
            'total' : 3716.00 + 4387.37
        },
        { 
            'comment' : 'EBS',
            'saved_url' : 'http://calculator.s3.amazonaws.com/index.html?lng=ja_JP#r=NRT&s=EC2&key=calc-8E6E0D83-5345-4D17-A984-47ADAF573D98',
            'total' : 417.81
        },
        { 
            'comment' : 'RDS',
            'saved_url' : 'http://calculator.s3.amazonaws.com/index.html?lng=ja_JP#r=NRT&s=RDS&key=calc-8003D1CC-2CE9-4824-90A0-F56EC75CB69E',
            'total' : 19437.00 + 4406.98
        },
        {
            'comment' : 'S3',
            'saved_url' : 'http://calculator.s3.amazonaws.com/index.html?lng=ja_JP#r=NRT&s=S3&key=calc-098AC36A-79EE-4477-8370-44C368D0CD3F',
            'total' : 5900.12
        },
        {
            'comment' : 'Direct Connect',
            'saved_url' : 'http://calculator.s3.amazonaws.com/index.html?lng=ja_JP#r=NRT&s=DirectConnect&key=calc-D2EE544E-1B4B-4DCA-8678-5E562309B192',
            'total' : 1115.66
        },
        {
            'comment' : 'AWS Support(ビジネス）',
            'saved_url' : 'http://calculator.s3.amazonaws.com/index.html?lng=ja_JP#r=NRT&s=S3&key=calc-DC87182F-13E2-434D-866A-F7F892595250',
            'total' : 6726.17 + 347.6
        },
        {
            'comment' : 'AWS CloudWatch',
            'saved_url' : 'http://calculator.s3.amazonaws.com/index.html?lng=ja_JP#r=NRT&s=CloudWatch&key=calc-261008C0-FAF2-47EA-B1BD-EDBDB127DEDC',
            'total' : 36.10
        },
        {
            'comment' : 'SNS',
            'saved_url' : 'http://calculator.s3.amazonaws.com/index.html?lng=ja_JP#r=NRT&s=SNS&key=calc-555019E5-2589-401F-B098-70F454C9A5D9',
            'total' : 136.18
        },
        {
            'comment' : 'SES',
            'saved_url' : 'http://calculator.s3.amazonaws.com/index.html?lng=ja_JP#r=NRT&s=SES&key=calc-611AB6E3-401A-4620-9C79-26B7FF478D9D',
            'total' : 383.61
        },
        { 
            'comment' : 'VPC',
            'saved_url' : 'http://calculator.s3.amazonaws.com/index.html?lng=ja_JP#r=NRT&s=VPN&key=calc-8DAEBF00-F6B3-459A-8A61-2981DCA072A4',
            'total' : 117.71
        },
        {
            'comment' : 'Route53',
            'saved_url' : 'http://calculator.s3.amazonaws.com/index.html?lng=ja_JP#r=NRT&s=Route53&key=calc-627A14A6-4736-4E20-A742-6222D26EBA74',
            'total' : 1501.03
        },
        {
            'comment' : 'CloudFront',
            'saved_url' : 'http://calculator.s3.amazonaws.com/index.html?lng=ja_JP#s=CloudFront&key=calc-12E9C394-CD29-4FB9-A1EB-AE80620FD05A',
            'total' : 1305.94
        },
        {
            'comment' : 'ElastiCache',
            'saved_url' : 'http://calculator.s3.amazonaws.com/index.html?lng=ja_JP#s=ElastiCache&key=calc-BD063041-A765-4DB6-BD0B-0A92BC22DBD7&r=NRT',
            'total' : 1844.00 + 726.86
        }
    ]

    estimate_test(testset, server_url)

