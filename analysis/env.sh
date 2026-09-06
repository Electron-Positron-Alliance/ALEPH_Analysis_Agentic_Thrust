#!/usr/bin/env bash
# Set up the analysis environment. Source, do not execute:
#
#   source analysis/env.sh
#   python analysis/verify_inputs.py
#
# Python and all pip dependencies are uv-managed. ROOT itself is not a pip
# package -- it comes from an existing ROOT install, and this script wires its
# PyROOT into the uv venv via PYTHONPATH.
#
# ROOTSYS defaults to the conda py312 install because that is the ROOT that
# works on this machine. Two notes on why, both verified:
#
#   * ~/code/root (6.38.00) does NOT work here. Its cling modulemap references
#     libc++ headers that AppleClang 21 reorganised:
#       etc/cling/std_darwin.modulemap:73: error: header
#       '__type_traits/add_lvalue_reference.h' not found
#     Dictionary generation for templated classes then fails, so RooUnfold
#     loads but cannot be used:
#       TypeError: cannot instantiate incomplete class 'RooUnfoldBayesT<TH1,TH2>'
#     Its libXMLParser also has a dangling /opt/local/lib/libxml2.2.dylib
#     (MacPorts) dependency. Rebuilding RooUnfold against 6.38 does not help --
#     the ROOT install is the problem, not RooUnfold.
#
#   * The uv Python must match the minor version the ROOT install was built
#     against, or PyROOT fails to import with
#       ImportError: symbol not found in flat namespace '__Py_HashPointer'
#     This script reads that from root-config and pins uv accordingly.
set -u
: "${ROOTSYS:=$HOME/code/miniconda3/envs/py312}"

if [ ! -x "$ROOTSYS/bin/root-config" ]; then
  echo "!! no ROOT install at ROOTSYS=$ROOTSYS" >&2
  return 1 2>/dev/null || exit 1
fi

_RV="$("$ROOTSYS/bin/root-config" --version)"
_RPY="$("$ROOTSYS/bin/root-config" --python-version)"
_RPY_MINOR="$(echo "$_RPY" | cut -d. -f1,2)"
_RLIB="$("$ROOTSYS/bin/root-config" --libdir)"

if [ -n "${BASH_SOURCE:-}" ]; then _SRC="${BASH_SOURCE[0]}"
elif [ -n "${ZSH_VERSION:-}" ]; then _SRC="${(%):-%x}"
else _SRC="$PWD/analysis/env.sh"; fi
HERE="$(cd "$(dirname "$_SRC")" && pwd)"

if [ ! -d "$HERE/.venv" ]; then
  echo "==> creating uv venv (python $_RPY_MINOR, to match ROOT $_RV)"
  uv venv "$HERE/.venv" --python "$_RPY_MINOR" || return 1
  uv pip install --python "$HERE/.venv/bin/python" -q numpy matplotlib pandas h5py || return 1
fi
source "$HERE/.venv/bin/activate"

# root-config must be callable: analysis/DataProcessing/Makefile uses
# `root-config --cflags/--libs` to build Analyze.exe.
export PATH="$ROOTSYS/bin:$PATH"

# PyROOT lives in the ROOT install, not the venv.
_SITE="$ROOTSYS/lib/python$_RPY_MINOR/site-packages"
export PYTHONPATH="${_SITE}:${_RLIB}${PYTHONPATH:+:$PYTHONPATH}"
export ROOTSYS

# RooUnfold must be built against this same ROOT. build/ links libCore.6.36.
export ROOUNFOLD_LIB="${ROOUNFOLD_LIB:-$HOME/code/RooUnfold/build/libRooUnfold.dylib}"

echo "    ROOT      $_RV  (python $_RPY)  $ROOTSYS"
echo "    python    $(python --version 2>&1 | awk '{print $2}')  (uv venv)"
python -c "import ROOT" 2>/dev/null && echo "    PyROOT    importable" \
  || echo "    !! PyROOT NOT importable" >&2
if [ -f "$ROOUNFOLD_LIB" ]; then echo "    RooUnfold $ROOUNFOLD_LIB"
else echo "    !! RooUnfold not found at $ROOUNFOLD_LIB" >&2; fi
