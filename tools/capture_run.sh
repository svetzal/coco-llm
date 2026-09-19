#!/usr/bin/env bash
# Record an XRoar demo as video with program audio, for the blog and the
# video series. Launches the demo the way the talk does, finds the XRoar
# window, records exactly that rectangle with macOS's own recorder, sends
# keystrokes to the emulator at set times, and encodes an MP4.
#
#   tools/capture_run.sh NAME [options] -- <launch command>
#
#   tools/capture_run.sh exp004-live-training --seconds 85 --keys "70: " \
#       -- make present EXP=4
#
# Options:
#   --geometry WxH+X+Y  size the XRoar window (default 640x480+80+80; macOS
#                   ignores the position). The window's real rectangle is read
#                   from the window server, which needs no permission
#   --rect x,y,w,h  record this rectangle instead (screen points)
#   --seconds N     length of the recording (default 120)
#   --keys "T:TEXT" type TEXT into XRoar T seconds after recording starts;
#                   repeatable. Named keys in braces: {return} {space} {up}
#                   {down} {left} {right} {esc}; see tools/xroar_keys.py
#   --settle S      seconds to wait after the window appears before recording
#                   (default 1); the demo keeps running meanwhile
#   --scale N       integer nearest-neighbour upscale for the MP4 (default 1;
#                   the recording is already at Retina pixel density)
#   --out DIR       where the files go (default build/captures)
#   --quit          stop XRoar when the recording ends
#
# Needs Screen Recording permission for the shell that runs it; macOS asks
# once. --keys also needs Accessibility permission for the app running the
# shell (macOS adds the entry when first asked; turn it on in System
# Settings, Privacy & Security, Accessibility). Without it the recording
# still works and the keys are reported as not sent. Writes NAME.mov (as recorded), NAME.mp4, and NAME.json
# with the command, window rectangle, key times and clock time, so a clip can
# say what run it is.
set -euo pipefail

NAME=""; SECONDS_TO_RECORD=120; SETTLE=1; SCALE=1; OUT=build/captures; QUIT=0; GEOM="640x480+80+80"; RECT=""
KEYS=()
while [ $# -gt 0 ]; do
  case "$1" in
    --geometry) GEOM="$2"; shift 2 ;;
    --rect) RECT="$2"; shift 2 ;;
    --seconds) SECONDS_TO_RECORD="$2"; shift 2 ;;
    --keys) KEYS+=("$2"); shift 2 ;;
    --settle) SETTLE="$2"; shift 2 ;;
    --scale) SCALE="$2"; shift 2 ;;
    --out) OUT="$2"; shift 2 ;;
    --quit) QUIT=1; shift ;;
    --) shift; break ;;
    -h|--help) sed -n '2,28p' "$0"; exit 0 ;;
    -*) echo "unknown option $1" >&2; exit 2 ;;
    *) if [ -z "$NAME" ]; then NAME="$1"; shift; else echo "unexpected argument $1" >&2; exit 2; fi ;;
  esac
