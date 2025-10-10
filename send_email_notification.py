import os
import glob
import smtplib
from email.message import EmailMessage
from datetime import datetime

# ================================
# 📧 EMAIL CONFIGURATION
# ================================
EMAIL_USER = os.environ.get("EMAIL_USER")  # Gmail address (from repo secrets)
GMAIL_APP_PASSWORD = os.environ.get("GMAIL_APP_PASSWORD")  # Gmail App Password
EMAIL_RECIPIENT = os.environ.get("EMAIL_RECIPIENT", EMAIL_USER)  # Default to sender if not set

REPORTS_DIR = "reports"

# ================================
# 🧠 FIND MOST RECENT TXT REPORT
# ================================
def get_latest_report():
    report_files = glob.glob(os.path.join(REPORTS_DIR, "open_data_policy_report_*.txt"))
    if not report_files:
        print("⚠️ No .txt report files found in 'reports/' folder.")
        return None
    latest_file = max(report_files, key=os.path.getmtime)
    print(f"📄 Latest report found: {latest_file}")
    return latest_file

# ================================
# ✉️ SEND EMAIL WITH REPORT ATTACHMENT
# ================================
def send_email(report_path=None):
    msg = EmailMessage()
    msg["Subject"] = "🧾 Weekly Open Data Policy Monitor Report"
    msg["From"] = EMAIL_USER
    msg["To"] = EMAIL_RECIPIENT

    if not report_path:
        report_path = get_latest_report()
        if not report_path:
            print("⚠️ No report found to attach.")
            return

    report_date = datetime.now().strftime("%B %d, %Y")
    msg.set_content(
        f"""Hello,

Your weekly Open Data Policy Monitor report is ready.

Attached is the latest plain-text report generated automatically on {report_date}.

Best regards,
Heidi’s Open Data Policy Monitor Bot
"""
    )

    # Attach the .txt report
    if os.path.exists(report_path):
        with open(report_path, "rb") as f:
            report_data = f.read()
            filename = os.path.basename(report_path)
            msg.add_attachment(
                report_data,
                maintype="text",
                subtype="plain",
                filename=filename
            )
            print(f"📎 Attached report: {filename}")
    else:
        print(f"⚠️ File not found: {report_path}")
        return

    # Send the email
    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
        smtp.login(EMAIL_USER, GMAIL_APP_PASSWORD)
        smtp.send_message(msg)
        print(f"✅ Email sent to {EMAIL_RECIPIENT} with report: {os.path.basename(report_path)}")

# ================================
# 🚀 MAIN EXECUTION
# ================================
if __name__ == "__main__":
    latest_report = get_latest_report()
    send_email(latest_report)
