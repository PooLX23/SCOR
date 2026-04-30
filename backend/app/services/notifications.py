import logging
import re

import httpx

from app.core.config import settings

logger = logging.getLogger('uvicorn.error')


class NotificationService:
    def __init__(self) -> None:
        self.enabled = all(
            [
                settings.graph_client_id,
                settings.graph_client_secret,
                settings.entra_tenant_id,
                settings.graph_mail_sender_user,
                settings.windykacja_group_id,
            ]
        )

    def _token(self) -> str:
        token_url = f'https://login.microsoftonline.com/{settings.entra_tenant_id}/oauth2/v2.0/token'
        data = {
            'client_id': settings.graph_client_id,
            'client_secret': settings.graph_client_secret,
            'grant_type': 'client_credentials',
            'scope': 'https://graph.microsoft.com/.default',
        }
        response = httpx.post(token_url, data=data, timeout=15)
        response.raise_for_status()
        return response.json()['access_token']

    @staticmethod
    def _is_email(value: str | None) -> bool:
        return bool(value and re.match(r'^[^@\s]+@[^@\s]+\.[^@\s]+$', value))

    def _resolve_recipient_email(self, token: str) -> str | None:
        recipient = settings.windykacja_group_id
        if self._is_email(recipient):
            return recipient
        if not recipient:
            return None
        try:
            url = f'https://graph.microsoft.com/v1.0/groups/{recipient}?$select=mail'
            response = httpx.get(url, headers={'Authorization': f'Bearer {token}'}, timeout=15)
            response.raise_for_status()
            group_mail = response.json().get('mail')
            if self._is_email(group_mail):
                return group_mail
            logger.error('WINDYKACJA_GROUP_ID points to group without mail address: %s', recipient)
            return None
        except Exception as exc:  # noqa: BLE001
            logger.exception('Resolving windykacja group mail failed: %s', exc)
            return None

    def notify_new_application(self, application_id: int, applicant_label: str, submitted_by: str) -> None:
        if not self.enabled:
            logger.info('Email notification disabled or incomplete Graph settings.')
            return

        subject = f'Nowy wniosek SCOR #{application_id}'
        logo_html = (
            f'<img src="{settings.notification_logo_url}" alt="SIXT" '
            'style="max-height:42px; display:block; margin:0 auto 12px auto;" />'
            if settings.notification_logo_url
            else '<div style="font-weight:800;font-size:24px;letter-spacing:1px;color:#ff5f00;">SIXT</div>'
        )
        html = (
            '<!doctype html>'
            '<html><body style="margin:0;padding:0;background:#0b0b0b;font-family:Arial,sans-serif;color:#f5f5f5;">'
            '<table role="presentation" width="100%" cellspacing="0" cellpadding="0" style="background:#0b0b0b;padding:24px 12px;">'
            '<tr><td align="center">'
            '<table role="presentation" width="600" cellspacing="0" cellpadding="0" '
            'style="max-width:600px;background:#121212;border:1px solid #2a2a2a;border-radius:16px;overflow:hidden;">'
            '<tr><td style="background:linear-gradient(90deg,#ff5f00,#ff8c42);height:6px;"></td></tr>'
            '<tr><td style="padding:22px 24px 10px 24px;text-align:center;">'
            f'{logo_html}'
            '<div style="font-size:12px;letter-spacing:2px;color:#ff9e66;font-weight:700;">SCORING • SIXT</div>'
            '<h2 style="margin:10px 0 0 0;color:#ffffff;font-size:22px;">Nowy wniosek scoringowy</h2>'
            '</td></tr>'
            '<tr><td style="padding:8px 24px 20px 24px;">'
            '<p style="margin:0 0 14px 0;color:#d6d6d6;font-size:14px;line-height:1.55;">'
            'W systemie został utworzony nowy wniosek wymagający obsługi przez zespół Windykacji.'
            '</p>'
            '<table role="presentation" width="100%" cellspacing="0" cellpadding="0" '
            'style="background:#1b1b1b;border:1px solid #2e2e2e;border-radius:10px;">'
            f'<tr><td style="padding:12px 14px;color:#f5f5f5;font-size:14px;"><strong>ID wniosku:</strong> #{application_id}</td></tr>'
            f'<tr><td style="padding:12px 14px;color:#f5f5f5;font-size:14px;border-top:1px solid #2e2e2e;"><strong>Wnioskodawca:</strong> {applicant_label}</td></tr>'
            f'<tr><td style="padding:12px 14px;color:#f5f5f5;font-size:14px;border-top:1px solid #2e2e2e;"><strong>Utworzył:</strong> {submitted_by}</td></tr>'
            '</table>'
            '</td></tr>'
            '<tr><td style="padding:0 24px 24px 24px;text-align:center;">'
            f'<a href="{settings.app_public_url}" '
            'style="display:inline-block;background:#ff5f00;color:#ffffff;text-decoration:none;font-weight:700;'
            'padding:11px 18px;border-radius:10px;">Przejdź do panelu SCOR</a>'
            '</td></tr>'
            '<tr><td style="padding:0 24px 20px 24px;text-align:center;color:#8e8e8e;font-size:12px;">'
            'Wiadomość automatyczna — prosimy na nią nie odpowiadać.'
            '</td></tr>'
            '</table></td></tr></table></body></html>'
        )
        try:
            token = self._token()
            recipient_email = self._resolve_recipient_email(token)
            if not recipient_email:
                logger.error('Cannot send new application email: recipient address unresolved.')
                return
            payload = {
                'message': {
                    'subject': subject,
                    'body': {'contentType': 'HTML', 'content': html},
                    'toRecipients': [{'emailAddress': {'address': recipient_email}}],
                },
                'saveToSentItems': False,
            }
            url = f'https://graph.microsoft.com/v1.0/users/{settings.graph_mail_sender_user}/sendMail'
            response = httpx.post(url, headers={'Authorization': f'Bearer {token}'}, json=payload, timeout=20)
            response.raise_for_status()
            logger.info('New application email sent successfully to %s.', recipient_email)
        except httpx.HTTPStatusError as exc:
            logger.exception(
                'Sending new application email failed: %s | response=%s',
                exc,
                exc.response.text,
            )
        except Exception as exc:  # noqa: BLE001
            logger.exception('Sending new application email failed: %s', exc)
