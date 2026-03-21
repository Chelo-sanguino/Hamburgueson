// 1. Inicialización Global
let modalInstancia;

document.addEventListener('DOMContentLoaded', () => {
    // Inicializamos el modal de Bootstrap una sola vez
    const elModal = document.getElementById('modalProducto');
    if (elModal) {
        modalInstancia = new bootstrap.Modal(elModal);
    }
    
    // --- LÓGICA PASO 2: BLINDAJE HAMBURGUESA SEMANAL ---
    const formSemanal = document.getElementById('form-semanal');
    if (formSemanal) {
        formSemanal.onsubmit = async (e) => {
            e.preventDefault();
            
            const nombreInput = document.getElementById('admin-nombre').value;
            const precioInput = document.getElementById('admin-precio').value;

            console.log("Intentando guardar semanal:", nombreInput, precioInput);

            const payload = {
                nombre: nombreInput,
                precio: parseFloat(precioInput)
            };

            try {
                const res = await fetch('/api/admin/configurar-semanal', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(payload)
                });

                const data = await res.json();

                if (res.ok) {
                    alert("✅ " + data.mensaje);
                    formSemanal.reset();
                    cargarListaAdmin(); // Refresca la tabla para mostrar la estrella ⭐
                    cargarEstadisticas();
                } else {
                    alert("❌ Error del servidor: " + data.error);
                }
            } catch (error) {
                console.error("Error de conexión:", error);
                alert("Hubo un problema de conexión con el servidor Flask.");
            }
        };
    }
    
    cargarEstadisticas();
    cargarListaAdmin();
});

// 2. Función Maestra para el Botón "+ Nuevo Producto" y "Editar"
function abrirModal(id = null, nombre = '', categoria = '', precio = '') {
    document.getElementById('prod-id').value = id || '';
    document.getElementById('prod-nombre').value = nombre;
    document.getElementById('prod-categoria').value = categoria || 'Hamburguesas';
    document.getElementById('prod-precio').value = precio;
    
    document.getElementById('tituloModal').innerText = id ? '✏️ Editar Producto' : '🍔 Nuevo Producto';
    
    modalInstancia.show();
}

// 3. Guardar Cambios (Crea o Edita)
async function guardarProducto() {
    const id = document.getElementById('prod-id').value;
    const datos = {
        nombre: document.getElementById('prod-nombre').value,
        categoria: document.getElementById('prod-categoria').value,
        precio: parseFloat(document.getElementById('prod-precio').value)
    };

    const url = id ? `/api/productos/${id}` : '/api/productos';
    const metodo = id ? 'PUT' : 'POST';

    const res = await fetch(url, {
        method: metodo,
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(datos)
    });

    if (res.ok) {
        modalInstancia.hide();
        cargarListaAdmin(); 
        alert("¡Operación exitosa!");
    } else {
        alert("Error al procesar la solicitud");
    }
}

// 4. Quitar promoción semanal
async function desactivarSemanal() {
    if(!confirm("¿Deseas quitar la promoción semanal actual?")) return;
    
    const res = await fetch('/api/admin/quitar-semanal', { method: 'POST' });
    if(res.ok) {
        alert("Estrellas semanales desactivadas");
        location.reload();
    }
}

// 5. Estadísticas
async function cargarEstadisticas() {
    const res = await fetch('/api/stats/mensual');
    if (res.ok) {
        const data = await res.json();
        document.getElementById('stat-ganancia').innerText = `${data.ganancia_total} Bs.`;
        document.getElementById('stat-mas-vendido-nombre').innerText = data.mas_vendido.nombre;
        document.getElementById('stat-mas-vendido-cantidad').innerText = `${data.mas_vendido.cantidad} unidades`;
        document.getElementById('stat-menos-vendido-nombre').innerText = data.menos_vendido.nombre;
        document.getElementById('stat-menos-vendido-cantidad').innerText = `${data.menos_vendido.cantidad} unidades`;
    }
}

