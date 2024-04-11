try:
    import psycopg
except ImportError:
    try:
        import psycopg2 as psycopg
    except ImportError:
        try:
            import psycopg2cffi as psycopg
        except ImportError:
            psycopg = None

try:
    from psycopg.conninfo import make_conninfo
except ImportError:
    try:
        from psycopg2.extensions import make_dsn as make_conninfo
    except ImportError:
        make_conninfo = lambda value: value  # noqa
