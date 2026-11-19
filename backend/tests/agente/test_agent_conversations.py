"""Recorridos conversacionales de v1 con catálogo y proveedor controlados."""

from application.services.agent_service import AgentService, ConversationTopics


class Catalog:
    def __init__(self):
        self.reads = []

    def planes_membresia(self):
        self.reads.append("planes")
        return [{"nombre_plan": "Plan QA", "precio": 91, "duracion": "31 días"}]

    def horarios_servicio(self, *, solo_activos):
        assert solo_activos is True
        self.reads.append("horarios")
        return [{
            "servicio": "Baile", "dia": "Lunes",
            "hora_inicio": "07:00", "hora_fin": "08:00",
        }]


class Provider:
    def __init__(self):
        self.calls = []

    def select_tool(self, message, last_topic=None):
        self.calls.append((message, last_topic))
        plain = message.casefold()
        if "plan" in plain:
            return "consultar_planes", "{}"
        if "ejercicio" in plain:
            return "consultar_informacion_publica", '{"tema":"actividades"}'
        if "cupo" in plain:
            return "consultar_informacion_publica", '{"tema":"cupos"}'
        if "one piece" in plain:
            return "fuera_de_tema", "{}"
        return None


def start():
    catalog, provider = Catalog(), Provider()
    return AgentService(catalog, provider, ConversationTopics()), catalog, provider


def ask(service, message, previous=None):
    result = service.respond(message, previous)
    if previous is not None:
        assert result["id_conversacion"] == previous
    return result


def test_conv_01_visitor_moves_from_greeting_to_registration_without_enrolment():
    service, catalog, provider = start()
    first = ask(service, "Hola")
    identifier = first["id_conversacion"]
    assert "Hola" in first["texto"]

    plan = ask(service, "¿Cuánto cuesta el plan?", identifier)
    assert "Plan QA: S/ 91 · 31 días" in plan["texto"]
    assert plan["enlaces"] == [{"texto": "Ver registro", "ruta": "/registro"}]

    schedule = ask(service, "¿Qué horarios tiene Baile?", identifier)
    assert "Baile:" in schedule["texto"]
    assert "Lunes 07:00–08:00" in schedule["texto"]

    guidance = ask(service, "¿Cómo me registro?", identifier)
    assert "Abre la página de Registro" in guidance["texto"]
    assert guidance["enlaces"] == [{"texto": "Ir al registro", "ruta": "/registro"}]

    private = ask(service, "Inscríbeme a Baile", identifier)
    assert private["estado"] == "fuera_de_alcance"
    assert "requiere usar los formularios" in private["texto"]

    thanks = ask(service, "Gracias", identifier)
    assert "De nada" in thanks["texto"]
    assert catalog.reads == ["planes", "horarios"]
    assert [message for message, _ in provider.calls] == [
        "¿Cuánto cuesta el plan?", "¿Qué horarios tiene Baile?",
    ]


def test_conv_02_activity_followup_uses_schedules_but_does_not_claim_live_capacity():
    service, catalog, provider = start()
    activities = ask(service, "¿Qué tipos de ejercicios hay?")
    identifier = activities["id_conversacion"]
    assert "Tipos de entrenamiento" in activities["texto"]

    schedules = ask(service, "¿Y los horarios?", identifier)
    assert "Baile:" in schedules["texto"]
    assert "Lunes 07:00–08:00" in schedules["texto"]

    capacity = ask(service, "¿Hay cupo en Baile el lunes?", identifier)
    assert "cupos limitados" in capacity["texto"]
    assert "hay espacio" not in capacity["texto"].casefold()
    assert "está lleno" not in capacity["texto"].casefold()
    assert catalog.reads == ["horarios"]
    assert [message for message, _ in provider.calls] == [
        "¿Qué tipos de ejercicios hay?", "¿Y los horarios?", "¿Hay cupo en Baile el lunes?",
    ]


def test_conv_03_recovery_and_personal_data_never_reach_provider_or_catalog():
    service, catalog, provider = start()
    recovery = ask(service, "Quiero recuperar mi cuenta")
    identifier = recovery["id_conversacion"]
    assert recovery["accion"] == "recuperacion_local"

    email = ask(service, "qa@example.com", identifier)
    password = ask(service, "Mi contraseña es secreto-qa", identifier)
    assert email["estado"] == password["estado"] == "bloqueado"
    assert "qa@example.com" not in email["texto"]
    assert "secreto-qa" not in password["texto"]
    assert provider.calls == []
    assert catalog.reads == []


def test_conv_04_ambiguous_off_topic_then_return_to_public_plan():
    service, catalog, provider = start()
    unclear = ask(service, "Quisiera saber algo")
    identifier = unclear["id_conversacion"]
    assert "Cuéntame un poco más" in unclear["texto"]

    first = ask(service, "¿Dónde está One Piece?", identifier)
    second = ask(service, "¿Dónde está One Piece?", identifier)
    assert first["estado"] == second["estado"] == "fuera_de_alcance"
    assert "se aleja un poco" in first["texto"]
    assert "centrémonos en Silver Gym" in second["texto"]

    plan = ask(service, "¿Cuánto cuesta el plan?", identifier)
    assert plan["estado"] == "respondida"
    assert "Plan QA: S/ 91" in plan["texto"]
    assert catalog.reads == ["planes"]
    assert len(provider.calls) == 4
