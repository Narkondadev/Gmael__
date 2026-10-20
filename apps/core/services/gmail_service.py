import imaplib
import email
from email.header import decode_header
import datetime
import re

def fetch_live_emails(inbox, limit=20, domain=None):
    if not inbox.app_password:
        return []

    try:
        # Connect to Gmail IMAP
        mail = imaplib.IMAP4_SSL("imap.gmail.com")
        mail.login(inbox.email_address, inbox.app_password)
        mail.select("INBOX")

        # Search for emails using valid IMAP syntax (TEXT "query"), with fallback to ALL
        email_ids = []
        if domain:
            domain_clean = domain.strip()
            try:
                result, data = mail.search(None, f'TEXT "{domain_clean}"')
                if result == 'OK' and data and data[0]:
                    email_ids = data[0].split()
            except Exception as search_err:
                print(f"IMAP TEXT Search warning: {search_err}")
                email_ids = []

        # If domain search yielded no results or was not provided, fetch ALL latest emails to filter
        if not email_ids:
            result, data = mail.search(None, 'ALL')
            if result == 'OK' and data and data[0]:
                email_ids = data[0].split()

        if not email_ids:
            return []

        # Fetch recent emails to find matching target emails up to limit
        scan_email_ids = email_ids[-50:] if len(email_ids) > 50 else email_ids
        emails_data = []

        for e_id in reversed(scan_email_ids):
            result, msg_data = mail.fetch(e_id, '(RFC822)')
            if result != 'OK':
                continue

            raw_email = msg_data[0][1]
            msg = email.message_from_bytes(raw_email)

            # Decode subject completely
            subject_parts = decode_header(msg.get("Subject", "(No Subject)"))
            decoded_subject = ""
            for part, encoding in subject_parts:
                if isinstance(part, bytes):
                    decoded_subject += part.decode(encoding or "utf-8", errors='ignore')
                else:
                    decoded_subject += str(part)
            subject = decoded_subject or "(No Subject)"

            # Decode sender
            sender = msg.get("From", "Unknown")

            # Decode recipient
            recipient = msg.get("To", "")

            # Get date
            date = msg.get("Date", "")

            # Extract body (supports both text/plain and text/html fallback for OTPs)
            body_text = ""
            html_text = ""

            if msg.is_multipart():
                for part in msg.walk():
                    content_type = part.get_content_type()
                    content_disposition = str(part.get("Content-Disposition"))

                    if "attachment" not in content_disposition:
                        if content_type == "text/plain" and not body_text:
                            body_text = part.get_payload(decode=True).decode(errors='ignore')
                        elif content_type == "text/html" and not html_text:
                            html_text = part.get_payload(decode=True).decode(errors='ignore')
            else:
                content_type = msg.get_content_type()
                payload = msg.get_payload(decode=True)
                if payload:
                    if content_type == "text/plain":
                        body_text = payload.decode(errors='ignore')
                    elif content_type == "text/html":
                        html_text = payload.decode(errors='ignore')

            # Fallback to HTML if text/plain is missing or empty
            final_body = body_text.strip()
            if not final_body and html_text:
                # Clean HTML tags to reveal plain text & 6-digit OTP codes
                clean_text = re.sub(r'<style[^>]*>[\s\S]*?</style>', '', html_text, flags=re.IGNORECASE)
                clean_text = re.sub(r'<script[^>]*>[\s\S]*?</script>', '', clean_text, flags=re.IGNORECASE)
                clean_text = re.sub(r'<[^>]+>', ' ', clean_text)
                clean_text = re.sub(r'\s+', ' ', clean_text).strip()
                final_body = clean_text

            # If a target domain was specified, verify that this email matches the target (sender/recipient/body/subject)
            if domain:
                d_lower = domain.strip().lower()
                full_searchable = f"{sender} {recipient} {subject} {final_body}".lower()
                # If d_lower is not in any field, skip
                if d_lower not in full_searchable:
                    continue

            emails_data.append({
                'subject': subject,
                'sender': sender,
                'date': date,
                'body': final_body[:1000], # preview snippet
            })

            if len(emails_data) >= limit:
                break

        mail.close()
        mail.logout()
        return emails_data

    except Exception as e:
        print(f"IMAP Fetch Error: {e}")
        return []

