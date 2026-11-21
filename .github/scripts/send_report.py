"""Validate and submit the course-generated report without changing its results."""

import json
import os
from pathlib import Path
import sys
from urllib.error import HTTPError
from urllib.request import Request, urlopen


def main():
    secret = os.environ.get("ES_ACCOUNT_SECRET", "").strip()
    if not secret:
        raise SystemExit("ES_ACCOUNT_SECRET is missing")
    if "\n" in secret or "\r" in secret:
        raise SystemExit("ES_ACCOUNT_SECRET must contain only the account token, without line breaks")
    report = json.loads(Path(os.environ["REPORT"]).read_text(encoding="utf-8-sig"))
    if not isinstance(report, dict):
        raise SystemExit("The course report must be a JSON object")
    payload = json.dumps(report, ensure_ascii=True, allow_nan=False).encode("ascii")
    print(f"Validated report: task={report.get('task')}, status={report.get('status')}, bytes={len(payload)}", flush=True)
    request = Request(
        "https://es.ant-lab.ru/api/results/",
        data=payload,
        headers={"Authorization": f"Bearer {secret}", "Content-Type": "application/json; charset=utf-8", "Accept": "application/json"},
        method="POST",
    )
    try:
        with urlopen(request, timeout=60) as response:
            status = response.status
            body = response.read().decode("utf-8")
    except HTTPError as error:
        status = error.code
        body = error.read().decode("utf-8", errors="replace")
    print(f"ant-lab HTTP {status}")
    print(body.replace(secret, "***"))
    if not 200 <= status < 300:
        raise SystemExit(1)
    result = json.loads(body)
    if result.get("ok") is not True:
        raise SystemExit("ant-lab did not confirm acceptance of the report")


if __name__ == "__main__":
    main()
