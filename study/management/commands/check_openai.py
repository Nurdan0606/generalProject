from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from openai import APIConnectionError, APIStatusError, APITimeoutError, OpenAI


class Command(BaseCommand):
    help = 'Check OpenAI credentials and model access without sending lecture data or generating content.'
    requires_system_checks = []

    def handle(self, *args, **options):
        if not settings.OPENAI_API_KEY:
            raise CommandError('Set OPENAI_API_KEY in the project .env file first.')
        try:
            with OpenAI(api_key=settings.OPENAI_API_KEY, timeout=15, max_retries=1) as client:
                model = client.models.retrieve(settings.OPENAI_MODEL)
        except APITimeoutError:
            raise CommandError('OpenAI timed out. Check your internet connection and retry.') from None
        except APIConnectionError:
            raise CommandError('Could not reach OpenAI. Check your internet connection and retry.') from None
        except APIStatusError as exc:
            raise CommandError(
                f'OpenAI returned HTTP {exc.status_code}. Check your API key, billing, and model access.'
            ) from None
        self.stdout.write(self.style.SUCCESS(f'OpenAI connected. Model: {model.id}'))
        self.stdout.write('Model lookup succeeded. Generate a question bank in the app to verify generation billing and quota.')
