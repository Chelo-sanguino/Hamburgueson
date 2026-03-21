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

// 8. Cierre de Caja
async function ejecutarCierre() {
    if (!confirm("¿Estás seguro de cerrar la caja actual?")) return;

    const res = await fetch('/api/caja/cerrar', { method: 'POST' });
    const data = await res.json();

    if (res.ok) {
        const r = data.resumen;
        alert(`--- REPORTE DE CIERRE ---
        Ventas Efectivo: ${r.ventas_efectivo} Bs.
        Ventas QR: ${r.ventas_qr} Bs.
        Ventas Tarjeta: ${r.ventas_tarjeta} Bs.
        -------------------------
        SALDO TOTAL EN CAJA: ${r.total_en_caja} Bs.`);
        location.reload();
    }
}