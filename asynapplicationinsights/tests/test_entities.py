from . import Theory, cases
from ..entities import RequestData


class TestEntities(Theory):

    @cases(
        (1000 * 16 + 150, '00:00:16.150'),
        (1000 * 16 + 15, '00:00:16.015'),
        (255, '00:00:00.255'),
        (1155, '00:00:01.155'),
        (50, '00:00:00.050'),
        (5, '00:00:00.005'),
    )
    def test_request_duration_formatting(self, value, expected_format):
        formatted = RequestData.format_duration(value)
        self.assertEqual(expected_format, formatted)
