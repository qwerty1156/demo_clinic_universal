"""Exercise booking core offline, using synthetic data and a temporary database."""
import json
import os
from pathlib import Path
import sys
import tempfile
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "demo_clinic_universal"))
os.environ.update(BOT_TOKEN="offline-demo-not-a-token", ADMIN_ID="123456789", WEBHOOK_URL="https://example.invalid")
from core.booking import BookingService
from core.applications import ApplicationService
from core.models import IncomingMessage
from database import Database

with tempfile.TemporaryDirectory(prefix="clinic-demo-") as directory:
    db = Database(str(Path(directory) / "demo.db"))
    booking = BookingService(db)
    replies = []
    def message(text=None):
        return IncomingMessage(platform="demo", user_id="synthetic-user", text=text)
    replies.append(booking.start(message(), "consultation").text)
    for text in ["Friday afternoon", "Demo User", "+70000000000"]:
        replies.append(booking.handle_text(message(text)).text)
    application_id = booking.confirm(message())
    if application_id is None:
        raise RuntimeError("Booking was not saved")
    confirmed, recipient = ApplicationService(db).process_admin_action(application_id, "confirm")
    if not confirmed or recipient != "synthetic-user":
        raise RuntimeError("Administrator confirmation failed")
    row = dict(db.get_application(application_id))
    if row["status"] != "confirmed":
        raise RuntimeError("Confirmation was not persisted")
    print(json.dumps({"mode": "offline core; no Telegram or AI calls", "replies": replies,
        "application_status": row["status"]}, ensure_ascii=False, indent=2))
