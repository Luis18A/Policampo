// Comportamiento de la cabecera.
//
// 1) Menú hamburguesa del celular: al tocar el botón, agrega o quita la clase "abierto"
//    al menú (el CSS lo muestra u oculta) y actualiza aria-expanded para lectores de pantalla.
//    Al tocar un enlace del menú, se cierra solo.
//
// 2) Cabecera transparente de la landing: mientras estás arriba de todo, la cabecera se ve
//    transparente sobre la foto. Apenas bajás (o abrís el menú), le agregamos la clase
//    "con-fondo" y recupera su fondo claro. En las demás páginas la clase no cambia nada,
//    porque las reglas del CSS solo aplican dentro de .pagina-landing.
document.addEventListener("DOMContentLoaded", function () {
    const cabecera = document.querySelector(".cabecera");
    const boton = document.querySelector("[data-boton-menu]");
    const menu = document.querySelector("[data-menu]");

    function actualizarFondo() {
        if (!cabecera) return;
        const menuAbierto = menu && menu.classList.contains("abierto");
        cabecera.classList.toggle("con-fondo", window.scrollY > 10 || menuAbierto);
    }

    function cambiarMenu(abrir) {
        menu.classList.toggle("abierto", abrir);
        boton.setAttribute("aria-expanded", String(abrir));
        actualizarFondo();
    }

    if (boton && menu) {
        boton.addEventListener("click", function () {
            cambiarMenu(!menu.classList.contains("abierto"));
        });
        menu.querySelectorAll("a").forEach(function (enlace) {
            enlace.addEventListener("click", function () { cambiarMenu(false); });
        });
    }

    // Avisos flotantes (mensajes de Django): se cierran con la X o solos a los 6 segundos.
    document.querySelectorAll(".mensaje").forEach(function (aviso) {
        function cerrar() {
            aviso.classList.add("oculto");                       // animación de salida (CSS)
            setTimeout(function () { aviso.remove(); }, 300);    // y después lo sacamos
        }
        const botonCerrar = aviso.querySelector("[data-cerrar-mensaje]");
        if (botonCerrar) botonCerrar.addEventListener("click", cerrar);
        setTimeout(cerrar, 6000);
    });

    // "passive: true" le avisa al navegador que no vamos a frenar el scroll: así va más fluido.
    window.addEventListener("scroll", actualizarFondo, { passive: true });
    actualizarFondo();

    // 3) Sección activa en el menú (lo que en inglés se llama "scrollspy").
    //    Buscamos los enlaces del menú que apuntan a una sección (#que-es, #como-funciona...)
    //    y usamos IntersectionObserver: el navegador nos avisa cuando una sección cruza
    //    la franja del medio de la pantalla. Esa sección es "la actual" y su enlace
    //    recibe la clase "activo" (el CSS le dibuja el subrayado).
    const enlaces = Array.from(document.querySelectorAll('.menu-enlaces a[href*="#"]'));
    const secciones = enlaces
        .map(function (enlace) { return document.getElementById(enlace.hash.slice(1)); })
        .filter(Boolean);
    if (!secciones.length || !("IntersectionObserver" in window)) return;

    function marcarActivo(id) {
        enlaces.forEach(function (enlace) {
            const esActivo = enlace.hash === "#" + id;
            enlace.classList.toggle("activo", esActivo);
            if (esActivo) {
                enlace.setAttribute("aria-current", "true");   // para lectores de pantalla
            } else {
                enlace.removeAttribute("aria-current");
            }
        });
    }

    // rootMargin recorta la zona observada a una franja angosta en el medio de la pantalla
    // (45 % arriba y 50 % abajo quedan afuera).
    const observador = new IntersectionObserver(function (entradas) {
        entradas.forEach(function (entrada) {
            if (entrada.isIntersecting) marcarActivo(entrada.target.id);
        });
    }, { rootMargin: "-45% 0px -50% 0px" });
    secciones.forEach(function (seccion) { observador.observe(seccion); });

    // Casos especiales que la franja del medio no detecta:
    // - arriba de todo (en la portada): ninguna sección activa;
    // - abajo de todo: la última sección (Contacto) puede no llegar a la mitad de la pantalla.
    window.addEventListener("scroll", function () {
        const primera = secciones[0].getBoundingClientRect().top;
        const alFinal = window.innerHeight + window.scrollY >= document.documentElement.scrollHeight - 4;
        if (alFinal) {
            marcarActivo(secciones[secciones.length - 1].id);
        } else if (primera > window.innerHeight / 2) {
            marcarActivo(null);
        }
    }, { passive: true });
});
