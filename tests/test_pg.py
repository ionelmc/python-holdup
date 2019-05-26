#!/usr/bin/python3 -u
if __name__ == "__main__":
    import sys
    import time
    import traceback

    import psycopg2

    start = time.time()
    failed = False

    while time.time() - start < 10:
        print("Connecting ...")
        try:
            conn = psycopg2.connect("postgresql://app:app@pg:5432/app")
            cursor = conn.cursor()
            cursor.execute("SELECT version()")
            print(cursor.fetchone())
        except Exception:
            traceback.print_exc()
            failed = True
        else:
            print("Connected!")
            break

    if failed:
        print("Failed!")
        sys.exit(1)
