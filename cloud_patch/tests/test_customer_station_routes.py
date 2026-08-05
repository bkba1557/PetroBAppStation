from app.customer_api.stations import _duration_seconds


def test_google_duration_is_converted_to_whole_seconds():
    assert _duration_seconds("901.6s") == 902


def test_invalid_google_duration_is_safe():
    assert _duration_seconds(None) == 0
    assert _duration_seconds("invalid") == 0
