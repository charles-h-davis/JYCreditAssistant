"""Demo friends loaded into the demo account by `seed.py`.

The same eight people whose activity the feed shows, so the friends list and the
feed tell one story. Addresses are `example.com`: nobody is emailed, and these
are deliberately *not* Supabase auth users — a friend here is a contact row the
user owns.
"""

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class DemoFriend:
    """One friend to load into the demo account."""

    name: str
    email: str


#: Loaded by `app.sections.friends.seed` (upserted, so re-running is safe).
DEFAULT_FRIENDS: tuple[DemoFriend, ...] = (
    DemoFriend(name="James May", email="james.may@example.com"),
    DemoFriend(name="Lucas James", email="lucas.james@example.com"),
    DemoFriend(name="Priya Shah", email="priya.shah@example.com"),
    DemoFriend(name="Aisha Khan", email="aisha.khan@example.com"),
    DemoFriend(name="Tom Ellis", email="tom.ellis@example.com"),
    DemoFriend(name="Marco Rossi", email="marco.rossi@example.com"),
    DemoFriend(name="Sofia Bianchi", email="sofia.bianchi@example.com"),
    DemoFriend(name="Daniel Okafor", email="daniel.okafor@example.com"),
)
