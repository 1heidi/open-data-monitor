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
    report_files = glob.glob(os.path.join(REPORTS_DIR, "open_data_policy_report_*.txt"))
    if not report_files:
        print("⚠️ No report files found in 'reports/' folder.")
        return None
    latest_file = max(report_files, key=os.path.getmtime)
    print(f"📄 Latest report found: {latest_file}")
    return latest_file

# ================================
# ✉️ SEND EMAIL (INLINE REPORT)
# ================================
def send_email(report_path=None):
    if not report_path:
        report_path = get_latest_report()
        if not report_path:
            print("⚠️ No report found to include.")
            return

    # Read the report content
    with open(report_path, "r", encoding="utf-8") as f:
        report_content = f.read()

    report_date = datetime.now().strftime("%B %d, %Y")

    msg = EmailMessage()
    msg["Subject"] = f"🧾 Weekly Open Data / Science Policy Monitor Report — {report_date}"
    msg["From"] = EMAIL_USER
    msg["To"] = EMAIL_RECIPIENT

    # ✅ Inline the report content directly in the email body
    msg.set_content(
        f"""Hello,

Here is your weekly update.

{'='*60}

{report_content}

{'='*60}

Best regards,
Heidi's Best Attempt at an Open Data / Science Policy Monitor Bot 🤖
"""
    )

    # Send the email
    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
        smtp.login(EMAIL_USER, GMAIL_APP_PASSWORD)
        smtp.send_message(msg)
        print(f"✅ Email sent to {EMAIL_RECIPIENT} with inline report: {os.path.basename(report_path)}")


if __name__ == "__main__":
    latest_report = get_latest_report()
    send_email(latest_report)
