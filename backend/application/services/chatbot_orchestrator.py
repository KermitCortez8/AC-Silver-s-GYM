# Módulo: application.services.chatbot_orchestrator
# Pipeline de 9 pasos ordenados deterministas para el Chatbot (FastAPI).
# Fuente: spec.md §2 y contracts/control.md.
from __future__ import annotations

from datetime import date, datetime, timezone
from typing import Any, Callable, Optional
from uuid import uuid4

from application.schemas.chatbot_schemas import (
    ChatRequest,
    ChatResponse,
    ContactBlock,
    NoticeBlock,
    QuickReply,
    ScheduleItem,
    ScheduleListBlock,
    TextBlock,
)
from domain.services.chatbot_actions import (
    ACCIONES_PERMITIDAS,
    autorizar_accion,
    es_accion_prohibida,
)
from domain.services.chatbot_budget import ChatbotBudgetController
from domain.services.chatbot_expiration import ChatbotExpirationController
from domain.services.chatbot_permissions import (
    ContextoUsuario,
    detectar_intento_datos_terceros,
    detectar_suplantacion_rol,
    evaluar_sesion,
)
from domain.services.chatbot_privacy import (
    contiene_datos_sensibles_entrada,
    enmascarar_datos_sensibles_salida,
)
from domain.services.chatbot_rate_limiter import ChatbotRateLimiter, obtener_clave_sujeto
from infrastructure.chatbot_config import ChatbotSettings
from infrastructure.repositories.chatbot_repository import MemoryChatbotRepository


DEFAULT_QUICK_REPLIES = [
    QuickReply(label="Horario del gimnasio", action="gym_hours"),
    QuickReply(label="Horario de atención", action="attention_hours"),
    QuickReply(label="Actividades y cupos", action="activities"),
    QuickReply(label="Productos de la tienda", action="products"),
    QuickReply(label="Hablar con una persona", action="contact_human"),
]


