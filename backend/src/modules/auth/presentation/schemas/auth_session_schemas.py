from src.shared.schemas.base_schema import BaseSchema, DomainString


class RevokeSessionRequest(BaseSchema):
    session_uuid: DomainString
