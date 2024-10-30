from django.core.management import BaseCommand
from databucket.models import Crunchbase
from tqdm import tqdm


class Command(BaseCommand):
    def handle(self, *args, **options):
        queryset = Crunchbase.objects.filter().order_by("-updated_at")

        # filter who logo starts with this https://res.cloudinary.com/crunchbase-production
        queryset = queryset.filter(
            logo__startswith='https://res.cloudinary.com/crunchbase-production')

        total = queryset.count()

        for i, company in enumerate(tqdm(queryset, total=total, ascii=' =')):
            queryset.filter(logo__startswith='https://res.cloudinary.com/crunchbase-production').update(
                logo=company.logo.replace(
                    'https://res.cloudinary.com/crunchbase-production', 'https://images.crunchbase.com')
            )
            # # replace logo prefix from https://res.cloudinary.com/crunchbase-production to https://images.crunchbase.com
            # company._id = str(company._id)
            # company.logo = company.logo.replace(
            #     'https://res.cloudinary.com/crunchbase-production', 'https://images.crunchbase.com')
            # company.save(update_fields=['logo'], force_update=True)
            # queryset.filter(_id=company._id).update(logo=company.logo)

            # # company.save_base()
            # # Crunchbase.objects.update(company)
            print("Company:", company._id, company.logo)
            if i > 2:
                break
