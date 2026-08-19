"""Campaign background task package.

Import campaign_tasks only from the Dramatiq worker process so application startup
is not coupled to Redis availability.
"""
