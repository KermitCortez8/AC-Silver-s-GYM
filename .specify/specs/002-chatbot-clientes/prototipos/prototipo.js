/* Prototipo local: datos y respuestas fijos, sin IA, red, almacenamiento o API. */
(() => {
  'use strict';
  const $ = (selector) => document.querySelector(selector);
  const CASES = {
    preregistro: { id: 'CU-CHAT-01', title: 'Preregistro asistido', objective: 'Como visitante, quiero conocer los planes y completar mi preregistro con ayuda del asistente.', criteria: ['CA-01', 'CA-02', 'CA-07', 'CA-08'], rule: 'El chat orienta. Los datos personales se completan en el formulario. Pagar y activar son pasos distintos.', caption: 'Conocer el plan y dar el primer paso', scenarios: [['normal', 'Flujo normal'], ['sin-ia', 'IA no disponible']], greeting: '¡Hola! Soy el asistente de Silver’s GYM. Te ayudo a conocer los planes y dar tu primer paso. ¿Por dónde empezamos?' },
    acceso: { id: 'CU-CHAT-02', title: 'Ingreso a la plataforma', objective: 'Como cliente, quiero ingresar y entender qué hacer si mi cuenta todavía no está habilitada.', criteria: ['CA-03', 'CA-07', 'CA-09'], rule: 'El formulario valida el acceso. El asistente no recibe contraseñas ni puede activar una cuenta.', caption: 'Entrar y continuar con confianza', scenarios: [['normal', 'Flujo normal'], ['pendiente', 'Cuenta pendiente de activación'], ['vencida', 'Membresía vencida'], ['sin-ia', 'IA no disponible']], greeting: '¿Ya formas parte de Silver’s GYM? Ingresa con el formulario para continuar. Tu contraseña se completa allí, fuera de esta conversación.' },
    matricula: { id: 'CU-CHAT-03', title: 'Consulta y matrícula en horarios', objective: 'Como cliente habilitado, quiero elegir una sesión y confirmar personalmente mi matrícula.', criteria: ['CA-04', 'CA-05', 'CA-06', 'CA-07'], rule: 'Consultar no reserva un cupo. La matrícula exige revisar fecha y hora y pulsar Confirmar matrícula.', caption: 'Elegir una clase, revisar y confirmar', scenarios: [['normal', 'Flujo normal'], ['cupo', 'Último cupo ocupado'], ['incierto', 'Respuesta perdida al confirmar'], ['sin-ia', 'IA no disponible']], greeting: '¡Vamos a encontrar tu próxima clase! Elige un servicio y una fecha. Después podrás revisar la sesión antes de confirmar tu matrícula.' },
  };
  const SCREENS = {
    planes: ['P01', 'Planes y bienvenida', 'Oferta de ejemplo y acciones para comenzar.'],
    registro: ['P02', 'Formulario de preregistro', 'Los datos personales se completan fuera del chat.'],
    pago: ['P03', 'Continuidad del preregistro', 'Solicitud, pago y activación son estados distintos.'],
    acceso: ['P04', 'Acceso a la plataforma', 'El asistente acompaña al formulario de acceso.'],
    bloqueado: ['P05', 'Cuenta no habilitada', 'Una restricción de acceso no se salta desde el chat.'],
    panel: ['P06', 'Panel de cliente', 'Acciones propias tras un ingreso simulado.'],
    horarios: ['P07', 'Búsqueda de horarios', 'Servicio, fecha concreta y sesiones de ejemplo.'],
    confirmacion: ['P08', 'Revisión de matrícula', 'La decisión final siempre corresponde al cliente.'],
    exito: ['P09', 'Mi horario', 'Resultado de ejemplo e inscripción única en esta demostración.'],
    cupo: ['P10', 'Cupo agotado', 'La disponibilidad puede cambiar antes de confirmar.'],
    incierto: ['P10', 'Resultado por verificar', 'Consultar las inscripciones antes de permitir un reintento.'],
  };
  let activeCase = 'preregistro';
  const PROGRAMMING = [
    ['PG01', 'Reglas', 'Validación y acciones locales; controles de servidor pendientes.'],
    ['PG02', 'IA', 'Respuestas fijas en el prototipo; integración del proveedor pendiente.'],
    ['PG03', 'Interfaz', 'Navegación funcional; integración de componentes Vue pendiente.'],
  ];
  let scenario = 'normal';
  let screen = 'planes';
  let plan = 'mensual';
  let service = 'Funcional';
  let classDate = '2026-11-05';
  let busy = false;
  let booked = false;
  let revision = 0;
  let messages = [];
  const prices = { mensual: ['Mensual', '30 días', 80], trimestral: ['Trimestral', '90 días', 210] };
  const formatDate = () => new Intl.DateTimeFormat('es-PE', { day: 'numeric', month: 'long', year: 'numeric', timeZone: 'America/Lima' }).format(new Date(`${classDate}T12:00:00-05:00`));
  const action = (label, name, variant = 'primary-button full-width') => `<button type="button" class="${variant}" data-action="${name}">${label}<span aria-hidden="true">→</span></button>`;
  const statusRow = (label, value) => `<div class="status-row"><span>${label}</span><strong>${value}</strong></div>`;
  const intro = (kicker, title, text) => `<p class="stage-kicker">${kicker}</p><h2 tabindex="-1">${title}</h2><p class="stage-description">${text}</p>`;
  const sessionSummary = () => `<div class="status-card">${statusRow('Servicio', service)}${statusRow('Fecha', formatDate())}${statusRow('Hora', '18:00 – 19:00')}${statusRow('Lugar', 'Sala funcional · Sede principal')}</div>`;

  function addMessage(text, role = 'assistant', actions = []) {
    messages.push({ text, role, actions });
    if (messages.length > 8) messages = messages.slice(-8);
    renderMessages();
  }
  function renderMessages() {
    const list = $('#messages');
    list.replaceChildren();
    messages.forEach((message) => {
      const wrap = document.createElement('div');
      wrap.className = `message ${message.role}`;
      const label = document.createElement('div');
      label.className = 'message-label';
      label.textContent = message.role === 'user' ? 'TÚ' : 'ASISTENTE SILVER';
      const bubble = document.createElement('div');
      bubble.className = 'bubble';
      bubble.textContent = message.text;
      wrap.append(label, bubble);
      if (message.actions.length) {
        const buttons = document.createElement('div');
        buttons.className = 'message-buttons';
        message.actions.forEach(([labelText, actionName]) => {
          const button = document.createElement('button');
          button.type = 'button';
          button.textContent = labelText;
          button.dataset.action = actionName;
          buttons.append(button);
        });
        wrap.append(buttons);
      }
      list.append(wrap);
    });
    list.scrollTop = list.scrollHeight;
  }
  function renderSidebar() {
    const current = CASES[activeCase];
    $('#use-case-id').textContent = current.id;
    $('#spec-title').textContent = current.title;
    $('#spec-objective').textContent = current.objective;
    $('#spec-rule').textContent = current.rule;
    $('#criteria').replaceChildren(...current.criteria.map((id) => {
      const tag = document.createElement('span');
      tag.textContent = id;
      return tag;
    }));
    $('#screen-caption').textContent = current.caption;
    const programming = [...PROGRAMMING, activeCase === 'matricula'
      ? ['PG05', 'Horarios / matrícula', 'Consulta y confirmación simuladas; conexión a sesiones y matrícula reales pendiente.']
      : ['PG04', 'Preregistro / acceso', 'Formularios y acceso simulados; conexión a servicios existentes pendiente.']];
    $('#programming-tags').replaceChildren(...programming.map(([id, label, description]) => {
      const tag = document.createElement('span');
      tag.textContent = `${id} · ${label}`;
      tag.title = description;
      return tag;
    }));
    document.querySelectorAll('[data-case]').forEach((button) => {
      if (button.dataset.case === activeCase) button.setAttribute('aria-current', 'step');
      else button.removeAttribute('aria-current');
    });
    $('#scenario').replaceChildren(...current.scenarios.map(([value, label]) => {
      const option = document.createElement('option');
      option.value = value;
      option.textContent = label;
      option.selected = value === scenario;
      return option;
    }));
    const actions = activeCase === 'preregistro' ? [['Ver planes', 'plans'], ['Quiero registrarme', 'register']]
      : activeCase === 'acceso' ? [['Cómo ingresar', 'login'], ['Necesito ayuda', 'help']]
        : [['Buscar horarios', 'schedules'], ['Mi horario', 'my-schedule']];
    const quick = $('#quick-actions');
    quick.replaceChildren(...actions.map(([text, name]) => {
      const button = document.createElement('button');
      button.type = 'button';
      button.textContent = text;
      button.dataset.action = name;
      return button;
    }));
    $('#chat-status').innerHTML = scenario === 'sin-ia' ? '<span></span> Ayuda guiada disponible' : '<span></span> Demostración guiada';
  }

  function renderStage(focus = false) {
    const root = $('#prototype-stage');
    const selected = prices[plan];
    let html = '';
    switch (screen) {
      case 'planes':
        html = intro('EMPIEZA TU RECORRIDO', 'Tu próximo paso.<br>Tu mejor versión.', 'Conoce nuestros planes y encuentra el que acompaña tu ritmo. El asistente está aquí para ayudarte.')
          + '<p class="section-label">Planes de ejemplo</p><div class="plan-list">'
          + Object.entries(prices).map(([key, value]) => `<button class="plan-card ${plan === key ? 'selected' : ''}" data-plan="${key}" aria-pressed="${plan === key}"><span class="plan-icon">${key === 'mensual' ? '↗' : '✦'}</span><span class="plan-name">${value[0]}<small>Acceso al gimnasio · ${value[1]}</small></span><span class="plan-price">S/ ${value[2]}<small>por ${value[1]}</small></span></button>`).join('')
          + '</div>' + action('Abrir preregistro', 'register') + '<p class="service-note"><span>✓</span> Conoce el plan antes de completar tus datos.</p>' + action('Ya tengo una cuenta', 'login', 'text-button');
        break;
      case 'registro':
        html = intro('TU PRIMER PASO', 'Hagamos espacio<br>para tu objetivo.', 'Completa el formulario para continuar. El asistente te acompaña sin pedirte estos datos en la conversación.')
          + `<div class="selected-plan">Plan seleccionado<strong>${selected[0]} · S/ ${selected[2]}</strong></div>`
          + '<form id="registration-form"><div class="form-grid"><label class="field wide">Nombre<input name="nombre" required maxlength="50" autocomplete="off" placeholder="Nombre de ejemplo"></label><label class="field wide">Correo<input name="correo" type="email" required maxlength="50" pattern="[^@]+@[^@]+\\.com" autocomplete="off" placeholder="demo@example.com"></label><label class="field">DNI<input name="dni" required inputmode="numeric" pattern="[0-9]{8}" maxlength="8" autocomplete="off" data-digits placeholder="00000000"></label><label class="field">Teléfono<input name="telefono" required inputmode="numeric" pattern="[0-9]{9}" maxlength="9" autocomplete="off" data-digits placeholder="900000000"></label><label class="field wide">Contraseña de prueba<input name="password" type="password" required minlength="6" maxlength="50" autocomplete="new-password" placeholder="Solo para esta demostración"></label></div><p class="form-hint">Usa datos ficticios. <button type="button" data-action="autofill">Completar con un ejemplo</button></p><button class="primary-button full-width" type="submit">Continuar al pago <span aria-hidden="true">→</span></button></form>' + action('Volver a planes', 'plans', 'text-button');
        break;
      case 'pago':
        html = '<div class="success-icon">✓</div>' + intro('PREREGISTRO DE EJEMPLO', 'Un paso más<br>cerca de empezar.', 'Así se mostraría la continuidad de tu solicitud. El pago se completa en la pasarela y la activación se realiza después.')
          + '<div class="progress-list"><div class="progress-step done"><span class="dot">✓</span><span>Datos del preregistro<br><strong>Completados en el formulario</strong></span></div><div class="progress-step"><span class="dot">2</span><span>Pago del plan<br><strong>Pendiente en esta demostración</strong></span></div><div class="progress-step"><span class="dot">3</span><span>Activación de la cuenta<br><strong>Después del pago confirmado</strong></span></div></div>'
          + action('Ver cómo sería el acceso', 'login') + '<p class="form-hint">Esta pantalla no abre una pasarela ni realiza un cobro.</p>';
        break;
      case 'acceso':
        html = intro('BIENVENIDO DE NUEVO', 'Tu esfuerzo<br>tiene su espacio.', 'Ingresa para consultar tus horarios y continuar tu entrenamiento. Usa únicamente datos de ejemplo.')
          + '<form id="login-form"><div class="form-grid"><label class="field wide">Correo<input name="correo" type="email" required maxlength="50" value="demo@example.com" autocomplete="off"></label><label class="field wide">Contraseña de prueba<input name="password" type="password" required minlength="6" maxlength="50" value="demo1234" autocomplete="off"></label></div><div class="login-note"><span>Acceso de demostración</span><span>Datos ficticios</span></div><button class="primary-button full-width" type="submit">Simular ingreso <span aria-hidden="true">→</span></button></form><div class="divider">o continúa con</div><button class="google-button" data-action="google"><strong>G</strong> Google · simulación</button>';
        break;
      case 'bloqueado':
        html = '<div class="success-icon warning">!</div>' + (scenario === 'vencida'
          ? intro('ACCESO DE EJEMPLO', 'Retomemos<br>tu entrenamiento.', 'Tu membresía de ejemplo aparece vencida. El acceso privado requiere una membresía pagada, vigente y activada.')
          : intro('ACCESO DE EJEMPLO', 'Casi todo listo.<br>Falta la activación.', 'Tu cuenta de ejemplo está pendiente de activación. El pago confirmado y la activación son pasos diferentes.'))
          + '<div class="status-card">' + statusRow('Acceso', '<span class="status-tag pending">No habilitado</span>') + statusRow('Siguiente paso', scenario === 'vencida' ? 'Consultar renovación' : 'Esperar la activación') + '</div>'
          + action('Volver al acceso', 'login') + action('Consultar planes', 'plans', 'text-button');
        break;
      case 'panel':
        html = intro('MI ESPACIO', 'Volvamos<br>a movernos.', 'Este es el panel de un cliente habilitado de ejemplo. El asistente puede orientarte sobre tus próximas clases.')
          + '<div class="account-pill">✓ Cuenta de ejemplo habilitada · Membresía vigente</div><div class="status-card">' + statusRow('Plan', 'Mensual') + statusRow('Estado', '<span class="status-tag">Activo · Ejemplo</span>') + '</div>'
          + action('Buscar horarios', 'schedules') + action('Cerrar sesión de ejemplo', 'logout', 'text-button');
        break;
      case 'horarios':
        html = intro('TU PRÓXIMA CLASE', 'Encuentra tu ritmo.<br>Elige tu horario.', 'Busca una sesión por servicio y fecha. Revisarás los detalles antes de confirmar tu matrícula.')
          + `<div class="filter-grid"><label class="field">Servicio<select id="service"><option${service === 'Funcional' ? ' selected' : ''}>Funcional</option><option${service === 'Musculación' ? ' selected' : ''}>Musculación</option></select></label><label class="field">Fecha<input id="class-date" type="date" value="${classDate}" min="2026-11-04" max="2026-11-30" required></label></div>`
          + `<div class="session-card"><div class="session-type">SESIÓN DE EJEMPLO</div><div class="session-card-heading"><h3>${service}</h3><span class="status-tag">${booked ? 'Ya inscrito' : '3 cupos'}</span></div><div class="session-meta"><span>◷ 18:00 – 19:00</span><span>↗ Sala funcional</span></div><p class="session-capacity">${formatDate()} · Información simulada</p>${action(booked ? 'Ver mi horario' : 'Revisar sesión', booked ? 'my-schedule' : 'review', 'secondary-button')}</div><p class="service-note"><span>i</span>Consultar una sesión no reserva el cupo.</p>`;
        break;
      case 'confirmacion':
        html = intro('ANTES DE CONFIRMAR', 'Este espacio<br>puede ser tuyo.', 'Revisa el servicio, la fecha y la hora. Solo se intentará la matrícula cuando pulses el botón de confirmación.')
          + sessionSummary() + '<div class="confirmation-note">La disponibilidad se vuelve a comprobar al confirmar. La propuesta del asistente todavía no es una matrícula.</div>'
          + `<button class="primary-button full-width" data-action="confirm"${busy ? ' disabled' : ''}>${busy ? 'Comprobando…' : 'Confirmar matrícula'}<span aria-hidden="true">→</span></button>` + action('Elegir otra sesión', 'schedules', 'text-button');
        break;
      case 'exito':
        html = '<div class="success-icon">✓</div>' + intro('MI HORARIO · EJEMPLO', 'Tu próxima clase<br>ya tiene lugar.', 'La demostración registra una sola inscripción local. Aquí se mostraría el resultado verificado por el servidor en el producto final.')
          + sessionSummary() + '<div class="account-pill">✓ Matrícula simulada · Una inscripción en esta sesión</div>'
          + action('Volver a horarios', 'schedules') + action('Cerrar sesión de ejemplo', 'logout', 'text-button');
        break;
      case 'cupo':
        html = '<div class="success-icon warning">!</div>' + intro('DISPONIBILIDAD ACTUALIZADA', 'Esta vez,<br>el cupo se adelantó.', 'Este escenario simula que otro cliente ocupó el último cupo antes de la confirmación. No se creó una matrícula.')
          + sessionSummary() + action('Buscar otra sesión', 'schedules');
        break;
      case 'incierto':
        html = '<div class="success-icon warning">↻</div>' + intro('RESULTADO POR VERIFICAR', 'Primero revisemos<br>tu inscripción.', 'Se simula una respuesta perdida al confirmar. Antes de intentar de nuevo, hay que consultar si la matrícula ya se registró.')
          + sessionSummary() + '<div class="confirmation-note">No hay un reintento automático. Esta demostración resolverá la consulta con una inscripción de ejemplo ya registrada.</div>' + action('Consultar mi inscripción', 'reconcile');
        break;
    }
    root.innerHTML = html;
    $('#screen-code').textContent = SCREENS[screen][0];
    $('#screen-purpose').textContent = SCREENS[screen][2];
    root.setAttribute('aria-label', SCREENS[screen][1]);
    if (focus) root.querySelector('h2')?.focus({ preventScroll: true });
  }
  function showScreen(next, focus = true) {
    if (busy && next !== 'confirmacion') { revision += 1; busy = false; }
    screen = next;
    renderStage(focus);
  }
  function openCase(key, nextScenario = 'normal') {
    revision += 1;
    activeCase = Object.hasOwn(CASES, key) ? key : 'preregistro';
    scenario = nextScenario;
    busy = false;
    booked = false;
    messages = [];
    $('#message').value = '';
    screen = activeCase === 'preregistro' ? 'planes' : activeCase === 'acceso' ? 'acceso' : 'horarios';
    renderSidebar();
    renderStage();
    addMessage(scenario === 'sin-ia' ? 'La conversación con IA no está disponible en este escenario. Puedes seguir usando los botones y formularios para completar el recorrido.' : CASES[activeCase].greeting, 'assistant', activeCase === 'preregistro' ? [['Ver los planes', 'plans'], ['Quiero registrarme', 'register']] : activeCase === 'acceso' ? [['Abrir formulario de acceso', 'login']] : [['Buscar una sesión', 'schedules']]);
    if (location.hash !== `#${activeCase}`) location.hash = activeCase;
  }
  function handleAction(name) {
    switch (name) {
      case 'plans':
        if (activeCase !== 'preregistro') openCase('preregistro');
        showScreen('planes');
        addMessage('Estos planes son datos de ejemplo del prototipo. Elige uno para ver cómo continuarías al preregistro.', 'assistant', [['Abrir preregistro', 'register']]);
        break;
      case 'register':
        if (activeCase !== 'preregistro') openCase('preregistro');
        showScreen('registro');
        addMessage('Completa tus datos en el formulario. Después podrás continuar al pago por el flujo del gimnasio. No escribas tu DNI o contraseña en el chat.');
        break;
      case 'login':
        if (activeCase !== 'acceso') openCase('acceso');
        showScreen('acceso');
        break;
      case 'autofill': {
        const form = $('#registration-form');
        if (!form) break;
        const values = { nombre: 'Cliente de ejemplo', correo: 'demo@example.com', dni: '00000000', telefono: '900000000', password: 'demo1234' };
        Object.entries(values).forEach(([key, value]) => { form.elements[key].value = value; });
        break;
      }
      case 'google':
      case 'sign-in':
        if (scenario === 'pendiente' || scenario === 'vencida') {
          showScreen('bloqueado');
          addMessage(scenario === 'pendiente' ? 'La cuenta de ejemplo espera activación. El asistente puede orientar, pero no activar la cuenta.' : 'La membresía de ejemplo está vencida. El asistente no puede habilitar el acceso privado ni modificar tu membresía.');
        } else {
          messages = [];
          renderMessages();
          showScreen('panel');
          addMessage('Ingreso simulado completado. Desde tu panel puedes consultar clases y revisar tu horario.', 'assistant', [['Buscar horarios', 'schedules']]);
        }
        break;
      case 'schedules':
        if (activeCase !== 'matricula') openCase('matricula');
        showScreen('horarios');
        break;
      case 'review':
        if (activeCase !== 'matricula') break;
        showScreen('confirmacion');
        addMessage(`Has elegido ${service} para el ${formatDate()}, de 18:00 a 19:00. Revisa la tarjeta y pulsa Confirmar matrícula si deseas continuar. Todavía no estás inscrito.`);
        break;
      case 'confirm': {
        if (activeCase !== 'matricula' || screen !== 'confirmacion' || busy || booked) break;
        busy = true;
        const pendingRevision = revision;
        renderStage();
        setTimeout(() => {
          if (pendingRevision !== revision) return;
          busy = false;
          if (scenario === 'cupo') {
            showScreen('cupo');
            addMessage('El escenario devuelve cupo agotado. No se creó una matrícula. Puedes buscar otra sesión.');
          } else if (scenario === 'incierto') {
            showScreen('incierto');
            addMessage('No se pudo verificar la respuesta. Consulta primero tus inscripciones; no se repetirá la matrícula automáticamente.');
          } else {
            booked = true;
            showScreen('exito');
            addMessage('Matrícula simulada completada. Mi horario muestra la sesión seleccionada. En el producto final este mensaje dependerá de una respuesta verificada del servidor.');
          }
        }, 450);
        break;
      }
      case 'my-schedule':
        if (activeCase !== 'matricula') break;
        if (booked) showScreen('exito');
        else addMessage('En esta demostración todavía no has confirmado una matrícula.', 'assistant', [['Buscar una sesión', 'schedules']]);
        break;
      case 'reconcile':
        if (screen !== 'incierto') break;
        booked = true;
        showScreen('exito');
        addMessage('La consulta simulada encontró una inscripción para esa sesión. Se muestra el resultado sin volver a enviar la matrícula.');
        break;
      case 'logout':
        openCase('acceso');
        addMessage('Sesión de ejemplo cerrada. Se borraron la conversación anterior y las selecciones pendientes.');
        break;
      case 'help':
        addMessage('Puedo ayudarte con planes, preregistro, acceso, horarios y matrícula. Las cuentas pendientes o vencidas mantienen las reglas de acceso del gimnasio.');
        break;
    }
  }
  document.addEventListener('click', (event) => {
    const caseButton = event.target.closest('[data-case]');
    if (caseButton) return openCase(caseButton.dataset.case);
    const planButton = event.target.closest('[data-plan]');
    if (planButton && Object.hasOwn(prices, planButton.dataset.plan)) { plan = planButton.dataset.plan; return renderStage(); }
    const actionButton = event.target.closest('[data-action]');
    if (actionButton && !actionButton.disabled) handleAction(actionButton.dataset.action);
  });
  document.addEventListener('submit', (event) => {
    if (event.target.id === 'registration-form') {
      event.preventDefault();
      if (!event.target.reportValidity()) return;
      showScreen('pago');
      addMessage('El preregistro de ejemplo está preparado. El pago se realiza en la pasarela y la activación es un paso posterior. Esta demostración no realiza ningún cobro.');
    }
    if (event.target.id === 'login-form') { event.preventDefault(); if (event.target.reportValidity()) handleAction('sign-in'); }
  });
  document.addEventListener('input', (event) => {
    if (event.target.matches('[data-digits]')) event.target.value = event.target.value.replace(/\D/g, '').slice(0, Number(event.target.maxLength));
  });
  document.addEventListener('change', (event) => {
    if (event.target.id === 'service') { service = event.target.value === 'Musculación' ? 'Musculación' : 'Funcional'; renderStage(); }
    if (event.target.id === 'class-date') {
      const value = event.target.value;
      if (/^2026-11-(?:0[4-9]|[12][0-9]|30)$/.test(value)) { classDate = value; renderStage(); }
    }
  });
  $('#scenario').addEventListener('change', (event) => openCase(activeCase, event.target.value));
  $('#reset').addEventListener('click', () => openCase(activeCase));
  $('#chat-form').addEventListener('submit', (event) => {
    event.preventDefault();
    const input = $('#message');
    const text = input.value.trim().slice(0, 150);
    if (!text) return;
    input.value = '';
    if (/@|\b(?:\d[ -]?){8,}\b|contrase(?:ñ|n)a|password|token|tarjeta/i.test(text)) {
      addMessage('Completa tus datos personales y credenciales en los formularios. El asistente puede orientarte sobre los pasos sin recibir esos datos.');
      return;
    }
    addMessage(text, 'user');
    if (scenario === 'sin-ia') return addMessage('En este escenario la IA no está disponible. Continúa con los botones de ayuda guiada.');
    if (/activar|cobrar|sql|ignora|administrador|otra persona|otro cliente/i.test(text)) return addMessage('Puedo orientar sobre registro, acceso y horarios. No puedo activar cuentas, cobrar, cambiar permisos o consultar datos de otras personas.');
    if (/confirm|inscr[ií]b|matric[uú]lame/i.test(text)) return addMessage('La matrícula requiere revisar el resumen y pulsar Confirmar matrícula. Un mensaje de chat no confirma la inscripción.', 'assistant', activeCase === 'matricula' ? [['Buscar horarios', 'schedules']] : []);
    if (/plan|precio|promoci[oó]n/i.test(text)) return handleAction('plans');
    if (/registr|inscribir/i.test(text)) return handleAction('register');
    if (/ingres|acced|sesi[oó]n|entrar/i.test(text)) return handleAction('login');
    if (/horario|clase|funcional|musculaci[oó]n/i.test(text)) return handleAction('schedules');
    handleAction('help');
  });
  window.addEventListener('hashchange', () => {
    const key = location.hash.slice(1);
    if (Object.hasOwn(CASES, key) && key !== activeCase) openCase(key);
  });
  openCase(location.hash.slice(1));
})();
