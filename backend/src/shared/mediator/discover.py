import importlib
import pkgutil

from src.shared.infrastructure.logger import logger
from src.shared.mediator.registry import registry


def auto_discover_listeners(modules_root: str = "src.modules") -> None:
    try:
        modules_package = importlib.import_module(modules_root)
    except Exception:
        logger.warning("[ListenerRegistry] modules root %s not found", modules_root)
        return

    for finder, module_name, _ in pkgutil.walk_packages(
        path=list(getattr(modules_package, "__path__", [])),
        prefix=f"{modules_root}.",
        onerror=lambda name: logger.warning("Could not import %s", name),
    ):
        if module_name.endswith("_listener"):
            try:
                importlib.import_module(module_name)
                logger.warning("[ListenerRegistry] Imported %s", module_name)
            except Exception:
                logger.exception("[ListenerRegistry] Failed to import %s", module_name)

    registry.log_all()
