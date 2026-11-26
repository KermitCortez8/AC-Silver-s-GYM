# Recuperación de contraseña

«¿Perdiste tu contraseña? Recupera tu cuenta» está debajo de «Regístrate aquí»
en el inicio de sesión. El modal acepta solo el correo. El correo de
recuperación permite crear una contraseña nueva y volver a iniciar sesión.
Solicitar otro enlace desde la pantalla de restablecimiento abre el modal.

- [Pruebas HTTP](../../../../backend/tests/identidad_acceso/integracion/test_recuperar_password.py)
  con correo simulado verificaron el envío para una cuenta identificada, la
  respuesta genérica para correos desconocidos o ambiguos, la vigencia, el uso
  único, la concurrencia y el acceso con la contraseña nueva.
- Chromium con API simulada verificó el estilo del enlace, el modal con un
  campo, la validación, el restablecimiento y la solicitud de otro enlace a
  1440 y 390 px.
- Backend aprobó 1144 pruebas y omitió 68. Frontend aprobó 459 y compiló.
- El enlace vence entre diez y veinte minutos después de emitirse, según la
  ventana de idempotencia. La operación reutiliza las tablas de cuentas y
  la transacción existente.
- El entorno local usa el remitente de prueba de Resend y `FRONTEND_PUBLIC_URL`
  apunta a localhost. El envío a clientes requiere un remitente de un dominio
  verificado y una URL accesible desde el correo del destinatario.
