#!/usr/bin/env bash
set -euo pipefail

# Installs Tamarin Prover and runtime dependencies for this repository.
# Safe to run repeatedly (idempotent).

TAMARIN_VERSION="1.12.0"
MAUDE_VERSION="Maude3.4"
LOCAL_BIN="${HOME}/.local/bin"
MAUDE_DIR="${HOME}/.local/maude-3.4/Linux64"

mkdir -p "${LOCAL_BIN}" "${HOME}/.local/maude-3.4"

if ! command -v dot >/dev/null 2>&1; then
  if command -v apt-get >/dev/null 2>&1; then
    sudo DEBIAN_FRONTEND=noninteractive apt-get update -qq
    sudo DEBIAN_FRONTEND=noninteractive apt-get install -y -qq graphviz wget unzip ca-certificates
  else
    echo "GraphViz (dot) is required but apt-get is unavailable." >&2
    exit 1
  fi
fi

if [[ ! -x "${LOCAL_BIN}/tamarin-prover" ]]; then
  tmp="$(mktemp -d)"
  wget -q "https://github.com/tamarin-prover/tamarin-prover/releases/download/${TAMARIN_VERSION}/tamarin-prover-${TAMARIN_VERSION}-linux64-ubuntu.tar.gz" \
    -O "${tmp}/tamarin-prover.tar.gz"
  tar -xzf "${tmp}/tamarin-prover.tar.gz" -C "${tmp}"
  install -m 755 "${tmp}/tamarin-prover" "${LOCAL_BIN}/tamarin-prover"
  rm -rf "${tmp}"
fi

if [[ ! -x "${MAUDE_DIR}/maude.linux64" ]]; then
  tmp="$(mktemp -d)"
  wget -q "https://github.com/maude-lang/Maude/releases/download/${MAUDE_VERSION}/Maude-linux.zip" \
    -O "${tmp}/Maude-linux.zip"
  unzip -qo "${tmp}/Maude-linux.zip" -d "${HOME}/.local/maude-3.4"
  rm -rf "${tmp}"
fi

cat > "${LOCAL_BIN}/maude" <<'EOF'
#!/usr/bin/env bash
MAUDE_DIR="${HOME}/.local/maude-3.4/Linux64"
cd "${MAUDE_DIR}" || exit 1
exec ./maude.linux64 "$@"
EOF
chmod +x "${LOCAL_BIN}/maude"

export PATH="${LOCAL_BIN}:${PATH}"
tamarin-prover --version
echo "Development tools are ready. Ensure ${LOCAL_BIN} is on your PATH."
