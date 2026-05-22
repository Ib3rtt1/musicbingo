#!/usr/bin/env bash
# exit on error
set -o errexit

# Instalar dependencias
pip install -r requirements.txt

# Recolectar archivos estáticos (CSS, JS)
python manage.py collectstatic --no-input

# Aplicar migraciones en la base de datos de Render
python manage.py migrate