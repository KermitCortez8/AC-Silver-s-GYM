# MOD-04 · Planes y promociones · Casos individuales

[Plan de ejecución del módulo](plan-de-pruebas.md): alcance, prioridad, entorno y criterios de aprobación.

13 casos individuales: 13 aprobados y 0 omitidos
registrados en la revisión del 2026-11-10. [Índice de módulos](../indice.md).
[Preparación, ejecución y lectura de resultados](../indice.md#cómo-leer-y-repetir-cada-caso).
[Escenarios de uso del módulo](casos-de-uso.md) y
[selectores/comandos estructurados](catalogo-pruebas.json).

## Pruebas unitarias

### Backend

#### test_promocion_cupos.py

| Caso individual | Escenario / variante original | Dado: fixtures / parámetros | Entonces: extractos del resultado esperado | Resultado registrado |
| --- | --- | --- | --- | --- |
| **CT-M04-U-BE-001** | <code>test_promocion_limite_cupos_exhaustion</code> · [test_promocion_cupos.py:5](../../../../../backend/tests/planes_promociones/unitarias/test_promocion_cupos.py#L5) | Preparación local de la función. | <code>promo&#91;"limite_cupos"&#93; == 2</code>; <code>promo&#91;"usos_actuales"&#93; == 1</code>; <code>v is not None</code> (5 en fuente). | Aprobado |

#### test_promocion_navidad.py

| Caso individual | Escenario / variante original | Dado: fixtures / parámetros | Entonces: extractos del resultado esperado | Resultado registrado |
| --- | --- | --- | --- | --- |
| **CT-M04-U-BE-002** | <code>test_prevent_promocion_overlap</code> · [test_promocion_navidad.py:20](../../../../../backend/tests/planes_promociones/unitarias/test_promocion_navidad.py#L20) | Preparación local de la función. | <code>promo1&#91;"id_promocion"&#93; &gt; 0</code>; <code>promo_mensual&#91;"id_promocion"&#93; &gt; 0</code>; <code>pytest.raises(ValueError, match="Ya existe una promoción vigente")</code> (3 en fuente). | Aprobado |
| **CT-M04-U-BE-003** | <code>test_promociones_vigentes_publicas_and_autoapply</code> · [test_promocion_navidad.py:60](../../../../../backend/tests/planes_promociones/unitarias/test_promocion_navidad.py#L60) | Preparación local de la función. | <code>len(vigentes) == 1</code>; <code>vigentes&#91;0&#93;&#91;"nombre"&#93; == "Navidad Especial"</code>; <code>vigentes&#91;0&#93;&#91;"valor_descuento"&#93; == 20.0</code> (6 en fuente). | Aprobado |

### Frontend

#### membership-plan-form.test.js

| Caso individual | Escenario / variante original | Dado: fixtures / parámetros | Entonces: extractos del resultado esperado | Resultado registrado |
| --- | --- | --- | --- | --- |
| **CT-M04-U-FE-001** | <code>las duraciones disponibles producen planes válidos sin texto libre</code> · [membership-plan-form.test.js:5](../../../../../frontend/tests/planes_promociones/unitarias/membership-plan-form.test.js#L5) | Fixtures: <code>Preparación y dobles del archivo fuente</code> | <code>assert.deepEqual(options.map(option =&gt; option.value), &#91; '1 día', '7 días', '15 días', '30 días', '60 días', '90 días', '180 días', '365 días', &#93;)</code>; <code>assert.deepEqual(membershipPlanErrors({ name: 'Plan nuevo', duration: value, price: 80 }), {})</code> (2 en fuente). | Aprobado |
| **CT-M04-U-FE-002** | <code>las duraciones guardadas se conservan sin convertir meses, años o días</code> · [membership-plan-form.test.js:15](../../../../../frontend/tests/planes_promociones/unitarias/membership-plan-form.test.js#L15) | Fixtures: <code>Preparación y dobles del archivo fuente</code> | <code>assert.equal(options.filter(option =&gt; option.value === duration).length, 1)</code>; <code>assert.deepEqual(membershipPlanErrors({ name: 'Plan existente', duration, price: 0 }), {})</code>; <code>assert.equal(planDurationOptions('30 días').filter(option =&gt; option.value === '30 días').length, 1)</code> (4 en fuente). | Aprobado |
| **CT-M04-U-FE-003** | <code>el formulario identifica los campos obligatorios y acepta un precio cero explícito</code> · [membership-plan-form.test.js:25](../../../../../frontend/tests/planes_promociones/unitarias/membership-plan-form.test.js#L25) | Fixtures: <code>Preparación y dobles del archivo fuente</code> | <code>assert.deepEqual(Object.keys(membershipPlanErrors({ name: '', duration: '30 días', price: '' })), &#91;'name', 'price'&#93;)</code>; <code>assert.deepEqual(membershipPlanErrors({ name: 'Acceso de prueba', duration: '1 día', price: 0 }), {})</code>; <code>assert.ok(membershipPlanErrors({ name: 'Plan', duration: '30 días', price }).price)</code> (3 en fuente). | Aprobado |
| **CT-M04-U-FE-004** | <code>el formulario rechaza una duración inválida y conserva el límite de nombre de 50</code> · [membership-plan-form.test.js:33](../../../../../frontend/tests/planes_promociones/unitarias/membership-plan-form.test.js#L33) | Fixtures: <code>Preparación y dobles del archivo fuente</code> | <code>assert.deepEqual(membershipPlanErrors(plan), {})</code>; <code>assert.ok(membershipPlanErrors({ ...plan, name: 'Á'.repeat(51) }).name)</code>; <code>assert.ok(membershipPlanErrors({ ...plan, duration }).duration)</code> (3 en fuente). | Aprobado |

## Pruebas de integración

### Frontend

#### plan-directory.test.js

| Caso individual | Escenario / variante original | Dado: fixtures / parámetros | Entonces: extractos del resultado esperado | Resultado registrado |
| --- | --- | --- | --- | --- |
| **CT-M04-I-FE-001** | <code>el catálogo combina búsqueda sin tildes con disponibilidad y cuenta planes activos</code> · [plan-directory.test.js:13](../../../../../frontend/tests/planes_promociones/integracion/plan-directory.test.js#L13) | Fixtures: <code>Preparación y dobles del archivo fuente</code> | <code>assert.equal(catalog.activeCount.value, 2)</code>; <code>assert.deepEqual(catalog.filteredPlans.value.map(plan =&gt; plan.id), &#91;'pm-1'&#93;)</code>; <code>assert.equal(catalog.filteredPlans.value.length, 0)</code> (6 en fuente). | Aprobado |
| **CT-M04-I-FE-002** | <code>el orden por precio conserva cero y no altera el catálogo original</code> · [plan-directory.test.js:27](../../../../../frontend/tests/planes_promociones/integracion/plan-directory.test.js#L27) | Fixtures: <code>Preparación y dobles del archivo fuente</code> | <code>assert.deepEqual(catalog.filteredPlans.value.map(plan =&gt; plan.price), &#91;0, 80, 500&#93;)</code>; <code>assert.deepEqual(catalog.filteredPlans.value.map(plan =&gt; plan.price), &#91;500, 80, 0&#93;)</code>; <code>assert.deepEqual(catalog.plans.value.map(plan =&gt; plan.id), &#91;'pm-1', 'pm-2', 'pm-3'&#93;)</code> (3 en fuente). | Aprobado |
| **CT-M04-I-FE-003** | <code>la carga evita consultas duplicadas y finaliza el estado de espera</code> · [plan-directory.test.js:36](../../../../../frontend/tests/planes_promociones/integracion/plan-directory.test.js#L36) | Fixtures: <code>Preparación y dobles del archivo fuente</code> | <code>assert.deepEqual(options, { section: 'plans' })</code>; <code>assert.equal(catalog.loading.value, true)</code>; <code>assert.equal(calls, 1)</code> (4 en fuente). | Aprobado |
| **CT-M04-I-FE-004** | <code>un fallo de carga conserva los planes y un reintento limpia el error</code> · [plan-directory.test.js:49](../../../../../frontend/tests/planes_promociones/integracion/plan-directory.test.js#L49) | Fixtures: <code>Preparación y dobles del archivo fuente</code> | <code>assert.equal(catalog.loadError.value, 'Servicio temporalmente indisponible')</code>; <code>assert.equal(catalog.loading.value, false)</code>; <code>assert.equal(catalog.plans.value.length, 3)</code> (4 en fuente). | Aprobado |

## Pruebas de interfaz

### Frontend

#### formularios.test.js

| Caso individual | Escenario / variante original | Dado: fixtures / parámetros | Entonces: extractos del resultado esperado | Resultado registrado |
| --- | --- | --- | --- | --- |
| **CT-M04-F-FE-001** | <code>promotion saves reject duplicate clicks and retain the draft with an inline error</code> · [formularios.test.js:5](../../../../../frontend/tests/planes_promociones/interfaz/formularios.test.js#L5) | Fixtures: <code>Preparación y dobles del archivo fuente</code> | <code>assert.equal(calls, 1)</code>; <code>assert.equal(setup.isModalOpen, true)</code>; <code>assert.equal(setup.modalError, 'Sin conexión')</code> (6 en fuente). | Aprobado |
| **CT-M04-F-FE-002** | <code>promotion deletion preserves its confirmation and target after failure</code> · [formularios.test.js:26](../../../../../frontend/tests/planes_promociones/interfaz/formularios.test.js#L26) | Fixtures: <code>Preparación y dobles del archivo fuente</code> | <code>assert.equal(setup.promoToDelete.id_promocion, 1)</code>; <code>assert.equal(setup.deleteError, 'No se pudo eliminar')</code>; <code>assert.equal(setup.deleting, false)</code> (3 en fuente). | Aprobado |
