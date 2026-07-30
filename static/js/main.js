/*
 * Utilidades generales de la interfaz del Mini ERP.
 */

document.addEventListener('DOMContentLoaded', function () {
    // Cierra automáticamente los mensajes/alertas después de unos segundos.
    var alertas = document.querySelectorAll('.alerta');
    alertas.forEach(function (alerta) {
        setTimeout(function () {
            alerta.style.transition = 'opacity 0.4s ease';
            alerta.style.opacity = '0';
            setTimeout(function () { alerta.remove(); }, 400);
        }, 5000);
    });

    // Lógica para el menú móvil
    var btnMenu = document.getElementById('btn-menu-lateral');
    var barraLateral = document.querySelector('.barra-lateral');
    var overlay = document.getElementById('overlay-sidebar');

    if (btnMenu && barraLateral && overlay) {
        function alternarMenu() {
            barraLateral.classList.toggle('barra-lateral--abierta');
            overlay.classList.toggle('activo');
        }

        btnMenu.addEventListener('click', alternarMenu);
        overlay.addEventListener('click', alternarMenu);
    }

    // Adaptabilidad de tablas para vista móvil (inyecta data-labels)
    var tablas = document.querySelectorAll('.tabla-datos');
    tablas.forEach(function(tabla) {
        var headers = Array.from(tabla.querySelectorAll('thead th')).map(th => th.innerText);
        var filas = tabla.querySelectorAll('tbody tr');
        filas.forEach(function(fila) {
            var celdas = fila.querySelectorAll('td');
            celdas.forEach(function(celda, indice) {
                if(headers[indice] && !celda.classList.contains('tabla-vacia')) {
                    celda.setAttribute('data-label', headers[indice]);
                }
            });
        });
    });
});

/** Lee el valor de una cookie por su nombre (usado para el token CSRF). */
function obtenerCookie(nombre) {
    var valorCookie = null;
    if (document.cookie && document.cookie !== '') {
        var cookies = document.cookie.split(';');
        for (var i = 0; i < cookies.length; i++) {
            var cookie = cookies[i].trim();
            if (cookie.substring(0, nombre.length + 1) === (nombre + '=')) {
                valorCookie = decodeURIComponent(cookie.substring(nombre.length + 1));
                break;
            }
        }
    }
    return valorCookie;
}

/** Formatea un número como moneda en Soles (S/). */
function formatearMoneda(valor) {
    return 'S/ ' + Number(valor).toFixed(2);
}
