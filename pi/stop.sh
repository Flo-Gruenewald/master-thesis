#!/bin/bash
# Stops the room on the Pi cleanly: every run.sh restart loop (however it was started), then the
# host (SIGTERM → LEDs off), then the presence script. Safe to call from run.sh (skips its caller).
skip="$$ $PPID"
for p in $(pgrep -f 'run\.sh'); do
  case " $skip " in *" $p "*) continue ;; esac
  args=$(tr '\000' ' ' < "/proc/$p/cmdline" 2>/dev/null)
  case "$args" in                      # only bash running our run.sh (not shells that merely mention it)
    "/bin/bash ./run.sh "*|"/bin/bash /home/pi/easteregged/run.sh "*|"bash ./run.sh "*|"bash /home/pi/easteregged/run.sh "*)
      kill "$p" 2>/dev/null ;;
  esac
done
pkill -TERM -f "[e]asteregged/host/main.py"
pkill -f "[e]asteregged/presence.py"
for i in 1 2 3 4 5 6 7 8 9 10; do
  pgrep -f "[e]asteregged/host/main.py" >/dev/null || { echo "stopped"; exit 0; }
  sleep 0.5
done
pkill -KILL -f "[e]asteregged/host/main.py"; echo "stopped (forced)"
