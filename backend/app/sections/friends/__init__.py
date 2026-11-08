"""Friends section.

The signed-in user's friend list: contact rows (name + email) they own, added by
email from the friends feed and seeded with a handful of demo people.

Friends are contacts, not Supabase auth users — see `README.md`.

Owner: _fill in_
"""

from app.sections.friends.router import router

__all__ = ["router"]
