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

## 📂 Estructura del Proyecto

```
AC-Silver-s-GYM/
├── src/
│   ├── navigation/        # Configuración de navegación
│   │   └── AppNavigator.js
│   ├── screens/          # Pantallas de la aplicación
│   │   ├── HomeScreen.js
│   │   ├── UsersScreen.js
│   │   ├── AttendanceScreen.js
│   │   └── InventoryScreen.js
│   ├── components/       # Componentes reutilizables
│   │   ├── Button.js
│   │   ├── Input.js
│   │   └── Card.js
│   ├── data/            # Gestión de datos
│   │   └── storage.js
│   └── constants/       # Constantes (colores, etc.)
│       └── colors.js
├── assets/              # Recursos estáticos
├── App.js              # Punto de entrada de la aplicación
└── package.json        # Dependencias del proyecto
```

## 🚀 Instalación y Ejecución

### Requisitos Previos
- Node.js (versión 14 o superior)
- npm o yarn
- Expo CLI (opcional para desarrollo)

### Pasos de Instalación

1. Clonar el repositorio:
```bash
git clone https://github.com/KermitCortez8/AC-Silver-s-GYM.git
cd AC-Silver-s-GYM
```

2. Instalar dependencias:
```bash
npm install
```

3. Ejecutar la aplicación:

```bash
# Para web
npm run web

# Para Android (requiere Android Studio o dispositivo físico)
npm run android

# Para iOS (requiere macOS y Xcode)
npm run ios
```

## 📱 Tecnologías Utilizadas

- **React Native** - Framework para desarrollo móvil
- **Expo** - Plataforma para desarrollo y construcción
- **React Navigation** - Navegación entre pantallas
- **@expo/vector-icons** - Iconos
- **JavaScript (ES6+)** - Lenguaje de programación

## 💾 Almacenamiento de Datos

Actualmente, la aplicación utiliza almacenamiento en memoria (volátil) para demostración. En futuras versiones se implementará:
- AsyncStorage para persistencia local
- Integración con backend/API REST
- Base de datos en la nube

## 🎨 Diseño

La aplicación cuenta con:
- Interfaz intuitiva y fácil de usar
- Diseño moderno y responsivo
- Esquema de colores profesional
- Componentes reutilizables
- Iconografía consistente

## 📝 Próximas Mejoras

- [ ] Implementar AsyncStorage para persistencia de datos
- [ ] Agregar autenticación de usuarios
- [ ] Integrar con backend (API REST)
- [ ] Agregar reportes y gráficas
- [ ] Implementar notificaciones push
- [ ] Agregar fotografías de usuarios
- [ ] Sistema de pagos de membresías
- [ ] Rutinas de entrenamiento personalizadas

## 👨‍💻 Desarrollo

Este proyecto fue desarrollado siguiendo las mejores prácticas de React Native y organizado de manera modular para facilitar el mantenimiento y la escalabilidad.

## 📄 Licencia

Este proyecto es de código abierto y está disponible bajo la licencia MIT.

## 🤝 Contribuciones

Las contribuciones son bienvenidas. Por favor, abre un issue o pull request para sugerencias o mejoras.

---

Desarrollado con ❤️ para AC Silver's GYM