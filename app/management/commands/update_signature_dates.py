from django.core.management.base import BaseCommand
from app.models import Consents
import boto3
from django.conf import settings

class Command(BaseCommand):
    help = "Update createdAt field in Consents with the S3 LastModified date of the signature file"

    def handle(self, *args, **kwargs):
        Consents.objects.all().update(createdAt=None)
        s3 = boto3.client(
            's3',
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
            region_name=settings.AWS_S3_REGION_NAME,
        )

        bucket_name = settings.AWS_STORAGE_BUCKET_NAME

        consents = Consents.objects.filter(signature__isnull=False, createdAt__isnull=True)

        for consent in consents:
            try:
                key = consent.signature.name  # path en S3
                response = s3.head_object(Bucket=bucket_name, Key=key)
                last_modified = response['LastModified']  # datetime en UTC
                consent.createdAt = last_modified
                consent.save(update_fields=['createdAt'])
                self.stdout.write(self.style.SUCCESS(f"Updated consent {consent.id} with {last_modified}"))
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"Error with {consent.id}: {e}"))
