from datetime import datetime
from typing import Annotated

from pydantic import (
    BaseModel,
    ConfigDict,
    EmailStr,
    Field as Field,
    StringConstraints,
    computed_field as computed_field,
    field_validator as field_validator,
    model_validator as model_validator,
)

DomainString = Annotated[str, StringConstraints(max_length=255)]
NameString = Annotated[str, StringConstraints(max_length=50)]
DomainEmail = Annotated[EmailStr, StringConstraints(max_length=254)]


class BaseSchema(BaseModel):
    """
    Base schema for all pydantic models
    """

    model_config = ConfigDict(
        extra="forbid",
        from_attributes=True,
        json_encoders={datetime: lambda v: v.isoformat().replace("+00:00", "Z")},
    )