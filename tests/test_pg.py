#!/usr/bin/python3
if __name__ == "__main__":
    import sys
    import traceback

    import psycopg2

    try:
        conn = psycopg2.connect("postgresql://app:app@pg:5432/app")
        cursor = conn.cursor()
        cursor.execute("SELECT version()")
        print(cursor.fetchone())
    except Exception:
        traceback.print_exc()
        sys.exit(1)
