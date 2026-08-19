from enum import StrEnum


class TemplateTypeEnum(StrEnum):
    SYSTEM = "system"
    CUSTOM = "custom"


class TemplateStatusEnum(StrEnum):
    DRAFT = "draft"
    PUBLISHED = "published"
    ARCHIVED = "archived"


class TemplateAssetTypeEnum(StrEnum):
    IMAGE = "image"
    DOCUMENT = "document"


class TemplateAssetUsageEnum(StrEnum):
    INLINE = "inline"
    ATTACHMENT = "attachment"