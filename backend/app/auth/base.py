"""AuthProvider interface — every provider resolves some external proof of
identity (a password, a SAML assertion) to an existing AppUser row, and the
API layer issues the same JWT regardless of which provider authenticated
the user. `local_password` is implemented now; `saml_surfconext` is the
planned SURFconext SSO provider and slots in here without touching the
token-issuing code.
"""

from __future__ import annotations

from abc import ABC, abstractmethod

from sqlalchemy.orm import Session

from app.models.user import AppUser


class AuthProvider(ABC):
    @abstractmethod
    def authenticate(self, db: Session, **credentials) -> AppUser | None:
        """Return the matching, active AppUser, or None if authentication failed."""
        raise NotImplementedError
