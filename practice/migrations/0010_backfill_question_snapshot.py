# Data migration: backfill question_snapshot for existing UserAnswer rows.
#
# For historical answers recorded before the snapshot feature landed, freeze
# the current question + option state into their snapshot. After this runs,
# all past results pages render from snapshotted data.

from django.db import migrations


def backfill_snapshots(apps, schema_editor):
    UserAnswer = apps.get_model("practice", "UserAnswer")

    # Only touch answers that don't already have a snapshot.
    qs = UserAnswer.objects.filter(question_snapshot__isnull=True).select_related("question")
    total = qs.count()
    if total == 0:
        return

    # Iterate in chunks to keep memory bounded on large DBs.
    CHUNK = 500
    last_id = 0
    processed = 0
    while True:
        batch = list(
            qs.filter(id__gt=last_id).order_by("id")[:CHUNK]
        )
        if not batch:
            break
        for answer in batch:
            question = answer.question
            options = list(question.answer_options.all().order_by("order"))
            selected_ids = list(answer.selected_options.values_list("id", flat=True))
            answer.question_snapshot = {
                "version": 1,
                "question_text": question.question_text,
                "question_type": question.question_type,
                "explanation": question.explanation or "",
                "options": [
                    {
                        "id": o.id,
                        "text": o.option_text,
                        "is_correct": o.is_correct,
                        "order": o.order,
                    }
                    for o in options
                ],
                "selected_option_ids": selected_ids,
                "correct_option_ids": [o.id for o in options if o.is_correct],
                "backfilled": True,  # marker for auditing
            }
            answer.save(update_fields=["question_snapshot"])
        last_id = batch[-1].id
        processed += len(batch)


def noop_reverse(apps, schema_editor):
    # Reversing this migration (unsetting snapshots) is pointless since the
    # forward step is idempotent. Provide a no-op so `migrate --plan` doesn't
    # complain about irreversibility.
    pass


class Migration(migrations.Migration):
    dependencies = [
        ("practice", "0009_useranswer_question_snapshot"),
    ]

    operations = [
        migrations.RunPython(backfill_snapshots, noop_reverse),
    ]
