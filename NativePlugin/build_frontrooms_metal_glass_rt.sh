#!/bin/sh
# Build the project-owned Metal RT bridge for Unity 6000.3.10f1.
# The resulting dylib is imported by Unity only on macOS; all other platforms
# continue using the existing URP reflection fallback.
set -eu

SCRIPT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
PROJECT_ROOT=$(CDPATH= cd -- "$SCRIPT_DIR/.." && pwd)
UNITY_EDITOR_VERSION=${UNITY_EDITOR_VERSION:-6000.3.10f1}
UNITY_APP=${UNITY_APP:-/Applications/Unity/Hub/Editor/${UNITY_EDITOR_VERSION}/Unity.app}
PLUGIN_API="$UNITY_APP/Contents/PluginAPI"
OUTPUT_DIR="$PROJECT_ROOT/Assets/Plugins/macOS"
OUTPUT="$OUTPUT_DIR/libFrontRoomsMetalGlassRT.dylib"

if [ ! -f "$PLUGIN_API/IUnityGraphicsMetal.h" ]; then
  echo "Unity PluginAPI not found: $PLUGIN_API" >&2
  exit 1
fi

mkdir -p "$OUTPUT_DIR"
xcrun clang++ -std=c++17 -fobjc-arc -O2 -dynamiclib \
  -arch arm64 -mmacosx-version-min=13.0 \
  -isystem "$PLUGIN_API" \
  -framework Metal -framework Foundation \
  -o "$OUTPUT" "$SCRIPT_DIR/FrontRoomsMetalGlassRT.mm"

# Unity must restart after replacing a native plugin because the macOS editor
# keeps loaded dylibs for the lifetime of the process.
echo "Built $OUTPUT"
