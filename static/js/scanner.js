/*
 * Lógica para la lectura de códigos de barras usando ZXing-JS
 */

var codeReader = null;
var isScanning = false;
var ultimoCodigoEscaneado = "";
var tiempoUltimoEscaneo = 0;

function initScanner(videoElementId, onDecodeCallback) {
    var botonEscanearCamara = document.getElementById('pos-btn-escanear-camara');
    var modalEscaner = document.getElementById('pos-modal-escaner');
    var botonCerrarEscaner = document.getElementById('pos-btn-cerrar-escaner');

    if (botonEscanearCamara) {
        botonEscanearCamara.addEventListener('click', function () {
            modalEscaner.style.display = 'flex';
            startScanning(videoElementId, onDecodeCallback);
        });

        botonCerrarEscaner.addEventListener('click', function () {
            stopScanning();
            modalEscaner.style.display = 'none';
        });
    }
}

function startScanning(videoElementId, onDecodeCallback) {
    if (typeof ZXing === 'undefined') {
        console.error("ZXing library no está cargada.");
        return;
    }

    if (!codeReader) {
        // Configuramos los formatos específicos de productos para evitar lecturas "basura" (falsos positivos)
        const hints = new Map();
        const formats = [
            ZXing.BarcodeFormat.EAN_13,
            ZXing.BarcodeFormat.EAN_8,
            ZXing.BarcodeFormat.UPC_A,
            ZXing.BarcodeFormat.UPC_E,
            ZXing.BarcodeFormat.CODE_128,
            ZXing.BarcodeFormat.QR_CODE
        ];
        hints.set(ZXing.DecodeHintType.POSSIBLE_FORMATS, formats);
        
        codeReader = new ZXing.BrowserMultiFormatReader(hints);
    }

    if (isScanning) return;

    // Iniciar escaneo con la cámara por defecto (trasera si es móvil)
    codeReader.decodeFromVideoDevice(null, videoElementId, function (result, err) {
        if (result) {
            var decodedText = result.getText();
            var ahora = new Date().getTime();

            // Evitar escaneos basura (falsos positivos menores a 5 caracteres)
            if (decodedText.length < 5) return;

            // Evitar escaneos duplicados del mismo producto en menos de 2 segundos
            if (decodedText === ultimoCodigoEscaneado && (ahora - tiempoUltimoEscaneo) < 2000) {
                return;
            }

            ultimoCodigoEscaneado = decodedText;
            tiempoUltimoEscaneo = ahora;

            onDecodeCallback(decodedText);
        }
        
        if (err && !(err instanceof ZXing.NotFoundException)) {
            // ZXing lanza NotFoundException continuamente cuando no detecta un código.
            // Ignoramos esa excepción específica, pero mostramos otras.
            // console.warn(err);
        }
    }).then(function () {
        isScanning = true;
    }).catch(function (err) {
        console.error("Error al iniciar la cámara con ZXing:", err);
    });
}

function stopScanning() {
    if (codeReader) {
        codeReader.reset();
        isScanning = false;
    }
}

// Función global para dar un destello de color al escáner
function flashScanner(color) {
    var container = document.querySelector('.scanner-container');
    if (container) {
        var overlay = document.createElement('div');
        overlay.style.position = 'absolute';
        overlay.style.top = '0';
        overlay.style.left = '0';
        overlay.style.width = '100%';
        overlay.style.height = '100%';
        overlay.style.backgroundColor = color || 'rgba(76, 175, 80, 0.6)';
        overlay.style.zIndex = '10';
        overlay.style.transition = 'opacity 0.4s ease-out';
        overlay.style.pointerEvents = 'none';
        container.appendChild(overlay);
        
        // Forzar renderizado
        overlay.getBoundingClientRect();
        
        overlay.style.opacity = '0';
        setTimeout(function() {
            if (container.contains(overlay)) {
                container.removeChild(overlay);
            }
        }, 400);
    }
}
