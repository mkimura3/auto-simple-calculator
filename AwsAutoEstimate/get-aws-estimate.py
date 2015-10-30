#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Get a detail estimate  From AWS SIMPLE MONTHLY CALCULATOR

Usage:
    get-aws-estimate.py -u <SavedURL> -s <serverURL> [options]

Options:
    -s,--server <serverURL>    Selenium Server URL.
    -u,--url <savedURL>        Estimate Saved URL.
    -h,--help                  Show this screen.
    --version                  Show version.
    -d,--driver <driver_type>  Selenium WebDriver Type [default: FIREFOX]
    -f,--file <filename>       Output filename
    -p,--prefix <file_prefix>  ScreenshotFile prefix name [default: aws-]
    --screen                   Take Sceenshot
"""

import sys, json
from docopt import docopt
from AwsEstimate import AwsEstimate

if __name__ == "__main__":
    args = docopt(__doc__, version="0.1.0")
    print >>sys.stderr, args

    ac = AwsEstimate(
            server_url=args['--server'],
            driver_type=args['--driver'],
            file_prefix=args['--prefix']
        )
    ret = ac.getEstimate(
            saved_url=args['--url'],
            screenshot=args['--screen']
        )
    ac.tearDown()

    output=json.dumps(ret, indent=4, ensure_ascii=False ).encode('utf-8')
    if args['--file'] :
        filename = args['--file']
        fp=open(filename,'w')
        print >> fp, output
        fp.close()
    else:
        print output

