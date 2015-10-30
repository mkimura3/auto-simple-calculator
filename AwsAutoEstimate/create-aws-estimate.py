#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Create Estimate Using AWS SIMPLE MONTHLY CALCULATOR

Usage:
    create-aws-estimate.py  -f <configFile> -s <serverURL> [options]

Options:
    -f,--file <configFile>     AWS SystemConfig File.
    -s,--server <serverURL>    SeleniumServer URL.
    -h,--help                  Show this screen.
    --version                  Show version.
    -d,--driver <driver_type>  Selenium WebDriver Type [default: FIREFOX]
    -p,--prefix <file_prefix>  ScreenshotFile prefix name [default: aws-]
    --screen                   Take Sceenshot
"""

import sys, json
from docopt import docopt
from AwsEstimate import AwsEstimate

if __name__ == "__main__":
    args = docopt(__doc__, version="0.1.0")
    print >>sys.stderr, args
   
    filename = args['--file']
    fp=open(filename,'r')
    text=fp.read()
    fp.close()
    sysconf=json.loads(text)

    ac = AwsEstimate(
            server_url=args['--server'],
            driver_type=args['--driver'],
            file_prefix=args['--prefix']
        )
    ret = ac.createEstimate(
            system_conf=sysconf,
            screenshot=args['--screen'] 
        )
    ac.tearDown()

    output=json.dumps(ret, indent=4, ensure_ascii=False ).encode('utf-8')
    print output 
