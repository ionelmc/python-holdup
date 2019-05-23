import pytest


def pytest_collection_modifyitems(items):
    for item in items:
        if item.name.startswith('test_func'):
            item.add_marker(pytest.mark.func)
        else:
            item.add_marker(pytest.mark.unit)
