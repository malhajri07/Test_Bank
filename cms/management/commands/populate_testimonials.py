"""
Seed the Testimonial table with a mixed-locale pool (Arabic, English,
Indian names) so the homepage carousel always has enough variety to fill
the random pick-10 the context processor does.

Idempotent — re-running updates existing entries (matched by name) in place.
"""

from django.core.management.base import BaseCommand

from cms.models import Testimonial


SEED = [
    # Arabic names
    ("Khalid Ali", "Director of Operations, Riyadh",
     "Exam Stellar turned a 6-month grind into a structured 8-week plan. The explanations after each question are better than the course I paid thousands for."),
    ("Noura Al-Sabah", "Project Manager, Kuwait City",
     "Passed PMP on my first sit. The scenario-based questions here are closer to the real exam than anything else I tried."),
    ("Fatima Al-Zahra", "Scrum Master, Dammam",
     "The CSM track is exactly the right mix of theory and case studies. I referenced these questions in two interview loops."),
    ("Abdulrahman Al-Mutairi", "Cloud Architect, Jeddah",
     "I used the AWS SAA bank during lunch breaks for three weeks and cleared the exam with a 800+ score."),
    ("Mariam Haddad", "Business Analyst, Dubai",
     "The dashboard shows me exactly where I'm weak. No guessing, no wasted study time."),
    ("Youssef Mansour", "QA Lead, Cairo",
     "Worth every riyal. The explanations teach you why, not just what the answer is."),
    # Indian names
    ("Priya Sharma", "Product Manager, Bengaluru",
     "I've tried three prep platforms. Exam Stellar is the only one where the practice questions actually taught me new concepts."),
    ("Rahul Gupta", "DevOps Engineer, Hyderabad",
     "The Kubernetes and AWS banks are tough in the best way. Cleared CKA with room to spare."),
    ("Ananya Iyer", "Program Manager, Mumbai",
     "Studied two hours a day for a month. The difficulty-level filter made sure I didn't waste time on questions that were too easy for me."),
    ("Arjun Patel", "Full-Stack Developer, Ahmedabad",
     "The explanations are a crash course in themselves. Passed my Scrum PSM I on the first attempt."),
    ("Kavita Menon", "Data Analyst, Chennai",
     "Well-organized, fair pricing, and the review mode is addictive. Already recommending to my team."),
    ("Vikram Rao", "IT Consultant, Pune",
     "The simulated exam mode mirrored the actual PMP — same pace, same feel. No surprises on test day."),
    # English names
    ("Sarah Thompson", "Senior Engineer, London",
     "I appreciate the detail in the answer explanations. It's like getting a mentor review for every wrong answer."),
    ("Michael Carter", "Operations Lead, Toronto",
     "Clean UI, no fluff, real exam-level questions. I wish I'd found this earlier."),
    ("Emily Davis", "Certified ScrumMaster, Austin",
     "The practice banks here held up better than two books I bought. Passed CSM with confidence."),
    ("James O'Connor", "Solution Architect, Dublin",
     "The platform gets out of the way and lets you practice. That's exactly what I needed."),
]


class Command(BaseCommand):
    help = "Seed the homepage testimonial pool with a mix of Arabic, English, and Indian names."

    def add_arguments(self, parser):
        parser.add_argument(
            '--reset',
            action='store_true',
            help='Delete all existing testimonials first, then reseed.',
        )

    def handle(self, *args, **options):
        if options['reset']:
            deleted, _ = Testimonial.objects.all().delete()
            self.stdout.write(f'Deleted {deleted} existing testimonials.')

        created, updated = 0, 0
        for idx, (name, role, quote) in enumerate(SEED):
            _, was_created = Testimonial.objects.update_or_create(
                name=name,
                defaults={
                    'role': role,
                    'quote': quote,
                    'is_active': True,
                    'order': idx,
                },
            )
            if was_created:
                created += 1
            else:
                updated += 1

        self.stdout.write(self.style.SUCCESS(
            f'Done. Created {created}, updated {updated}, total active: {Testimonial.objects.filter(is_active=True).count()}.'
        ))