// 6. Cargar Tabla con Lógica de Estrellas
async function cargarListaAdmin() {
    const res = await fetch('/api/productos');
    const productos = await res.json();
    const tabla = document.getElementById('tabla-productos-admin');
    tabla.innerHTML = '';

    productos.forEach(p => {
        const estrella = p.es_semanal ? '<span class="text-warning fw-bold"> ⭐</span>' : '';
        
        tabla.innerHTML += `
            <tr>
                <td>${p.id}</td>
                <td class="text-white">${p.nombre}${estrella}</td>
                <td><span class="badge bg-secondary">${p.categoria}</span></td>
                <td class="text-warning fw-bold">${p.precio.toFixed(2)} Bs.</td>
                <td>
                    <button class="btn btn-sm btn-outline-warning me-1" 
                            onclick="abrirModal(${p.id}, '${p.nombre}', '${p.categoria}', ${p.precio})">✏️</button>
                    <button class="btn btn-sm btn-outline-danger" 
                            onclick="eliminarProducto(${p.id})">🗑️</button>
                </td>
            </tr>`;
    });
}

// 7. Eliminar Producto
async function eliminarProducto(id) {
    if (!confirm("⚠️ ¿Estás seguro de eliminar este producto?")) return;

    try {
        const res = await fetch(`/api/productos/${id}`, { 
            method: 'DELETE',
            headers: { 'Content-Type': 'application/json' }
        });

        const data = await res.json();

        if (res.ok) {
            alert("✅ " + data.mensaje);
            cargarListaAdmin();
        } else {
            alert("❌ Error: " + data.error);
        }
    } catch (error) {
        console.error("Error en la petición DELETE:", error);
        alert("Hubo un error al conectar con el servidor.");
    }
}

// 8. Cierre de Caja a prueba de bloqueos
async function ejecutarCierre() {
    if (!confirm("⚠️ ¿Estás seguro de cerrar la caja actual?")) return;

    // 1. Abrimos la pestaña ANTES de hablar con el servidor (Evita el bloqueo)
    const ventanaPDF = window.open('', '_blank');
    ventanaPDF.document.write('<h2>Generando reporte de cierre... por favor espere.</h2>');

    try {
        const res = await fetch('/api/caja/cerrar', { method: 'POST' });
        const data = await res.json();

        if (res.ok) {
            // 2. Si el servidor nos dio el ID, redirigimos la pestaña al PDF
            if (data.caja_id) {
                ventanaPDF.location.href = `/api/caja/ticket_cierre/${data.caja_id}`;
            } else {
                ventanaPDF.close();
                alert("Error: El servidor no envió el ID de la caja.");
            }

            // 3. Pequeña pausa para asegurar la carga, luego recargamos el panel
            setTimeout(() => {
                location.reload();
            }, 1000);

        } else {
            ventanaPDF.close();
            alert(data.error || "Error al cerrar la caja");
        }
    } catch (error) {
        ventanaPDF.close();
        console.error(error);
        alert("Error de conexión con el servidor.");
    }
}

// Cargar opciones en los selectores de promos
async function cargarOpcionesPromo() {
    const res = await fetch('/api/productos');
    const productos = await res.json();
    const b1 = document.getElementById('promo-burger-1');
    const b2 = document.getElementById('promo-burger-2');
    
    // Filtramos solo para que muestre hamburguesas
    const hamburguesas = productos.filter(p => p.categoria === 'Hamburguesas');
    
    let opciones = '<option value="">Selecciona...</option>';
    hamburguesas.forEach(h => {
        opciones += `<option value="${h.nombre}">${h.nombre}</option>`;
    });

    if(b1 && b2) {
        b1.innerHTML = opciones;
        b2.innerHTML = opciones;
    }
}
// Llamamos a la función al cargar la página
document.addEventListener('DOMContentLoaded', cargarOpcionesPromo);

// Guardar la Promo Diaria
const formPromo = document.getElementById('form-promo-diaria');
if (formPromo) {
    formPromo.onsubmit = async (e) => {
        e.preventDefault();
        const burger1 = document.getElementById('promo-burger-1').value;
        const burger2 = document.getElementById('promo-burger-2').value;
        const precio = document.getElementById('promo-precio').value;

        // El truco: Fusionamos los nombres
        const nombrePromo = `PROMO: ${burger1} + ${burger2}`;

        // Reutilizamos tu ruta de creación de productos
        const res = await fetch('/api/productos', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                nombre: nombrePromo,
                precio: parseFloat(precio),
                categoria: 'Promocion' // Nueva categoría especial
            })
        });

        if (res.ok) {
            alert("¡Promoción Diaria creada con éxito!");
            location.reload();
        }
    };
}