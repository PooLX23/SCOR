import logging

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

    def notify_new_application(self, application_id: int, applicant_label: str, submitted_by: str) -> None:
        if not self.enabled:
            logger.info('Email notification disabled or incomplete Graph settings.')
            return

        subject = f'Nowy wniosek SCOR #{application_id}'
        html = (
            f'<p>Utworzono nowy wniosek SCOR.</p>'
            f'<p><strong>ID:</strong> {application_id}<br/>'
            f'<strong>Wnioskodawca:</strong> {applicant_label}<br/>'
            f'<strong>Utworzył:</strong> {submitted_by}</p>'
        )
        payload = {
            'message': {
                'subject': subject,
                'body': {'contentType': 'HTML', 'content': html},
                'toRecipients': [{'emailAddress': {'address': settings.windykacja_group_id}}],
            },
            'saveToSentItems': 'false',
        }
        try:
            token = self._token()
            url = f'https://graph.microsoft.com/v1.0/users/{settings.graph_mail_sender_user}/sendMail'
            response = httpx.post(url, headers={'Authorization': f'Bearer {token}'}, json=payload, timeout=20)
            response.raise_for_status()
        except Exception as exc:  # noqa: BLE001
            logger.exception('Sending new application email failed: %s', exc)
