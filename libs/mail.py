import smtplib
from email.message import EmailMessage

import libs.config


_mail_cfg = None


def _get_mail_config() -> dict:
    global _mail_cfg

    if _mail_cfg:
        return _mail_cfg

    _mail_cfg = {
        'SMTP_HOST': libs.config.get_value('SYSTEM', 'MAIL_SMTP_HOST'),
        'SMTP_PORT': int(libs.config.get_value('SYSTEM', 'MAIL_SMTP_PORT')),
        'ADDRESS': libs.config.get_value('SYSTEM', 'MAIL_ADDRESS'),
        'PASSWORD': libs.config.get_value('SYSTEM', 'MAIL_PASSWORD')
    }
    return _mail_cfg


def send_msg(dest: str, subject: str, msg: str):
    """Send email message

    Args:
        dest: destination address
        subject: email subject
        msg: email contents in plain text
    """
    mail_cfg = _get_mail_config()

    mail_msg = EmailMessage()
    mail_msg.set_content(msg)
    mail_msg['Subject'] = subject
    mail_msg['From'] = mail_cfg['ADDRESS']
    mail_msg['To'] = dest

    smtp_svr = smtplib.SMTP(host=mail_cfg['SMTP_HOST'], port=mail_cfg['SMTP_PORT'])
    smtp_svr.starttls()
    smtp_svr.login(mail_cfg['ADDRESS'], mail_cfg['PASSWORD'])
    smtp_svr.sendmail(mail_msg['From'], mail_msg['To'], mail_msg.as_string())
    smtp_svr.quit()
