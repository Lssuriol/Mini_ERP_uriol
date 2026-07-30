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
