#!/bin/bash

# Iniciar el backend (Flask) en una terminal
gnome-terminal -- bash -c "python app.py; exec bash"

# Iniciar el frontend (Angular) con el proxy en otra terminal
gnome-terminal -- bash -c "cd ../frontend && ng serve --proxy-config proxy.conf.json; exec bash" 