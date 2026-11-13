"""Información pública comprobable de las páginas del gimnasio.

Revisar estas fichas cuando cambien LandingView, useLandingPage o las FAQ.
Nunca incluir datos de clientes, claves, reglas internas ni contenido de .env.
"""

PUBLIC_TOPICS = {
    "actividades": {
        "texto": (
            "Tipos de entrenamiento:\n"
            "• Fitness: entrenamiento general.\n"
            "• Musculación: trabajo de fuerza.\n"
            "• Cardio: entrenamiento de resistencia.\n"
            "• Baile: clases grupales.\n"
            "Puedes pedirme los horarios de estas actividades y te mostraré "
            "las clases publicadas."
        ),
        "enlace": ("Ver servicios", "/#servicios"),
    },
    "primer_dia": {
        "texto": (
            "Para tu primer día, la página de preguntas frecuentes recomienda:\n"
            "• Ropa cómoda.\n"
            "• Zapatillas deportivas.\n"
            "• Una botella de agua.\n"
            "• Una toalla pequeña."
        ),
        "enlace": ("Ver preguntas frecuentes", "/preguntas-frecuentes"),
    },
    "principiantes": {
        "texto": (
            "La página de preguntas frecuentes indica que no necesitas "
            "experiencia previa: hay rutinas para distintos niveles y los "
            "entrenadores te orientan desde el primer día."
        ),
        "enlace": ("Ver preguntas frecuentes", "/preguntas-frecuentes"),
    },
    "ubicacion": {
        "texto": (
            "La ubicación publicada de Silver Gym Surco es Jirón Vista "
            "Alegre 606, Lima 15056. La web indica estacionamiento cercano "
            "en la misma cuadra."
        ),
        "enlace": ("Ver ubicación", "/#ubicacion"),
    },
    "registro": {
        "texto": (
            "Para registrarte en Silver Gym:\n"
            "1. Abre la página de Registro y elige un plan de membresía.\n"
            "2. Completa tu nombre, correo, DNI y teléfono. Usa una contraseña "
            "o la opción de Google si está disponible.\n"
            "3. Revisa tus datos y pulsa «Pagar con Stripe» para ir al pago seguro.\n"
            "4. Tras confirmarse el pago, tu cuenta requerirá activación "
            "administrativa antes de que puedas ingresar.\n"
            "El chat solo te orienta; no realiza el registro ni el pago."
        ),
        "enlace": ("Ir al registro", "/registro"),
    },
    "acceso": {
        "texto": (
            "Si ya tienes una cuenta, entra desde la página de acceso. "
            "Las gestiones de tu cuenta requieren iniciar sesión; el chat "
            "público no puede ver tus datos."
        ),
        "enlace": ("Ir al acceso", "/login"),
    },
    "cupos": {
        "texto": (
            "Las clases grupales tienen cupos limitados. Para ver horarios "
            "publicados consulta Servicios; una consulta en el chat no "
            "reserva un cupo."
        ),
        "enlace": ("Ver servicios", "/#servicios"),
    },
}
