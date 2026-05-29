from __future__ import annotations

import argparse


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Deprecated legacy local-file metadata importer. Use sync_howgow_metadata.py instead."
    )
    parser.parse_args()
    raise SystemExit(
        "This legacy local-file metadata importer has been removed. "
        "Use scripts/sync_howgow_metadata.py to sync from the SQL Server ai_platform catalog."
    )


if __name__ == "__main__":
    main()
