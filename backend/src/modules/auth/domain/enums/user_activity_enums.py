from enum import StrEnum


class UserActivityTypeEnum(StrEnum):
    PROFILE_UPDATED = "profile_updated"
    PASSWORD_CHANGED = "password_changed"
    TWO_FA_ENABLED = "2fa_enabled"
    TWO_FA_DISABLED = "2fa_disabled"
    TWO_FA_CHALLENGE = "2fa_challenge"
    SUSPICIOUS_LOGIN = "suspicious_login"
