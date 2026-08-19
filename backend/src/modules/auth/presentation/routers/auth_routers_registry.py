from fastapi import APIRouter

from src.modules.auth.presentation.routers.auth_core_routers import (
    router as core_router,
)
from src.modules.auth.presentation.routers.auth_email_routers import (
    router as email_router,
)
from src.modules.auth.presentation.routers.auth_oauth_routers import (
    router as oauth_router,
)
from src.modules.auth.presentation.routers.auth_password_routers import (
    router as password_router,
)
from src.modules.auth.presentation.routers.auth_session_routers import (
    router as session_router,
)


def register_auth_routers(main_router: APIRouter):
    main_router.include_router(core_router)
    main_router.include_router(password_router)
    main_router.include_router(oauth_router)
    main_router.include_router(email_router)
    main_router.include_router(session_router)