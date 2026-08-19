import asyncio
import json
import os
import subprocess
import sys
from datetime import UTC, datetime
from typing import Any


BACKEND_CONTAINER = "mail-tracko-local-backend-1"
CONTAINER_SEED_PATH = (
    "scripts/seed/emailtemplates/"
    "seed_sys_template_and_category.py"
)


def run_inside_backend_container() -> None:
    """
    The command is started from the host machine, but the actual seed
    executes inside the backend container using its working database
    connection.
    """
    if os.getenv("MAILTRACKO_EMAIL_TEMPLATE_SEED_CONTAINER") == "1":
        return

    print("Running email-template seed inside backend container...")

    result = subprocess.run(
        [
            "docker",
            "exec",
            "-e",
            "MAILTRACKO_EMAIL_TEMPLATE_SEED_CONTAINER=1",
            BACKEND_CONTAINER,
            "sh",
            "-lc",
            (
                "cd /app && "
                "PYTHONPATH=/app "
                f"python {CONTAINER_SEED_PATH}"
            ),
        ],
        check=False,
    )

    sys.exit(result.returncode)


from sqlalchemy import String, Text  # noqa: E402
from sqlalchemy.future import select  # noqa: E402
from src.modules.auth.infrastructure.models.user_model import (  # noqa: E402, F401
    UserModel,
)
from src.modules.organization.infrastructure.models.organization_model import (  # noqa: E402, F401
    OrganizationModel,
)

from src.modules.email_template.domain.enums.template_enums import (  # noqa: E402
    TemplateStatusEnum,
    TemplateTypeEnum,
)
from src.modules.email_template.infrastructure.models.template_category_model import (  # noqa: E402
    TemplateCategoryModel,
)
from src.modules.email_template.infrastructure.models.template_model import (  # noqa: E402
    TemplateModel,
)
from src.shared.infrastructure.db import async_session  # noqa: E402
DEFAULT_CATEGORIES = [
    {
        "name": "Welcome & Onboarding",
        "description": (
            "Templates for welcoming new users and helping "
            "them begin using the product."
        ),
        "display_order": 1,
        "is_active": True,
    },
    {
        "name": "Newsletter",
        "description": (
            "Templates for recurring news, announcements, "
            "product updates, and company highlights."
        ),
        "display_order": 2,
        "is_active": True,
    },
    {
        "name": "Promotion",
        "description": (
            "Templates for special offers, discounts, "
            "product launches, and promotional messages."
        ),
        "display_order": 3,
        "is_active": True,
    },
    {
        "name": "Follow-up",
        "description": (
            "Templates for reminders, customer check-ins, "
            "and follow-up communication."
        ),
        "display_order": 4,
        "is_active": True,
    },
    {
        "name": "Event",
        "description": (
            "Templates for event invitations, confirmations, "
            "registrations, and reminders."
        ),
        "display_order": 5,
        "is_active": True,
    },
]


