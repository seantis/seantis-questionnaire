from django.core.management.base import NoArgsCommand


class Command(NoArgsCommand):
    def handle_noargs(self, **options):
        from questionnaire.emails import send_emails
        res = send_emails()
        if res:
            print res
