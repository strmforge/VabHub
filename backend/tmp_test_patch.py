from unittest.mock import patch

@patch('math.ceil')
def test_simple(mock_ceiling):
    assert True