DEFAULT_SYSTEM_TEMPLATES = [
    {
        "category_name": "Welcome & Onboarding",
        "name": "Welcome New User",
        "description": (
            "A friendly welcome email for newly registered users."
        ),
        "subject": (
            "Welcome to {{company|our platform}}, "
            "{{first_name|there}}!"
        ),
        "preheader": (
            "Your account is ready. Let us help you get started."
        ),
        "body_html": """
<html>
<body>
    <h1>Hello {{first_name|there}},</h1>

    <p>
        Welcome to {{company|our platform}}.
        Your account has been created successfully.
    </p>

    <p>
        We are excited to have you with us. You can now explore
        your account and begin using the available features.
    </p>

    <p>
        Best regards,<br>
        {{company|Our}} Team
    </p>
</body>
</html>
""".strip(),
        "from_name": "Mailtracko Team",
        "from_email": None,
        "tags": [
            "welcome",
            "onboarding",
            "new-user",
        ],
        "is_default": True,
    },
    {
        "category_name": "Newsletter",
        "name": "Monthly Newsletter",
        "description": (
            "A clean newsletter template for monthly news "
            "and product updates."
        ),
        "subject": (
            "Your {{month|monthly}} update from "
            "{{company|our team}}"
        ),
        "preheader": (
            "The latest news, improvements, and highlights."
        ),
        "body_html": """
<html>
<body>
    <h1>{{newsletter_title|Our latest updates}}</h1>

    <p>Hello {{first_name|there}},</p>

    <p>
        {{newsletter_summary|Here is a quick look at what has
        been happening this month.}}
    </p>

    <p>
        We have been working on useful improvements and new
        features to make your experience better.
    </p>

    <p>
        <a href="{{cta_url}}">
            Read the full update
        </a>
    </p>

    <p>
        Regards,<br>
        {{company|Our}} Team
    </p>
</body>
</html>
""".strip(),
        "from_name": "Mailtracko Team",
        "from_email": None,
        "tags": [
            "newsletter",
            "monthly",
            "updates",
        ],
        "is_default": False,
    },
    {
        "category_name": "Promotion",
        "name": "Limited-Time Promotion",
        "description": (
            "A promotional template for discounts and "
            "limited-time offers."
        ),
        "subject": (
            "{{offer_name|A special offer}} for "
            "{{first_name|you}}"
        ),
        "preheader": (
            "Take advantage of this offer before it ends."
        ),
        "body_html": """
<html>
<body>
    <h1>{{offer_name|A special offer is waiting}}</h1>

    <p>Hello {{first_name|there}},</p>

    <p>
        Enjoy {{discount|an exclusive discount}} on your
        next purchase.
    </p>

    <p>
        This offer is available until
        {{expiry_date|the stated closing date}}.
    </p>

    <p>
        <a href="{{cta_url}}">
            View the offer
        </a>
    </p>

    <p>
        Best regards,<br>
        {{company|Our}} Team
    </p>
</body>
</html>
""".strip(),
        "from_name": "Mailtracko Team",
        "from_email": None,
        "tags": [
            "promotion",
            "discount",
            "offer",
        ],
        "is_default": False,
    },
    {
        "category_name": "Follow-up",
        "name": "Friendly Follow-up",
        "description": (
            "A simple follow-up template after a meeting, "
            "conversation, or enquiry."
        ),
        "subject": (
            "Following up about "
            "{{topic|our recent conversation}}"
        ),
        "preheader": (
            "A quick follow-up regarding our recent discussion."
        ),
        "body_html": """
<html>
<body>
    <p>Hello {{first_name|there}},</p>

    <p>
        I wanted to follow up regarding
        {{topic|our recent conversation}}.
    </p>

    <p>
        {{next_step|Please let me know a suitable time to
        continue the discussion.}}
    </p>

    <p>
        Best regards,<br>
        {{sender_name|The Mailtracko Team}}
    </p>
</body>
</html>
""".strip(),
        "from_name": "Mailtracko Team",
        "from_email": None,
        "tags": [
            "follow-up",
            "reminder",
            "check-in",
        ],
        "is_default": False,
    },
    {
        "category_name": "Event",
        "name": "Event Invitation",
        "description": (
            "An invitation template for webinars, meetings, "
            "workshops, and other events."
        ),
        "subject": (
            "You are invited: "
            "{{event_name|Our upcoming event}}"
        ),
        "preheader": (
            "View the event details and complete your registration."
        ),
        "body_html": """
<html>
<body>
    <h1>{{event_name|You are invited}}</h1>

    <p>Hello {{first_name|there}},</p>

    <p>
        We would be pleased to have you join us on
        {{event_date|the scheduled date}} at
        {{event_time|the scheduled time}}.
    </p>

    <p>
        Location:
        {{event_location|Event details will be shared soon}}
    </p>

    <p>
        <a href="{{registration_url}}">
            Register now
        </a>
    </p>

    <p>
        Regards,<br>
        {{company|Our}} Events Team
    </p>
</body>
</html>
""".strip(),
        "from_name": "Mailtracko Events",
        "from_email": None,
        "tags": [
            "event",
            "invitation",
            "registration",
        ],
        "is_default": False,
    },
]


def get_supported_values(
    model_class: type,
    values: dict[str, Any],
) -> dict[str, Any]:
    """
    Keeps only fields that exist in the current SQLAlchemy model.

    This allows the seed script to work with optional template
    fields such as preheader, tags, from_name, and is_default
    without failing when a field is not present.
    """
    columns = model_class.__table__.columns

    supported_values = {
        key: value
        for key, value in values.items()
        if key in columns
    }

    if "tags" in supported_values:
        tags_column = columns["tags"]

        if isinstance(
            tags_column.type,
            (String, Text),
        ):
            supported_values["tags"] = json.dumps(
                supported_values["tags"]
            )

    return supported_values


