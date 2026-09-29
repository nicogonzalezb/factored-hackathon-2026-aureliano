"""python -m lbank <download|pipeline|dq|eda|all> [args]"""
import sys

from . import download, dq, eda, pipeline

CMDS = {"download": download.main, "pipeline": pipeline.main, "dq": dq.main, "eda": eda.main}


def main() -> int:
    if len(sys.argv) < 2 or sys.argv[1] not in (*CMDS, "all"):
        print(__doc__)
        return 2
    cmd, rest = sys.argv[1], sys.argv[2:]
    if cmd == "all":
        for step in ("pipeline", "dq", "eda"):
            rc = CMDS[step]([])
            if rc:
                return rc
        return 0
    return CMDS[cmd](rest)


raise SystemExit(main())
