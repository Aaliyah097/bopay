import datetime
from typing import Any

import ulid
from sqlalchemy import Column, DateTime, String
from sqlalchemy.ext.declarative import as_declarative


@as_declarative()
class Base:
    id = Column(String(26), primary_key=True, default=lambda: str(ulid.new()))
    created_at = Column(DateTime, insert_default=datetime.datetime.now)
    updated_at = Column(DateTime, onupdate=datetime.datetime.now)

    def to_dict(self, exclude_fields: list[str] | None = None) -> dict[str, Any]:
        if not exclude_fields:
            exclude_fields = []
        # pylint: disable=E1101
        return {
            column.name: getattr(self, column.name)
            for column in self.__table__.columns  # type: ignore
            if column.name not in exclude_fields
        }
