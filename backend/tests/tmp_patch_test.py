from unittest.mock import patch

@patch('builtins.print')
def test_patch(mock_print):
    assert mock_print is not None
