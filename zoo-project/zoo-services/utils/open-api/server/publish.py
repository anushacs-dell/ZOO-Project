#!/usr/bin/python3
#
# Author : Gérald Fenoy
#
# Copyright 2020-2023 GeoLabs SARL. All rights reserved.
#
# Permission is hereby granted, free of charge, to any person obtaining a
# copy of this software and associated documentation files (the
# "Software"), to deal in the Software without restriction, including with
# out limitation the rights to use, copy, modify, merge, publish,
# distribute, sublicense, and/or sell copies of the Software, and to
# permit persons to whom the Software is furnished to do so, subject to
# the following conditions:
#
# The above copyright notice and this permission notice shall be included
# in all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS
# OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
# MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.
# IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY
# CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT,
# TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE
# SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
#

import os
import sys
import redis
import json
from urllib import parse

try:
    data = sys.stdin.read()
except Exception as e:
    print(e, file=sys.stderr)
    data = "{}"

print("Content-Type: text/html")
print("")

try:
    params = parse.parse_qs(os.environ.get("QUERY_STRING", ""))
    jobid = params.get("jobid", ["unknown-job"])[0]

    # connect to redis
    redis_host = os.environ.get("ZOO_REDIS_HOST", "redis")
    r = redis.Redis(host=redis_host, port=6379, db=0)

    payload = None
    try:
        payload = json.loads(data)
    except Exception:
        payload = {"raw": data}


    payload["jobID"] = jobid

    # detect "final result" (OGC style result document)
    if any(k in payload for k in ("a", "b", "c")):
        outputs = {k: payload[k] for k in ("a", "b", "c") if k in payload}

        payload = {
            "jobID": jobid,
            "status": "succeeded",
            "progress": 100,
            "message": "Completed successfully",
            "outputs": outputs,
        }

    # detect error
    if "error" in payload:
        payload["status"] = "failed"
        payload["progress"] = 100

    # publish cleaned JSON
    r.publish(jobid, json.dumps(payload))

except Exception as e:
    print("Publish error:", e, file=sys.stderr)


