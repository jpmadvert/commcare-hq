# coding: utf-8
from __future__ import print_function
from __future__ import absolute_import
from __future__ import unicode_literals
from django.core.management.base import BaseCommand
import time


class Command(BaseCommand):
    help = "Tell user to use make_superuser"

    def add_arguments(self, parser):
        parser.add_argument(
            'domain_name',
        )
        parser.add_argument(
            'username',
        )
        parser.add_argument(
            'passwd',
        )

    def handle(self, domain_name, username, passwd, **options):
        print()
        print("The bootstrap command doesn't exist anymore.")
        print()
        time.sleep(2)
        print("Please use `./manage.py make_superuser {username}` "
              "and then create a domain in the UI instead.".format(username=username))
        print()