async def get_or_create_categories(
    session,
) -> tuple[dict[str, TemplateCategoryModel], int]:
    """
    Creates missing categories and returns all seeded categories
    indexed by category name.
    """
    categories_by_name: dict[
        str,
        TemplateCategoryModel,
    ] = {}

    added_count = 0

    for category_data in DEFAULT_CATEGORIES:
        query = select(
            TemplateCategoryModel
        ).where(
            TemplateCategoryModel.name
            == category_data["name"]
        )

        result = await session.execute(query)
        category = result.scalars().first()

        supported_values = get_supported_values(
            TemplateCategoryModel,
            category_data,
        )

        if category is None:
            category = TemplateCategoryModel(
                **supported_values
            )

            session.add(category)
            added_count += 1

        else:
            for field_name, field_value in (
                supported_values.items()
            ):
                setattr(
                    category,
                    field_name,
                    field_value,
                )

            if hasattr(category, "deleted_at"):
                category.deleted_at = None

        categories_by_name[
            category_data["name"]
        ] = category

    await session.flush()

    return categories_by_name, added_count


async def seed_system_templates(
    session,
    categories_by_name: dict[
        str,
        TemplateCategoryModel,
    ],
) -> tuple[int, int]:
    """
    Creates missing system templates and updates previously
    seeded templates when the script is run again.
    """
    added_count = 0
    updated_count = 0
    published_at = datetime.now(UTC)

    for template_data in DEFAULT_SYSTEM_TEMPLATES:
        category_name = template_data[
            "category_name"
        ]

        category = categories_by_name[
            category_name
        ]

        conditions = [
            TemplateModel.name
            == template_data["name"],
            TemplateModel.template_type
            == TemplateTypeEnum.SYSTEM.value,
        ]

        if hasattr(
            TemplateModel,
            "organization_id",
        ):
            conditions.append(
                TemplateModel.organization_id.is_(
                    None
                )
            )

        query = select(
            TemplateModel
        ).where(
            *conditions
        )

        result = await session.execute(query)
        template = result.scalars().first()

        template_values = {
            "organization_id": None,
            "category_id": category.id,
            "source_template_id": None,
            "name": template_data["name"],
            "description": template_data[
                "description"
            ],
            "subject": template_data["subject"],
            "preheader": template_data[
                "preheader"
            ],
            "body_html": template_data[
                "body_html"
            ],
            "from_name": template_data[
                "from_name"
            ],
            "from_email": template_data[
                "from_email"
            ],
            "tags": template_data["tags"],
            "template_type": (
                TemplateTypeEnum.SYSTEM.value
            ),
            "status": (
                TemplateStatusEnum.PUBLISHED.value
            ),
            "is_active": True,
            "is_default": template_data[
                "is_default"
            ],
            "smart_personalization_enabled": (
                True
            ),
            "published_at": published_at,
            "archived_at": None,
            "created_by_id": None,
            "updated_by_id": None,
        }

        supported_values = get_supported_values(
            TemplateModel,
            template_values,
        )

        if template is None:
            template = TemplateModel(
                **supported_values
            )

            session.add(template)
            added_count += 1

        else:
            for field_name, field_value in (
                supported_values.items()
            ):
                setattr(
                    template,
                    field_name,
                    field_value,
                )

            if hasattr(template, "deleted_at"):
                template.deleted_at = None

            updated_count += 1

    return added_count, updated_count


async def seed_sys_email_templates():
    async with async_session() as session:
        try:
            print(
                "[1/2] Checking system template "
                "categories..."
            )

            (
                categories_by_name,
                categories_added,
            ) = await get_or_create_categories(
                session
            )

            print(
                "[2/2] Checking system email "
                "templates..."
            )

            (
                templates_added,
                templates_updated,
            ) = await seed_system_templates(
                session,
                categories_by_name,
            )

            await session.commit()

        except Exception:
            await session.rollback()
            raise

    print(
        "System email template seed completed!"
    )
    print(
        f"Categories added: {categories_added}"
    )
    print(
        f"System templates added: "
        f"{templates_added}"
    )
    print(
        f"System templates updated: "
        f"{templates_updated}"
    )


if __name__ == "__main__":
    asyncio.run(
        seed_sys_email_templates()
    )
