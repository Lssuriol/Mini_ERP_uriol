/*
 * Lógica del Punto de Venta (POS).
 *
 * Mantiene el carrito en memoria (arreglo `carritoVenta`) y lo envía como
 * JSON al backend, donde `procesar_venta` se encarga de crear la venta,
 * el detalle y descontar el stock dentro de una transacción atómica.
 */

var carritoVenta = [];

document.addEventListener('DOMContentLoaded', function () {
    var campoBusqueda = document.getElementById('pos-campo-busqueda');
    var contenedorResultados = document.getElementById('pos-resultados');
    var botonRegistrarVenta = document.getElementById('pos-boton-registrar-venta');

    if (!campoBusqueda) return; // No estamos en la página del POS.

    var temporizadorBusqueda = null;

    campoBusqueda.addEventListener('focus', function () {
        var termino = campoBusqueda.value.trim();
        if (contenedorResultados.innerHTML === '' || contenedorResultados.style.display === 'none') {
            buscarProductos(termino);
            contenedorResultados.style.display = 'block';
        }
    });

    campoBusqueda.addEventListener('input', function () {
        var termino = campoBusqueda.value.trim();
        clearTimeout(temporizadorBusqueda);

        temporizadorBusqueda = setTimeout(function () {
            buscarProductos(termino);
            if (contenedorResultados.innerHTML) {
                contenedorResultados.style.display = 'block';
            }
        }, 250);
    });

    campoBusqueda.addEventListener('keydown', function (e) {
        if (e.key === 'Enter') {
            e.preventDefault();
            var termino = campoBusqueda.value.trim();
            if (!termino) return;

            clearTimeout(temporizadorBusqueda);
            
            fetch('/caja/api/productos/?q=' + encodeURIComponent(termino))
                .then(function (respuesta) { return respuesta.json(); })
                .then(function (datos) {
                    var coincidenciaExacta = datos.resultados.find(function(p) { return p.codigo === termino; });
                    
                    if (coincidenciaExacta) {
                        agregarProductoAlCarrito(coincidenciaExacta);
                        campoBusqueda.value = '';
                        contenedorResultados.style.display = 'none';
                    } else if (datos.resultados.length === 1) {
                        agregarProductoAlCarrito(datos.resultados[0]);
                        campoBusqueda.value = '';
                        contenedorResultados.style.display = 'none';
                    } else {
                        buscarProductos(termino);
                    }
                });
        }
    });

    campoBusqueda.addEventListener('blur', function () {
        setTimeout(function () {
            contenedorResultados.style.display = 'none';
        }, 200);
    });

    botonRegistrarVenta.addEventListener('click', registrarVenta);

    renderizarCarrito();

    if (typeof initScanner === 'function') {
        initScanner('pos-lector-camara', function(decodedText) {
            campoBusqueda.value = decodedText;
            var event = new KeyboardEvent('keydown', {
                key: 'Enter',
                code: 'Enter',
                which: 13,
                keyCode: 13,
                bubbles: true
            });
            campoBusqueda.dispatchEvent(event);
            
            // Dar feedback visual sutil de que se leyó
            var lector = document.getElementById('pos-lector-camara');
            if (lector) {
                lector.style.outline = '4px solid #4CAF50';
                setTimeout(function() { lector.style.outline = 'none'; }, 300);
            }
        });
    }

    var botonBuscarRuc = document.getElementById('pos-btn-buscar-ruc');
    if (botonBuscarRuc) {
        botonBuscarRuc.addEventListener('click', function() {
            var documento = document.getElementById('id_cliente_documento').value.trim();
            var mensajeEstado = document.getElementById('pos-mensaje-estado');
            var inputNombre = document.getElementById('id_cliente_nombre');
            
            if (documento.length !== 8 && documento.length !== 11) {
                mensajeEstado.textContent = 'Ingrese un DNI de 8 dígitos o un RUC de 11 dígitos para buscar.';
                mensajeEstado.className = 'alerta alerta--error';
                return;
            }
            
            var tipoConsulta = documento.length === 8 ? 'DNI' : 'RUC';
            
            botonBuscarRuc.disabled = true;
            botonBuscarRuc.innerHTML = '...';
            mensajeEstado.textContent = 'Buscando ' + tipoConsulta + ' en RENIEC/SUNAT...';
            mensajeEstado.className = 'alerta alerta--info';
            
            fetch('/caja/api/consultar-documento/?numero=' + encodeURIComponent(documento))
                .then(function(respuesta) { return respuesta.json(); })
                .then(function(datos) {
                    botonBuscarRuc.disabled = false;
                    botonBuscarRuc.innerHTML = '<i class="fi fi-rs-search"></i>';
                    if (datos.exito) {
                        inputNombre.value = datos.nombre;
                        mensajeEstado.textContent = 'Datos encontrados correctamente.';
                        mensajeEstado.className = 'alerta alerta--exito';
                    } else {
                        mensajeEstado.textContent = datos.mensaje;
                        mensajeEstado.className = 'alerta alerta--error';
                    }
                })
                .catch(function() {
                    botonBuscarRuc.disabled = false;
                    botonBuscarRuc.textContent = '🔍';
                    mensajeEstado.textContent = 'Error al consultar el RUC.';
                    mensajeEstado.className = 'alerta alerta--error';
                });
        });
    }
});

