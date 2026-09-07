import logging
from api.models import UserProfile

logger = logging.getLogger(__name__)


class UserService:
    @staticmethod
    def get_or_create_user(email: str, name: str, section: str = "") -> UserProfile:
        """
        Retrieves an existing UserProfile by email or creates a new one.
        Updates name and section if provided.
        """
        email_clean = email.strip().lower()
        name_clean = name.strip() or email_clean.split('@')[0]
        section_clean = section.strip()

        user, created = UserProfile.objects.get_or_create(
            email=email_clean,
            defaults={
                'name': name_clean,
                'section': section_clean
            }
        )

        if not created:
            updated = False
            if name_clean and user.name != name_clean:
                user.name = name_clean
                updated = True
            if section_clean and user.section != section_clean:
                user.section = section_clean
                updated = True
            if updated:
                user.save()

        return user
