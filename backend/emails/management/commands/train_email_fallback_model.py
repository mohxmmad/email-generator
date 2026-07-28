from django.core.management.base import BaseCommand, CommandError

from emails.local_ai import train_local_model


class Command(BaseCommand):
    help = "Train the local fallback email model from a CSV/JSONL dataset or URL."

    def add_arguments(self, parser):
        parser.add_argument(
            "--dataset-path",
            type=str,
            default=None,
            help="Local dataset file path (.csv or .jsonl).",
        )
        parser.add_argument(
            "--dataset-url",
            type=str,
            default=None,
            help="Public dataset URL (.csv or .jsonl).",
        )

    def handle(self, *args, **options):
        dataset_path = options["dataset_path"]
        dataset_url = options["dataset_url"]
        try:
            model = train_local_model(dataset_path=dataset_path, dataset_url=dataset_url)
        except ValueError as exc:
            raise CommandError(str(exc)) from exc
        self.stdout.write(
            self.style.SUCCESS(
                "Local fallback model trained successfully "
                f"(tones: {', '.join(sorted(model['body_starts_by_tone'].keys()))})."
            )
        )
