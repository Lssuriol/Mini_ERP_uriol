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
        codeReader = new ZXing.BrowserMultiFormatReader();
    }

    if (isScanning) return;

    // Iniciar escaneo con la cámara por defecto (trasera si es móvil)
    codeReader.decodeFromVideoDevice(null, videoElementId, function (result, err) {
        if (result) {
            var decodedText = result.getText();
            var ahora = new Date().getTime();

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