function buscarProductos(termino) {
    var contenedorResultados = document.getElementById('pos-resultados');

    fetch('/caja/api/productos/?q=' + encodeURIComponent(termino))
        .then(function (respuesta) { return respuesta.json(); })
        .then(function (datos) {
            contenedorResultados.innerHTML = '';

            if (datos.resultados.length === 0) {
                contenedorResultados.innerHTML = '<div class="pos-resultados__item">Sin resultados</div>';
            } else {
                datos.resultados.forEach(function (producto) {
                    var item = document.createElement('div');
                    item.className = 'pos-resultados__item';
                    item.style.display = 'flex';
                    item.style.alignItems = 'center';
                    item.style.gap = '10px';
                    
                    var imgHtml = producto.imagen 
                        ? '<img src="' + producto.imagen + '" style="width: 40px; height: 40px; object-fit: cover; border-radius: 4px; flex-shrink: 0;">'
                        : '<div style="width: 40px; height: 40px; background: #f1f5f9; border-radius: 4px; flex-shrink: 0; display:flex; align-items:center; justify-content:center; color:#cbd5e1;"><i class="fi fi-rs-picture"></i></div>';

                    item.innerHTML =
                        imgHtml +
                        '<div style="flex-grow: 1;">' +
                        '<div class="pos-resultados__nombre">' + producto.nombre + '</div>' +
                        '<div class="pos-resultados__meta">' + producto.codigo + ' · ' + producto.categoria +
                        ' · Stock: ' + producto.stock_actual + '</div>' +
                        '</div>' +
                        '<div style="font-weight: 600;">' + formatearMoneda(producto.precio_venta) + '</div>';
                    item.addEventListener('click', function () {
                        agregarProductoAlCarrito(producto);
                        contenedorResultados.style.display = 'none';
                        document.getElementById('pos-campo-busqueda').value = '';
                    });
                    contenedorResultados.appendChild(item);
                });
            }

            contenedorResultados.style.display = 'block';
        });
}

function agregarProductoAlCarrito(producto) {
    var lineaExistente = carritoVenta.find(function (linea) { return linea.producto_id === producto.id; });

    if (lineaExistente) {
        if (lineaExistente.cantidad < producto.stock_actual) {
            lineaExistente.cantidad += 1;
        }
    } else {
        carritoVenta.push({
            producto_id: producto.id,
            nombre: producto.nombre,
            precio_venta: parseFloat(producto.precio_venta),
            stock_actual: producto.stock_actual,
            cantidad: 1,
            imagen: producto.imagen,
        });
    }

    renderizarCarrito();
}

function actualizarCantidad(productoId, nuevaCantidad) {
    var linea = carritoVenta.find(function (l) { return l.producto_id === productoId; });
    if (!linea) return;

    nuevaCantidad = parseInt(nuevaCantidad, 10);
    if (isNaN(nuevaCantidad) || nuevaCantidad < 1) nuevaCantidad = 1;
    if (nuevaCantidad > linea.stock_actual) nuevaCantidad = linea.stock_actual;

    linea.cantidad = nuevaCantidad;
    renderizarCarrito();
}

function quitarDelCarrito(productoId) {
    carritoVenta = carritoVenta.filter(function (linea) { return linea.producto_id !== productoId; });
    renderizarCarrito();
}