class ChatbotOrchestrator:
    def __init__(
        self,
        settings: ChatbotSettings,
        repository: MemoryChatbotRepository,
        budget_controller: ChatbotBudgetController,
        rate_limiter: ChatbotRateLimiter,
        expiration_controller: ChatbotExpirationController,
        llm_caller: Optional[Callable[[str, list[dict[str, str]]], tuple[str, int]]] = None,
    ) -> None:
        self.settings = settings
        self.repo = repository
        self.budget = budget_controller
        self.rate_limiter = rate_limiter
        self.expiration = expiration_controller
        self.llm_caller = llm_caller

    def procesar_mensaje(
        self,
        request: ChatRequest,
        authorization_header: Optional[str] = None,
        ip_real: Optional[str] = None,
        ahora: Optional[datetime] = None,
    ) -> ChatResponse:
        now = ahora or datetime.now(timezone.utc)
        today = now.date()

        # ---------------------------------------------------------
        # ETAPA 1: Identificar sujeto con JWT (HU-CB11, RN-01)
        # ---------------------------------------------------------
        contexto, error_jwt = evaluar_sesion(authorization_header)

        if error_jwt == "jwt_expirado":
            self.repo.record_security_event(
                tipo_evento="jwt_expirado",
                conversacion_id=request.conversation_id,
                ip_hmac=ip_real,
                detalle={"motivo": "Token expirado durante la sesión"},
            )
            return ChatResponse(
                conversation_id=request.conversation_id or str(uuid4()),
                state="session_expired",
                blocks=[
                    NoticeBlock(
                        kind="session_expired",
                        text="Tu sesión expiró. Inicia sesión para continuar consultando tus datos personales.",
                    )
                ],
                quick_replies=DEFAULT_QUICK_REPLIES,
            )

        if error_jwt == "jwt_invalido":
            self.repo.record_security_event(
                tipo_evento="jwt_invalido",
                conversacion_id=request.conversation_id,
                ip_hmac=ip_real,
            )
            return ChatResponse(
                conversation_id=request.conversation_id or str(uuid4()),
                state="session_expired",
                blocks=[
                    NoticeBlock(
                        kind="session_expired",
                        text="Sesión inválida o corrupta. Por favor inicia sesión nuevamente.",
                    )
                ],
                quick_replies=DEFAULT_QUICK_REPLIES,
            )

        # ---------------------------------------------------------
        # GESTIÓN DE CONVERSACIÓN & INACTIVIDAD (HU-CB16, EX-14)
        # ---------------------------------------------------------
        cid = request.conversation_id
        if cid:
            exp_check = self.expiration.verificar_inactividad(cid, ahora=now)
            if exp_check.expirada:
                # Si expiró, se crea una nueva conversación limpia con nuevo UUID
                conv = self.repo.create_conversation(
                    cliente_id=contexto.cliente_id,
                    tipo_sujeto=contexto.tipo_sujeto,
                    ip_hmac=ip_real,
                )
                cid = conv["id"]
        else:
            conv = self.repo.create_conversation(
                cliente_id=contexto.cliente_id,
                tipo_sujeto=contexto.tipo_sujeto,
                ip_hmac=ip_real,
            )
            cid = conv["id"]

        # ---------------------------------------------------------
        # ETAPA 2: Validar Rate Limit de Mensajes (HU-CB14, RN-10)
        # ---------------------------------------------------------
        clave, tipo_sujeto = obtener_clave_sujeto(contexto, ip_real, self.settings.ip_hmac_secret)
        rl_res = self.rate_limiter.verificar_y_consumir(clave, tipo_sujeto, ahora=now)

        if not rl_res.permitido:
            self.repo.record_security_event(
                tipo_evento="limite_mensajes_superado",
                conversacion_id=cid,
                cliente_id=contexto.cliente_id,
                tipo_sujeto=tipo_sujeto,
                detalle={"ventana": rl_res.ventana_afectada, "reintento": rl_res.retry_after_seconds},
            )
            return ChatResponse(
                conversation_id=cid,
                state="rate_limited",
                blocks=[
                    NoticeBlock(
                        kind="rate_limit",
                        text=f"Has superado el límite de mensajes permitidos. Podrás enviar otro mensaje en {rl_res.retry_after_seconds} segundos.",
                        retry_in_seconds=rl_res.retry_after_seconds,
                    )
                ],
                quick_replies=[],
                retry_after_seconds=rl_res.retry_after_seconds,
            )

        # ---------------------------------------------------------
        # ETAPA 3: Validar Longitud máxima (HU-CB14) -> Ya en ChatRequest Pydantic
        # ---------------------------------------------------------

        # ---------------------------------------------------------
        # ETAPA 4: Filtrar datos sensibles en entrada (HU-CB12, RN-07)
        # ---------------------------------------------------------
        if contiene_datos_sensibles_entrada(request.message):
            self.repo.record_security_event(
                tipo_evento="datos_sensibles_entrada",
                conversacion_id=cid,
                cliente_id=contexto.cliente_id,
                tipo_sujeto=tipo_sujeto,
                detalle={"alerta": "Tarjeta o contraseña detectada en mensaje de entrada"},
            )
            return ChatResponse(
                conversation_id=cid,
                state="ok",
                blocks=[
                    TextBlock(
                        text="Por tu seguridad, no compartas contraseñas, PINs ni datos de tarjetas bancarias en el chat. Ningún dato confidencial ha sido guardado."
                    )
                ],
                quick_replies=DEFAULT_QUICK_REPLIES,
            )

        # Detección de intento de extracción de datos ajenos (EX-13)
        if detectar_intento_datos_terceros(request.message):
            self.repo.record_security_event(
                tipo_evento="acceso_datos_tercero",
                conversacion_id=cid,
                cliente_id=contexto.cliente_id,
                tipo_sujeto=tipo_sujeto,
            )
            return ChatResponse(
                conversation_id=cid,
                state="ok",
                blocks=[
                    TextBlock(
                        text="No se encontró información correspondiente a la consulta solicitada."
                    )
                ],
                quick_replies=DEFAULT_QUICK_REPLIES,
            )

        # ---------------------------------------------------------
        # ETAPA 5: Verificar Presupuesto de Tokens (HU-CB15, RN-11)
        # ---------------------------------------------------------
        budget_state = self.budget.consultar_estado(clave, tipo_sujeto, today)
        modo_basico = budget_state.modo_basico

        # ---------------------------------------------------------
        # ETAPA 7: Re-validar Acción con Lista Cerrada (HU-CB13, RN-04, RN-05)
        # ---------------------------------------------------------
        if es_accion_prohibida(request.message):
            self.repo.record_security_event(
                tipo_evento="accion_no_permitida",
                conversacion_id=cid,
                cliente_id=contexto.cliente_id,
                tipo_sujeto=tipo_sujeto,
                detalle={"mensaje": "Intento de acción administrativa prohibida"},
            )
            return ChatResponse(
                conversation_id=cid,
                state="forbidden",
                blocks=[
                    TextBlock(
                        text="Esta gestión debe realizarse directamente con nuestro personal en recepción o administración."
                    ),
                    ContactBlock(),
                ],
                quick_replies=DEFAULT_QUICK_REPLIES,
            )

        # Si el mensaje pide una acción específica
        accion_solicitada = request.action
        if accion_solicitada:
            auth_accion = autorizar_accion(
                accion_solicitada,
                contexto,
                confirmado=request.confirmed,
            )
            if not auth_accion.autorizada:
                return ChatResponse(
                    conversation_id=cid,
                    state="forbidden",
                    blocks=[
                        TextBlock(text=auth_accion.motivo_rechazo or "Acción no permitida."),
                        ContactBlock(),
                    ],
                    quick_replies=DEFAULT_QUICK_REPLIES,
                )

            if auth_accion.requiere_confirmacion:
                self.repo.set_pending_action(cid, {"accion": accion_solicitada})
                return ChatResponse(
                    conversation_id=cid,
                    state="ok",
                    blocks=[
                        TextBlock(
                            text=f"¿Confirmas que deseas proceder con la {accion_solicitada.replace('_', ' ')}?"
                        )
                    ],
                    quick_replies=[
                        QuickReply(label="Sí, confirmar", action=accion_solicitada),
                        QuickReply(label="Cancelar", action="contact_human"),
                    ],
                )

        # ---------------------------------------------------------
        # ETAPA 6: Invocación al LLM o Modo Básico Degradado
        # ---------------------------------------------------------
        tokens_consumidos = 0
        texto_generado = ""

        if modo_basico:
            texto_generado = "Estamos operando en modo esencial para garantizar disponibilidad. Puedes consultar nuestros horarios y servicios a continuación:"
            blocks: list[Any] = [
                NoticeBlock(
                    kind="basic_mode",
                    text="Nuestros servicios avanzados están en mantenimiento preventivo. Opciones disponibles:",
                ),
                TextBlock(text=texto_generado),
            ]
        else:
            # Llamada al LLM con timeout y reintento
            if self.llm_caller:
                def call_wrapper():
                    return self.llm_caller(request.message, [])

                res_call, exito_llm = self.expiration.ejecutar_llamada_llm_con_reintento(call_wrapper)
                if not exito_llm:
                    return ChatResponse(
                        conversation_id=cid,
                        state="slow",
                        blocks=[
                            TextBlock(
                                text="El servicio está tardando más de lo habitual. Puedes intentar nuevamente o comunicarte con recepción:"
                            ),
                            ContactBlock(),
                        ],
                        quick_replies=DEFAULT_QUICK_REPLIES,
                    )
                texto_generado, tokens_consumidos = res_call
                blocks = [TextBlock(text=texto_generado)]
            else:
                texto_generado = "Hola, soy Silver. Puedo brindarte información sobre horarios, actividades y productos."
                blocks = [TextBlock(text=texto_generado)]

        # ---------------------------------------------------------
        # ETAPA 8: Enmascarar PII en la salida (HU-CB12, RN-07)
        # ---------------------------------------------------------
        texto_sanitizado = enmascarar_datos_sensibles_salida(texto_generado)
        for b in blocks:
            if isinstance(b, TextBlock):
                b.text = enmascarar_datos_sensibles_salida(b.text)

        # ---------------------------------------------------------
        # ETAPA 9: Persistencia segura e Historial (CUS30 Paso 9)
        # ---------------------------------------------------------
        self.repo.touch_conversation(cid)
        self.repo.add_message(
            cid,
            rol="usuario",
            contenido=request.message,
            accion_detectada=request.action,
        )
        self.repo.add_message(
            cid,
            rol="asistente",
            contenido=texto_sanitizado,
            tokens_consumidos=tokens_consumidos if tokens_consumidos > 0 else None,
        )

        if tokens_consumidos > 0:
            self.budget.registrar_consumo(clave, tipo_sujeto, today, tokens_consumidos)

        return ChatResponse(
            conversation_id=cid,
            state="basic_mode" if modo_basico else "ok",
            blocks=blocks,
            quick_replies=DEFAULT_QUICK_REPLIES,
        )
