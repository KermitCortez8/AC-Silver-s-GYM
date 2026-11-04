"""Solicitudes temporales: identidad verificada, precio reservado y conversión atómica."""
from datetime import datetime, timedelta, timezone

from domain.errors import EntityNotFound
from domain.money import cents
from domain.validation import required_text


def utc_now():
    return datetime.now(timezone.utc).isoformat()


def deadline(now):
    return (datetime.fromisoformat(now) + timedelta(hours=24)).isoformat()


class PreregistrationRules:
    def __init__(self, rules):
        self.context, self.accounts, self.memberships = rules.context, rules.accounts, rules.memberships

    def get(self, token):
        row = next((r for r in self.context.state.get('preregistros', []) if r['token'] == token), None)
        if not row:
            raise EntityNotFound('Preregistro no encontrado')
        return row

    def prepare(self, payload, token, now):
        state = self.context.state
        correo, dni = payload['correo'], payload['dni']
        if (self.accounts.get_cliente_by_email(correo) or self.accounts.get_cliente_by_dni(dni)
                or self.accounts.get_usuario_by_email(correo)
                or (payload.get('google_sub') and self.accounts.get_account_by_google_sub(payload['google_sub']))):
            raise ValueError('Ya existe una cuenta registrada. Inicia sesión o contacta con administración.')
        row = next((r for r in state.get('preregistros', []) if r['correo'] == correo), None)
        password = str(payload.get('password') or payload.get('contrasena') or '').strip()
        subject = str(payload.get('google_sub') or '')
        if row:
            identity_matches = (subject == row.get('google_sub') if subject else
                                self.context.passwords.verify(password, row.get('password_hash') or ''))
            if not identity_matches or row['dni'] != dni:
                raise ValueError('Ya existe una solicitud con esos datos. Utiliza las mismas credenciales.')
            if row['estado'] == 'CONVERTIDO':
                raise ValueError('El registro ya se completó. Ve a Acceso.')
            if row['estado'] == 'PENDIENTE':
                return row
        if any(r['dni'] == dni and r['correo'] != correo for r in state.get('preregistros', [])):
            raise ValueError('Ya existe una solicitud con ese DNI y otro correo.')
        if subject and any(r.get('google_sub') == subject and r['correo'] != correo for r in state.get('preregistros', [])):
            raise ValueError('Ya existe una solicitud con esta identidad de Google.')
        nombre = required_text(payload.get('nombre'))
        if not subject and len(password) < 6:
            raise ValueError('La contraseña debe tener al menos 6 caracteres')
        plan, promo_id, amount = self.memberships.reserve_public_quote(payload.get('plan') or 'MENSUAL')
        prepared = {
            'id_preregistro': row['id_preregistro'] if row else self.context.next_int_id('preregistros', 'id_preregistro'),
            'token': row['token'] if row else token,
            'intento': int(row['intento']) + 1 if row else 1,
            'nombre': nombre, 'correo': correo, 'dni': dni, 'telefono': payload['telefono'],
            'password_hash': self.context.passwords.hash(password) if not subject else '', 'google_sub': subject,
            'plan': plan, 'id_pm': plan['id_pm'], 'id_promocion': promo_id, 'monto_pago': amount,
            'estado': 'PENDIENTE', 'creado_en': now, 'expira_en': deadline(now),
            'checkout_session_id': '', 'checkout_url': '', 'id_cliente': None, 'id_membresia': None,
        }
        if row:
            row.update(prepared)
        else:
            state.setdefault('preregistros', []).append(prepared)
        return prepared

    def attach(self, token, attempt, session_id, checkout_url):
        row = self.get(token)
        if int(row['intento']) != attempt or row['estado'] == 'EXPIRADO':
            raise ValueError('El intento de pago ya no está vigente')
        if row['checkout_session_id'] and row['checkout_session_id'] != session_id:
            raise ValueError('La sesión no corresponde al preregistro')
        row.update(checkout_session_id=session_id, checkout_url=checkout_url)
        return row

    def expire(self, token, attempt, session_id):
        row = self.get(token)
        if int(row['intento']) != attempt or row['estado'] != 'PENDIENTE':
            return row
        if row['checkout_session_id'] != session_id:
            raise ValueError('La sesión no corresponde al preregistro')
        row['estado'] = 'EXPIRADO'
        promo = next((p for p in self.context.state.get('promociones', [])
                      if p['id_promocion'] == row.get('id_promocion')), None)
        if promo:
            promo['usos_actuales'] = max(0, int(promo.get('usos_actuales') or 0) - 1)
        return row

    def convert(self, token, attempt, session_id, amount):
        row = self.get(token)
        if int(row['intento']) != attempt or (row['checkout_session_id'] and row['checkout_session_id'] != session_id):
            raise ValueError('La sesión no corresponde al preregistro')
        if cents(amount) != cents(row['monto_pago']) or cents(amount) <= 0:
            raise ValueError('El importe del pago no coincide con el preregistro')
        state = self.context.state
        if row['estado'] == 'CONVERTIDO':
            client = next((c for c in state['clientes'] if c['id_cliente'] == row['id_cliente']), None)
            membership = next((m for m in state['membresia'] if m['id_membresia'] == row['id_membresia']), None)
            if not client or not membership:
                raise EntityNotFound('El cliente de este pago ya no está disponible; contacta con administración')
            return {'cliente': client, 'membresia': membership, 'plan': row['plan']}
        # Un pago verificado tardío se conserva incluso después de la caducidad local.
        if (self.accounts.get_cliente_by_email(row['correo']) or self.accounts.get_cliente_by_dni(row['dni'])
                or self.accounts.get_usuario_by_email(row['correo'])
                or (row['google_sub'] and self.accounts.get_account_by_google_sub(row['google_sub']))):
            raise ValueError('La identidad del pago requiere revisión administrativa; no se creó una cuenta duplicada')
        cid = self.context.next_int_id('clientes', 'id_cliente')
        mid = self.context.next_int_id('membresia', 'id_membresia')
        client = {k: row[k] for k in ('nombre', 'correo', 'dni', 'telefono', 'password_hash', 'google_sub')}
        client.update(id_cliente=cid, id_usuario=f'SGCLI{cid:03d}', plan=row['plan']['nombre_plan'],
                      promocion=f"promo-{row['id_promocion']}" if row['id_promocion'] else 'SIN PROMOCION',
                      estado='EN_TRAMITE', origen_registro='PUBLICO', fecha_registro=self.context.today())
        membership = dict(id_membresia=mid, id_cliente=cid, id_pm=row['id_pm'], id_promocion=row['id_promocion'],
                          monto_pago=row['monto_pago'], estado='EN_TRAMITE', estado_pago='PAGADO',
                          fecha_inicio='', fecha_fin='', metodo_pago='stripe', referencia_pago=session_id,
                          fecha_pago=self.context.today())
        state['clientes'].insert(0, client)
        state['membresia'].insert(0, membership)
        if row['estado'] == 'EXPIRADO':
            self.memberships._increment_promocion_usos(state, row['id_promocion'])
        row.update(estado='CONVERTIDO', id_cliente=cid, id_membresia=mid, checkout_session_id=session_id,
                   password_hash='', google_sub='', nombre='', telefono='', correo='', dni='')
        return {'cliente': client, 'membresia': membership, 'plan': row['plan']}
