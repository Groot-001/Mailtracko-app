# import argparse
# from src.modules.auth.application.listeners.user_created_listener import *  # noqa: F403

# # from src.modules.audit.application.listeners.repository_audit_listener import *  # noqa: F403
# from src.modules.auth.application.listeners.user_updated_listener import *  # noqa: F403
# from src.modules.auth.application.listeners.user_invalid_login_attempt_listener import *  # noqa: F403
# from src.modules.auth.application.listeners.organization.auth_switch_organization_listener import *  # noqa: F403
# from src.shared.mediator.registry import registry


# def main():
#     parser = argparse.ArgumentParser(description="List all registered event handlers.")
#     parser.add_argument("--event", help="Filter by event name, e.g. UserCreatedEvent")
#     parser.add_argument(
#         "--module", help="Filter handlers by module substring, e.g. auth"
#     )
#     args = parser.parse_args()

#     all_events = registry.inspect()

#     if not all_events:
#         print("No listeners registered.")
#         return

#     for event_name, handlers in sorted(all_events.items()):
#         if args.event and args.event.lower() not in event_name.lower():
#             continue
#         if args.module:
#             handlers = [h for h in handlers if args.module in h.module]
#         if not handlers:
#             continue

#         print(
#             f"\n{event_name} ({len(handlers)} handler{'s' if len(handlers) != 1 else ''})"
#         )
#         print("─" * 50)
#         for h in handlers:
#             print(f"  ▸ {h.name}")
#             print(f"    module : {h.module}")
#             if h.doc:
#                 print(f"    doc    : {h.doc}")


# if __name__ == "__main__":
#     main()
