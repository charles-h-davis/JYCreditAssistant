"""Friends Feed section.

A small social feed for the Learning tab: fictional friend activity mixed with
the caller's own finished lessons and refresh rounds, newest first.

Friend activity is hardcoded in `content.py` and never stored; the user's own
entries live in `friends_feed_entries` (see `schema.sql`).

Owner: _fill in_
"""

from app.sections.friends_feed.router import router

__all__ = ["router"]