function renderizarCarrito() {
    var cuerpoTabla = document.getElementById('pos-carrito-cuerpo');
    var totalVenta = 0;

    if (carritoVenta.length === 0) {
        cuerpoTabla.innerHTML = '<tr><td colspan="5" class="pos-carrito-vacio">Aún no has agregado productos.</td></tr>';
    } else {
        cuerpoTabla.innerHTML = '';
        carritoVenta.forEach(function (linea) {
            var subtotalLinea = linea.precio_venta * linea.cantidad;
            totalVenta += subtotalLinea;

            var fila = document.createElement('tr');
            fila.className = 'pos-carrito__fila';
            
            var imgHtml = linea.imagen 
                ? '<img src="' + linea.imagen + '" style="width: 32px; height: 32px; object-fit: cover; border-radius: 4px; flex-shrink: 0;">'
                : '<div style="width: 32px; height: 32px; background: #f1f5f9; border-radius: 4px; flex-shrink: 0;"></div>';

            fila.innerHTML =
                '<td><div style="display: flex; align-items: center; gap: 8px;">' + imgHtml + '<span>' + linea.nombre + '</span></div></td>' +
                '<td class="celda-numerica">' + formatearMoneda(linea.precio_venta) + '</td>' +
                '<td><input type="number" min="1" max="' + linea.stock_actual + '" value="' + linea.cantidad +
                '" class="pos-carrito__cantidad" data-producto-id="' + linea.producto_id + '"></td>' +
                '<td class="celda-numerica">' + formatearMoneda(subtotalLinea) + '</td>' +
                '<td class="celda-acciones"><button type="button" class="boton boton--secundario boton--pequeno" ' +
                'data-quitar-id="' + linea.producto_id + '">Quitar</button></td>';
            cuerpoTabla.appendChild(fila);
        });

        cuerpoTabla.querySelectorAll('.pos-carrito__cantidad').forEach(function (input) {
            input.addEventListener('change', function () {
                actualizarCantidad(parseInt(input.dataset.productoId, 10), input.value);
            });
        });

        cuerpoTabla.querySelectorAll('[data-quitar-id]').forEach(function (boton) {
            boton.addEventListener('click', function () {
                quitarDelCarrito(parseInt(boton.dataset.quitarId, 10));
            });
        });
    }

    var tasaIgv = parseFloat(document.getElementById('pos-tasa-igv').value);
    var valorVenta = totalVenta / (1 + tasaIgv);
    var igv = totalVenta - valorVenta;

    document.getElementById('pos-resumen-subtotal').textContent = formatearMoneda(valorVenta);
    document.getElementById('pos-resumen-igv').textContent = formatearMoneda(igv);
    document.getElementById('pos-resumen-total').textContent = formatearMoneda(totalVenta);

    document.getElementById('pos-boton-registrar-venta').disabled = carritoVenta.length === 0;
}

function registrarVenta() {
    var mensajeEstado = document.getElementById('pos-mensaje-estado');
    mensajeEstado.textContent = '';
    mensajeEstado.className = '';

    var tipoComprobante = document.getElementById('id_tipo_comprobante').value;
    var clienteNombre = document.getElementById('id_cliente_nombre').value.trim();
    var clienteDocumento = document.getElementById('id_cliente_documento').value.trim();
    var clienteEmail = '';
    var inputEmail = document.getElementById('id_cliente_email');
    if (inputEmail) {
        clienteEmail = inputEmail.value.trim();
    }

    if (tipoComprobante === 'FACTURA') {
        if (!clienteDocumento || !clienteNombre || clienteNombre.toLowerCase() === 'cliente varios') {
            mensajeEstado.textContent = 'Para emitir una FACTURA, es obligatorio ingresar el RUC y Razón Social del cliente.';
            mensajeEstado.className = 'alerta alerta--error';
            return;
        }
    }

    var metodoPago = document.getElementById('id_metodo_pago').value;

    if (metodoPago === 'TARJETA') {
        var totalTexto = document.getElementById('pos-resumen-total').textContent;
        document.getElementById('pos-monto-cobrar').textContent = totalTexto;
        document.getElementById('pos-modal-tarjeta').style.display = 'flex';
        return;
    }

    procesarEnvioVenta();
}

