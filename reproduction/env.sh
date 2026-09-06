#!/usr/bin/env bash
# Set up the reproduction environment. Source, do not execute.
#
#   source reproduction/env.sh
#
# Requires a local ROOT build. ROOTSYS defaults to ~/code/root, matching the
# path in Appendix A of the paper; override by exporting ROOTSYS first.
set -u
: "${ROOTSYS:=$HOME/code/root}"

if [ ! -f "$ROOTSYS/bin/thisroot.sh" ]; then
  echo "!! no ROOT build at $ROOTSYS -- set ROOTSYS to your build" >&2
  return 1 2>/dev/null || exit 1
fi
source "$ROOTSYS/bin/thisroot.sh"

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
if [ ! -d "$HERE/.venv" ]; then
  echo "==> creating uv venv (python 3.11, to match this ROOT build)"
  uv venv "$HERE/.venv" --python 3.11 || return 1
  uv pip install --python "$HERE/.venv/bin/python" numpy matplotlib pandas h5py || return 1
fi
source "$HERE/.venv/bin/activate"

echo "    ROOT   $(root-config --version)  (built for python $(root-config --python-version))"
echo "    python $(python --version 2>&1 | awk '{print $2}')"
python -c "import ROOT" 2>/dev/null && echo "    PyROOT importable" \
  || echo "    !! PyROOT NOT importable -- python/ROOT ABI mismatch"
