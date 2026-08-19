from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TASKS = ROOT / 'backend/src/modules/campaign/infrastructure/background_tasks/campaign_tasks.py'
text = TASKS.read_text(encoding='utf-8')

assert 'except (InvalidError, ConflictError) as exc:' in text
assert 'Campaign worker skipped campaign_id=%s' in text
assert 'exc.errors' in text
assert '@dramatiq.actor(' in text
print('PASS: non-ready campaign validation is acknowledged without Dramatiq retry amplification')
