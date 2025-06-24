#!/bin/bash

# Buat direktori untuk cache dan RPZ
mkdir -p /dev/shm/kresd-cache
mkdir -p /dev/shm/kresd-rpz

# Set permission agar knot-resolver bisa akses
chown -R knot-resolver:knot-resolver /dev/shm/kresd-cache /dev/shm/kresd-rpz
chmod 750 /dev/shm/kresd-cache /dev/shm/kresd-rpz

# Copy file konfigurasi RPZ dan CSV dari sumber
cp -f /opt/knot-update/*.rpz /dev/shm/kresd-rpz/
cp -f /opt/knot-update/*.csv /dev/shm/kresd-rpz/
chown knot-resolver:knot-resolver /dev/shm/kresd-rpz/*
chmod 644 /dev/shm/kresd-rpz/*