function procesarEnvioVenta(datosPOS) {
    datosPOS = datosPOS || {};
    var mensajeEstado = document.getElementById('pos-mensaje-estado');
    var boton = document.getElementById('pos-boton-registrar-venta');
    boton.disabled = true;
    boton.textContent = 'Procesando comprobante...';

    var cuerpoPeticion = {
        carrito: carritoVenta.map(function (linea) {
            return { producto_id: linea.producto_id, cantidad: linea.cantidad };
        }),
        tipo_comprobante: document.getElementById('id_tipo_comprobante').value,
        metodo_pago: document.getElementById('id_metodo_pago').value,
        cliente_nombre: document.getElementById('id_cliente_nombre').value.trim(),
        cliente_documento: document.getElementById('id_cliente_documento').value.trim(),
        cliente_email: document.getElementById('id_cliente_email') ? document.getElementById('id_cliente_email').value.trim() : '',
        pos_operador: datosPOS.pos_operador || '',
        pos_tipo_tarjeta: datosPOS.pos_tipo_tarjeta || '',
        pos_numero_autorizacion: datosPOS.pos_numero_autorizacion || '',
        pos_ultimos_digitos: datosPOS.pos_ultimos_digitos || '',
    };

    fetch('/caja/api/registrar-venta/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': obtenerCookie('csrftoken'),
        },
        body: JSON.stringify(cuerpoPeticion),
    })
        .then(function (respuesta) { return respuesta.json().then(function (datos) { return { ok: respuesta.ok, datos: datos }; }); })
        .then(function (resultado) {
            if (resultado.ok && resultado.datos.exito) {
                if (resultado.datos.estado_fe === 'ACEPTADA') {
                    mensajeEstado.textContent = 'Venta y comprobante registrados correctamente.';
                    mensajeEstado.className = 'alerta alerta--exito';
                } else if (resultado.datos.estado_fe === 'PENDIENTE' || resultado.datos.estado_fe === 'ERROR' || resultado.datos.estado_fe === 'RECHAZADA') {
                    mensajeEstado.textContent = 'Venta registrada. Comprobante pendiente de emisión.';
                    mensajeEstado.className = 'alerta alerta--info';
                } else {
                    mensajeEstado.textContent = 'Venta registrada.';
                    mensajeEstado.className = 'alerta alerta--exito';
                }
                
                setTimeout(function() {
                    window.location.href = resultado.datos.url_comprobante + '?imprimir=auto';
                }, 1500);
            } else {
                mensajeEstado.textContent = resultado.datos.mensaje || 'Ocurrió un error al registrar la venta.';
                mensajeEstado.className = 'alerta alerta--error';
                boton.disabled = false;
                boton.textContent = 'Registrar venta';
            }
        })
        .catch(function (error) {
            console.error('Error:', error);
            mensajeEstado.textContent = 'Ocurrió un error de red o de servidor.';
            mensajeEstado.className = 'alerta alerta--error';
            boton.disabled = false;
            boton.textContent = 'Registrar venta';
        });
}

// Configurar modal POS
document.addEventListener('DOMContentLoaded', function() {
    var btnCancelarPOS = document.getElementById('pos-btn-cancelar-tarjeta');
    var btnConfirmarPOS = document.getElementById('pos-btn-confirmar-tarjeta');
    var modalPOS = document.getElementById('pos-modal-tarjeta');

    if (btnCancelarPOS) {
        btnCancelarPOS.addEventListener('click', function() {
            modalPOS.style.display = 'none';
        });
    }

    if (btnConfirmarPOS) {
        btnConfirmarPOS.addEventListener('click', function() {
            var btnOriginal = document.getElementById('pos-boton-registrar-venta');
            // Cambiar el texto del botón del modal para dar feedback
            btnConfirmarPOS.disabled = true;
            btnConfirmarPOS.textContent = 'Enviando...';

            var datosPOS = {
                pos_operador: document.getElementById('pos-input-operador').value,
                pos_tipo_tarjeta: document.getElementById('pos-input-tipo-tarjeta').value,
                pos_numero_autorizacion: document.getElementById('pos-input-autorizacion').value.trim(),
                pos_ultimos_digitos: document.getElementById('pos-input-ultimos-digitos').value.trim(),
            };

            modalPOS.style.display = 'none';
            procesarEnvioVenta(datosPOS);
            
            // Restaurar modal
            setTimeout(function() {
                btnConfirmarPOS.disabled = false;
                btnConfirmarPOS.textContent = 'Confirmar Pago en POS';
            }, 1000);
        });
    }
});
