@echo off
title Lanzador Hamburgueson - POS
echo 🍔 Iniciando el sistema de Hamburgueson...

:: 1. Intentar abrir XAMPP automáticamente (opcional)
:: start /d "C:\xampp" xampp-control.exe

echo ⏳ Esperando a que MySQL este listo...
timeout /t 3

:: 2. Instalar librerias si es la primera vez (solo por seguridad)
pip install flask flask-sqlalchemy reportlab

:: 3. Abrir el Punto de Venta en el navegador predeterminado
start http://127.0.0.1:5000

:: 4. Ejecutar el servidor de Flask
echo 🚀 Servidor activo en http://127.0.0.1:5000
python backend/app.py

pause