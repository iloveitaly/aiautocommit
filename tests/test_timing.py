from unittest.mock import patch

from aiautocommit.timing import log_execution_time


def test_logs_rounded_execution_time_without_timing_in_message():
    with (
        patch("aiautocommit.timing.perf_counter", side_effect=[1.0, 1.123456]),
        patch("aiautocommit.timing.log.debug") as mock_debug,
    ):
        with log_execution_time("example"):
            pass

    mock_debug.assert_called_once_with(
        "example",
        execution_time=0.1235,
        function_name="example",
    )
