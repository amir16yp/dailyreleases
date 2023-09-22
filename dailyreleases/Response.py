"""Custom class mirroring requests.Response"""

import json


class Response:
    def __init__(self, byte_data: bytes = None, status_code: int = None,
                 content_type: str = None):
        self.byte_data = byte_data
        self.status_code = status_code
        self.content_type = content_type

    @classmethod
    def from_row(cls, row):
        response = cls(
            byte_data=row["response"],
            status_code=row["status_code"],
            content_type=row["content_type"]
        )
        return response

    @property
    def json(self):
        return json.loads(self.byte_data)
