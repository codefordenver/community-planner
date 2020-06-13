from argparse import ArgumentParser
from typing import Any

from django.core.management.base import CommandError

from zerver.lib.management import ZulipBaseCommand


class Command(ZulipBaseCommand):
    help = """Show the owners and administrators in an organization."""

    def add_arguments(self, parser: ArgumentParser) -> None:
        self.add_realm_args(parser, required=True)

    def handle(self, *args: Any, **options: Any) -> None:
        realm = self.get_realm(options)
        assert realm is not None  # True because of required=True above

        admin_users = realm.get_admin_users_and_bots()
        owner_user_ids = set(list(realm.get_human_owner_users().values_list("id", flat=True)))

        if admin_users:
            print('Administrators:\n')
            for user in admin_users:
                owner_detail = ""
                if user.id in owner_user_ids:
                    owner_detail = " [owner]"
                print('  %s (%s)%s' % (user.delivery_email, user.full_name, owner_detail))

        else:
            raise CommandError('There are no admins for this realm!')

        print('\nYou can use the "knight" management command to make more users admins.')
        print('\nOr with the --revoke argument, remove admin status from users.')
