import os
import glob
import smtplib
from email.message import EmailMessage
from datetime import datetime

# ================================
# 📧 EMAIL CONFIGURATION
# ================================
EMAIL_USER = os.environ.get("EMAIL_USER")  # your Gmail address
GMAIL_APP_PASSWORD = os.environ.get("GMAIL_APP_PASSWORD")  # Gmail App Password
EMAIL_RECIPIENT = os.environ.get("EMAIL_RECIPIENT", EMAIL_USER)  # recipient(s)

REPORTS_DIR = "reports"

# ================================
# 🧠 FIND MOST RECENT REPORT
# ================================
def get_latest_report():
    report_files = glob.glob(os.path.join(REPORTS_DIR, "open_data_monitor_*.md"))
    if not report_files:
        print("⚠️ No report files found in 'reports/' folder.")
        return None
    latest_file = max(report_files, key=os.path.getmtime)
    print(f"📄 Latest report found: {latest_file}")
    return latest_file

# ================================
# ✉️ SEND EMAIL
# ================================
def send_email():
    report_path = get_latest_report()
    if not report_path:
        return

    report_date = datetime.now().strftime("%B %d, %Y")

    # Create the email
    msg = EmailMessage()
    msg["Subject"] = f"📊 Weekly Open Data Monitor Report — {report_date}"
    msg["From"] = EMAIL_USER
    msg["To"] = EMAIL_RECIPIENT.split(",")

    msg.set_content(
        f"""Hello,

Your weekly Open Data Policy Monitor report is ready.

Attached is the latest markdown report gener
