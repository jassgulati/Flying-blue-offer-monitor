import requests
import re
import os
from bs4 import BeautifulSoup
import smtplib
from twilio.rest import Client

URLS = {
    "Doctor of Credit (Tag)": "https://www.doctorofcredit.com/tag/flying-blue/",
    "Doctor of Credit (Offer)": "https://www.doctorofcredit.com/bank-of-america-air-france-klm-flyingblue-credit-card-70000-miles-signup-bonus-100-100-xp-bonus/",
    "Flying Blue / KLM": "https://www.klm.com/information/flying-blue/creditcard",
    "Upgraded Points": "https://upgradedpoints.com/news/air-france-klm-credit-card-offer-70k-miles/",
    "Frequent Miler": "https://frequentmiler.com/tag/flying-blue/"
}

REQUIRED_BONUS = 70000
CARD_KEYWORDS = ["flying blue", "air france", "klm"]

SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587

def extract_bonus(text):
    matches = re.findall(r'(\d{2,3})[, ]?000', text)
    bonuses = [int(m) * 1000 for m in matches]
    return max(bonuses) if bonuses else 0

def fee_waived(text):
    return any(p in text for p in [
        "annual fee waived",
        "$0 annual fee",
        "no annual fee first year"
    ])

def card_mentioned(text):
    return any(k in text for k in CARD_KEYWORDS)

def send_email(subject, body):
    with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
        server.starttls()
        server.login(os.getenv("SMTP_USER"), os.getenv("SMTP_PASS"))
        server.sendmail(
            os.getenv("SMTP_USER"),
            os.getenv("EMAIL_TO"),
            f"Subject: {subject}\n\n{body}"
        )

def send_sms(body):
    client = Client(
        os.getenv("TWILIO_SID"),
        os.getenv("TWILIO_TOKEN")
    )
    client.messages.create(
        body=body,
        from_=os.getenv("TWILIO_FROM"),
        to=os.getenv("TWILIO_TO")
    )

for source, url in URLS.items():
    r = requests.get(url, timeout=15)
    if r.status_code != 200:
        continue

    soup = BeautifulSoup(r.text, "html.parser")
    text = soup.get_text(" ", strip=True).lower()

    if not card_mentioned(text):
        continue

    bonus = extract_bonus(text)
    if bonus < REQUIRED_BONUS:
        continue

    waived = fee_waived(text)

    message = (
        f"Source: {source}\n"
        f"Bonus: {bonus} miles\n"
        f"Annual Fee Waived: {'YES' if waived else 'Not mentioned'}\n"
        f"{url}"
    )

    send_email("🚨 Flying Blue 70K+ Offer Detected", message)
    send_sms(message)
    break