done
[ -n "$NAME" ] || { echo "usage: $0 NAME [options] -- <launch command>" >&2; exit 2; }
[ $# -gt 0 ] || { echo "no launch command after --" >&2; exit 2; }

if pgrep -x xroar >/dev/null; then
  echo "an XRoar is already running; quit it first so the recording is of this run" >&2
  exit 1
fi
mkdir -p "$OUT"
MOV="$OUT/$NAME.mov"; MP4="$OUT/$NAME.mp4"; META="$OUT/$NAME.json"
rm -f "$MOV" "$MP4"

# The window goes where we say, so the rectangle to record is known. The
# Makefile takes the emulator from $XROAR, which reaches every nested make;
# the wrapper below is what it runs.
RECT_GIVEN="$RECT"
if [ -z "$RECT" ]; then
  # The make targets test that $XROAR is an executable, so options cannot ride
  # in the variable; a wrapper adds them.
  WRAP="$OUT/.xroar-placed"
  printf '#!/bin/sh\nexec %s -geometry %s "$@"\n' "$(command -v xroar)" "$GEOM" > "$WRAP"
  chmod +x "$WRAP"
  export XROAR="$WRAP"
fi
echo "launch: $*"
STARTED=$(date -u +%Y-%m-%dT%H:%M:%SZ)
"$@" >/dev/null 2>&1 &

# Wait for the emulator to be running, then ask the window server where its
# window is. The geometry option sets the size but macOS places the window,
# so the position cannot be assumed. The frame includes the title bar; the
# content is the requested height at the bottom of it.
for _ in $(seq 1 240); do pgrep -x xroar >/dev/null && break; sleep 0.5; done
pgrep -x xroar >/dev/null || { echo "XRoar did not start" >&2; exit 1; }
if [ -z "$RECT_GIVEN" ]; then
  FRAME=""
  for _ in $(seq 1 60); do
    FRAME=$(uv run --with pyobjc-framework-Quartz python tools/xroar_window.py 2>/dev/null || true)
    [ -n "$FRAME" ] && break
    sleep 0.5
  done
  [ -n "$FRAME" ] || { echo "no XRoar window on screen" >&2; exit 1; }
  IFS=, read -r FX FY FW FH <<< "$FRAME"
  GW="${GEOM%%x*}"; REST="${GEOM#*x}"; GH="${REST%%+*}"
  if [ "$FH" -gt "$GH" ]; then FY=$((FY + FH - GH)); FH=$GH; fi
  RECT="$FX,$FY,$FW,$FH"
fi
echo "window: $RECT"
# Park the pointer in the bottom-right corner so it is not in the frame.
uv run --with pyobjc-framework-Quartz python -c 'import Quartz; b = Quartz.CGDisplayBounds(Quartz.CGMainDisplayID()); Quartz.CGWarpMouseCursorPosition((b.size.width - 2, b.size.height - 2))' 2>/dev/null || true
sleep "$SETTLE"

# Record that rectangle, with the system audio the emulator is playing.
screencapture -v -A -R "$RECT" -V "$SECONDS_TO_RECORD" "$MOV" &
REC=$!
REC_START=$(date +%s)
echo "recording ${SECONDS_TO_RECORD}s to $MOV"

# Keystrokes at their times, into the emulator.
for spec in "${KEYS[@]:-}"; do
  [ -n "$spec" ] || continue
  T="${spec%%:*}"; TEXT="${spec#*:}"
  while [ $(( $(date +%s) - REC_START )) -lt "$T" ]; do sleep 0.2; done
  if uv run --with pyobjc-framework-Quartz python tools/xroar_keys.py "$RECT" "$TEXT" 2>&1; then
    echo "keys at ${T}s: $(printf '%q' "$TEXT")"
  else
    echo "keys at ${T}s NOT sent; is Accessibility granted to the app running this shell?" >&2
  fi
done

wait "$REC"
[ -s "$MOV" ] || { echo "recording failed; was Screen Recording permission granted?" >&2; exit 1; }

if [ "$QUIT" = 1 ]; then
  pkill -x xroar || true
fi

# Encode. Nearest-neighbour scaling keeps the pixels square; yuv420p plays everywhere.
ffmpeg -hide_banner -loglevel error -y -i "$MOV" \
  -vf "scale=iw*${SCALE}:ih*${SCALE}:flags=neighbor,pad=ceil(iw/2)*2:ceil(ih/2)*2" \
  -c:v libx264 -preset slow -crf 18 -pix_fmt yuv420p -c:a aac -b:a 160k -movflags +faststart "$MP4"

python3 - "$META" "$NAME" "$STARTED" "$RECT" "$SECONDS_TO_RECORD" "$SCALE" "$MOV" "$MP4" "$*" "${KEYS[@]:-}" <<'PY'
import json, sys
meta, name, started, rect, secs, scale, mov, mp4, launch, *keys = sys.argv[1:]
json.dump({"name": name, "started_utc": started, "launch": launch, "window_rect_points": rect,
           "seconds": int(secs), "scale": int(scale), "keys": [k for k in keys if k],
           "recorded": mov, "encoded": mp4,
           "note": "XRoar at the machine's clock rate (-ratelimit); an emulator recording, not hardware"},
          open(meta, "w"), indent=2)
PY
echo "wrote $MP4 and $META"
ffprobe -hide_banner -v error -show_entries format=duration:stream=codec_type,width,height -of compact "$MP4"
