# AC Silver's GYM - Sistema de Gestión

Aplicación móvil desarrollada con React Native y Expo para la gestión integral del gimnasio AC Silver's GYM.

## Características

### 📱 Funcionalidades Principales

1. **Gestión de Usuarios**
   - Registro de nuevos miembros
   - Actualización de información de usuarios
   - Eliminación de usuarios
   - Visualización de todos los miembros registrados
   - Gestión de tipos de membresía

2. **Control de Asistencia**
   - Registro de entrada de miembros
   - Historial de asistencias
   - Estadísticas de asistencia diaria
   - Visualización por fecha

3. **Gestión de Inventario**
   - Registro de equipamiento y productos
   - Control de cantidades
   - Alertas de stock bajo
   - Categorización de artículos
   - Ubicación de artículos en el gimnasio

4. **Panel de Inicio**
   - Estadísticas en tiempo real
   - Acceso rápido a todas las funcionalidades
   - Vista general del gimnasio



##

### Pasos de Instalación

1. Instalar dependencias:
```bash
npm install
```

3. Ejecutar la aplicación:

```bash
# Para web
npm run web
```

## 💾 Almacenamiento de Datos

Actualmente, la aplicación utiliza almacenamiento en memoria (volátil) para demostración. En futuras versiones se implementará:
- AsyncStorage para persistencia local
- Integración con backend/API REST
- Base de datos en la nube

## 📝 Próximas Mejoras

- [ ] Implementar AsyncStorage para persistencia de datos con mongo
- [ ] Agregar autenticación de usuarios
- [ ] Integrar con backend (API REST)
- [ ] Agregar reportes y gráficas
- [ ] Implementar notificaciones push
- [ ] Agregar fotografías de usuarios
- [ ] Sistema de pagos de membresías
- [ ] Rutinas de entrenamiento personalizadas

