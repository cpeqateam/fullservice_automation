#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Gmail SMTP üzerinden e-posta gönderme yardımcısı.

GRK app/utils/__sendEmail.py'nin sadeleştirilmiş portudur (aynı SMTP hesabı).
FULL Servis bildirimi maili DOSYASIZ gönderir (sadece gövde) — GRK ile aynı.
"""
import smtplib
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders

from common.config import get_secret


class EmailSender:
    """Gmail SMTP ile e-posta gönderen zincirlenebilir yardımcı (konu/gövde/alıcı/ek ayarla,
    tek `send_email()` ile gönder). SMTP kimliği get_secret ile secrets.json/env'den gelir."""

    def __init__(self):
        """SMTP ayarlarını (Gmail, 587) ve sırları (get_secret) yükler, boş içerik alanlarını kurar."""
        self.smtp_server = 'smtp.gmail.com'
        self.smtp_port = 587
        # Sırlar repoya KONMAZ — ortam değişkeni ya da gitignore'lu secrets.json'dan gelir.
        self.username = get_secret("FS_SMTP_USER")
        self.password = get_secret("FS_SMTP_PASS")
        self.from_addr = get_secret("FS_SMTP_FROM", "cpetestteam@gmail.com")

        self.body = ""
        self.subject = ""
        self.to_addresses = []
        self.cc_addresses = []
        self.attachments = []

    def set_body(self, body):
        """Mail gövdesini ayarlar (zincirleme için self döner)."""
        self.body = str(body)
        return self

    def set_subject(self, subject):
        """Mail konusunu ayarlar (zincirleme için self döner)."""
        self.subject = str(subject)
        return self

    def add_to_address(self, address):
        """Alıcı (To) adresi ekler — str ya da liste kabul eder; tekrarları atlar."""
        if isinstance(address, str):
            if address not in self.to_addresses:
                self.to_addresses.append(address)
        elif isinstance(address, list):
            for addr in address:
                self.add_to_address(addr)
        return self

    def add_cc_address(self, address):
        """Kopya (CC) adresi ekler — str ya da liste kabul eder; tekrarları atlar."""
        if isinstance(address, str):
            if address not in self.cc_addresses:
                self.cc_addresses.append(address)
        elif isinstance(address, list):
            for addr in address:
                self.add_cc_address(addr)
        return self

    def add_attachment(self, file_path):
        """Dosya eki ekler (yoksa FileNotFoundError). FULL Servis bildirim mailinde ek YOK."""
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Belirtilen dosya bulunamadı: {file_path}")
        if file_path not in self.attachments:
            self.attachments.append(file_path)
        return self

    def send_email(self):
        """Hazırlanan maili gönderir (starttls + login + sendmail); konu `[ROBOT] ...`,
        gövde HTML. Zorunlu alanlar boşsa ValueError."""
        if not self.body.strip():
            raise ValueError("Mesaj içeriği boş olamaz!")
        if not self.subject.strip():
            raise ValueError("Konu başlığı boş olamaz!")
        if not self.to_addresses:
            raise ValueError("En az bir alıcı adresi belirtilmelidir!")

        smtpObj = None
        try:
            smtpObj = smtplib.SMTP(self.smtp_server, self.smtp_port)
            smtpObj.starttls()
            smtpObj.login(self.username, self.password)

            msg = MIMEMultipart('alternative')
            msg['From'] = self.from_addr
            msg['To'] = ', '.join(self.to_addresses)
            if self.cc_addresses:
                msg['Cc'] = ', '.join(self.cc_addresses)
            msg['Subject'] = f"[ROBOT] {self.subject}"

            html = self.body.replace("\n", "<br>")
            msg.attach(MIMEText(html, 'html', 'utf-8'))

            if self.attachments:
                for file_path in self.attachments:
                    filename = os.path.basename(file_path)
                    with open(file_path, 'rb') as attachment:
                        part = MIMEBase('application', 'octet-stream')
                        part.set_payload(attachment.read())
                    encoders.encode_base64(part)
                    part.add_header('Content-Disposition', f"attachment; filename={filename}")
                    msg.attach(part)

            all_recipients = self.to_addresses + self.cc_addresses
            smtpObj.sendmail(self.from_addr, all_recipients, msg.as_string())
            return True
        except Exception as e:
            print(f"❌ E-posta gönderim hatası: {e}")
            raise
        finally:
            try:
                if smtpObj:
                    smtpObj.quit()
            except Exception:
                pass
