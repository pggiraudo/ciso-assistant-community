#!/usr/bin/env bash
# ---------------------------------------------------------------------------
# Instalador guiado (Mac / Linux) para el asistente de Declaración de
# Aplicabilidad del ENS. Comprueba e instala Python 3 y rclone, y ayuda a
# conectar tu Google Drive. No instala nada sin preguntarte antes.
# ---------------------------------------------------------------------------
set -u

say()  { printf "\n\033[1;34m==>\033[0m %s\n" "$1"; }
ok()   { printf "\033[1;32m  OK:\033[0m %s\n" "$1"; }
warn() { printf "\033[1;33m  !!\033[0m %s\n" "$1"; }
ask()  { local p="$1"; local r; read -r -p "$p [s/N]: " r; [ "${r:-N}" = "s" ] || [ "${r:-N}" = "S" ]; }

# Detectar gestor de paquetes
PKG=""
if   command -v brew    >/dev/null 2>&1; then PKG="brew"
elif command -v apt-get >/dev/null 2>&1; then PKG="apt"
elif command -v dnf     >/dev/null 2>&1; then PKG="dnf"
elif command -v pacman  >/dev/null 2>&1; then PKG="pacman"
fi

install_pkg() {  # $1 = nombre del paquete
  case "$PKG" in
    brew)   brew install "$1" ;;
    apt)    sudo apt-get update && sudo apt-get install -y "$1" ;;
    dnf)    sudo dnf install -y "$1" ;;
    pacman) sudo pacman -S --noconfirm "$1" ;;
    *)      return 1 ;;
  esac
}

say "1) Comprobando Python 3"
if command -v python3 >/dev/null 2>&1; then
  ok "Python 3 ya está instalado ($(python3 --version 2>&1))"
else
  warn "No se ha encontrado Python 3."
  if [ -n "$PKG" ] && ask "¿Instalar Python 3 ahora con $PKG?"; then
    [ "$PKG" = "brew" ] && install_pkg python || install_pkg python3
  else
    warn "Instálalo manualmente desde https://www.python.org/downloads/"
  fi
fi

say "2) Comprobando rclone (para subir a Google Drive)"
if command -v rclone >/dev/null 2>&1; then
  ok "rclone ya está instalado ($(rclone version 2>/dev/null | head -1))"
else
  warn "No se ha encontrado rclone."
  if ask "¿Instalar rclone ahora?"; then
    if [ -n "$PKG" ]; then
      install_pkg rclone || true
    fi
    if ! command -v rclone >/dev/null 2>&1; then
      warn "Intentando con el instalador oficial de rclone (requiere contraseña sudo)..."
      curl -fsSL https://rclone.org/install.sh | sudo bash || \
        warn "No se pudo instalar automáticamente. Ver https://rclone.org/install/"
    fi
  fi
fi

say "3) Conectar tu Google Drive con rclone"
if command -v rclone >/dev/null 2>&1; then
  if rclone listremotes 2>/dev/null | grep -q '^gdrive:'; then
    ok "Ya tienes un remoto 'gdrive:' configurado."
  else
    cat <<'EOT'
  Vas a crear el remoto de Google Drive. Cuando rclone pregunte, responde:
    - n) New remote
    - name>            gdrive
    - Storage>         drive          (Google Drive)
    - client_id>       (Enter, vacío)
    - client_secret>   (Enter, vacío)
    - scope>           1              (acceso completo)
    - el resto>        Enter
    - Use auto config? y  -> se abrirá el navegador para iniciar sesión
    - Shared Drive?    n
    - Confirmar:       y, y luego q para salir
EOT
    if ask "¿Lanzar 'rclone config' ahora?"; then
      rclone config
    fi
  fi
else
  warn "rclone no disponible: podrás generar el archivo, pero tendrás que subirlo a Drive a mano."
fi

say "Instalación finalizada."
echo "Ahora puedes ejecutar el asistente con ./ejecutar.sh"
read -r -p "Pulsa Enter para cerrar..."
