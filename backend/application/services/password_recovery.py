"""Envía un enlace personal y consume el estado de credenciales en una escritura atómica."""
from collections import OrderedDict
from hashlib import sha256
import logging
from threading import Lock
from time import monotonic
from urllib.parse import urlsplit

from application.operations.accounts import ResetPasswordCommand
from application.ports.integrations import EmailSender, PasswordRecoveryTokens
from application.services.email_templates import password_recovery_email
from domain.services.accounts_rules import internal_account_active, password_recovery_state
from domain.validation import email_address

logger = logging.getLogger(__name__)


class PasswordRecoveryLimit:
    """Acota los intentos por conexión antes de consultar cuentas o enviar correos."""

    def __init__(self):
        self.requests = OrderedDict()
        self.lock = Lock()

    def allow(self, address: str) -> bool:
        with self.lock:
            now = monotonic()
            while self.requests and next(iter(self.requests.values()))[1] <= now:
                self.requests.popitem(last=False)
            if address not in self.requests and len(self.requests) >= 4096:
                return False
            attempts, expires = self.requests.get(address, (0, now + 600))
            if attempts >= 8:
                return False
            self.requests[address] = (attempts + 1, expires)
            return True


class PasswordRecoveryService:
    def __init__(self, gym, settings, sender: EmailSender, tokens: PasswordRecoveryTokens):
        self.gym, self.settings, self.sender, self.tokens = gym, settings, sender, tokens

    def validate_request(self, correo: str) -> str:
        frontend = urlsplit(self.settings.frontend_public_url)
        if not self.settings.has_email_credentials or frontend.scheme not in {"http", "https"} or not frontend.netloc:
            raise RuntimeError("El servicio de recuperación no está configurado.")
        return email_address(correo)

    def send(self, email: str) -> None:
        try:
            internal = self.gym.get_usuario_by_email(email)
            client = self.gym.get_cliente_by_email(email)
            if internal_account_active(internal):
                if client:
                    return
                account, is_client = internal, False
            elif client:
                account, is_client = client, True
            else:
                return
            state = password_recovery_state(account)
            token = self.tokens.issue(account["id_usuario"], is_client, state)
            payload = password_recovery_email(self.settings, state[0], token)
            self.sender.send(payload, f"password-recovery:{sha256(token.encode()).hexdigest()}")
        except (RuntimeError, ValueError, OSError) as error:
            logger.warning("No se pudo enviar un enlace de recuperación (%s).", type(error).__name__)

    def reset(self, token: str, password: str) -> None:
        invalid = "El enlace de recuperación venció o ya fue utilizado. Solicita otro."
        claims = self.tokens.read(token)
        if not claims:
            raise ValueError(invalid)
        account = self.gym.account_for_session(claims["sub"], client=claims["client"])
        if not account:
            raise ValueError(invalid)
        state = password_recovery_state(account)
        if not self.tokens.matches(claims["stamp"], state):
            raise ValueError(invalid)
        client_id = int(account["id_cliente"]) if claims["client"] else None
        self.gym.executor.execute(ResetPasswordCommand(claims["sub"], client_id, state, password))
