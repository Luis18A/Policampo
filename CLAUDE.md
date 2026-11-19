# PoliCampo — Sistema web de apoyo a la toma de decisiones agroecológicas

## Qué es el proyecto

Sistema web para productores e ingenieros agrónomos de Jujuy. Permite registrar fincas, cultivos y
condiciones del terreno (por formulario o croquis), obtener un diagnóstico de biodiversidad, recibir
propuestas de rediseño con corredores/franjas florales y plantas de servicio (al menos 20 % de la
superficie con hábitat natural, según Garibaldi et al.), planificar un calendario agroecológico y descargar informes técnicos.

Es un trabajo grupal universitario (Facultad de Ingeniería, UNJu). El documento completo del proyecto
está en `docs/SEMANA\\\_2\\\_1.pdf`.

## Stack

* Python + Django (proyecto nuevo, desde cero)
* PostgreSQL como base de datos (credenciales por variables de entorno, archivo `.env`, nunca en el código)
* Plantillas de Django (HTML + CSS), diseño responsive: se usa mucho desde el celular en el campo
* Idioma de la interfaz: español

## Roles

Solo hay dos roles:

* **Usuario**: productor o ingeniero agrónomo. NO se distingue entre ambos, tienen los mismos permisos.
* **Administrador**: gestiona el sistema.

(Los roles del documento son orientativos, estos son los definitivos.)

## Mi parte (Martina): autenticación + landing page

### Autenticación

* Modelo de usuario personalizado (`AUTH\\\_USER\\\_MODEL`) definido ANTES de la primera migración.
* **Registro**: con email (único) + nombre de usuario elegido (único) + contraseña. Todo usuario nuevo
se registra con rol Usuario; los administradores se crean aparte.
* **Login**: se puede entrar con nombre de usuario **o** con email, más la contraseña
(backend de autenticación personalizado).
* Logout y recuperación de contraseña por email.
* Usar el sistema de autenticación de Django (contraseñas cifradas, validadores, CSRF).
Cuidar los datos personales (Ley 25.326).

### Landing page (pantalla principal)

* Página pública, de presentación del sistema: qué es PoliCampo, beneficios, cómo funciona,
para quién es, y botones de "Registrarse" / "Iniciar sesión".
* **Si sobra tiempo**: página de inicio para el usuario logueado con accesos a los módulos
(Mis fincas, Diagnóstico, Rediseño, Informes). Esos módulos los hacen otros integrantes.

## Fuera de mi parte (no implementar, solo dejar enlaces/espacios si hace falta)

Registro de fincas y cultivos, croquis, motor de reglas/diagnóstico, propuesta de rediseño,
informes, pagos/suscripción, encuestas.

## Cómo quiero que trabajes

* Explicame lo que hacés: estoy aprendiendo Django y tengo que poder defender el código.
* Antes de cambios grandes, mostrame el plan y esperá que lo apruebe.
* Código y comentarios en español cuando sea razonable; nombres claros.
* Escribí tests para registro y login.
* Organización sugerida: apps `usuarios` (autenticación) y `principal` (landing).

