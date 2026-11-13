"""Información pública comprobable de las páginas del gimnasio.

Revisar estas fichas cuando cambien LandingView, useLandingPage o las FAQ.
Nunca incluir datos de clientes, claves, reglas internas ni contenido de .env.
"""

PUBLIC_TOPICS = {
    "actividades": {
        "texto": (
            "En la web se muestran Fitness (entrenamiento general), "
            "Musculación (trabajo de fuerza), Cardio (resistencia) y Baile "
            "(clases grupales). Los horarios concretos se consultan aparte."
        ),
        "enlace": ("Ver servicios", "/#servicios"),
    },
    "primer_dia": {
        "texto": (
            "Para el primer día, la página de preguntas frecuentes recomienda "
            "ropa cómoda, zapatillas deportivas, una botella de agua y una "
            "toalla pequeña."
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
            "Puedes iniciar tu preinscripción en la página de registro y "
            "elegir allí un plan. El chat no registra cuentas ni confirma pagos."
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
