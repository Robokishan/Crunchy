"""Run Crunchbase and Tracxn crawlers in parallel (two processes). One command. Ctrl+C kills both."""
import subprocess
import sys
import signal

def main():
    procs = [
        subprocess.Popen([sys.executable, "go-crunchy-cb.py"], cwd="."),
        subprocess.Popen([sys.executable, "go-crunchy-tracxn.py"], cwd="."),
    ]

    def kill_both(*args):
        for p in procs:
            if p.poll() is None:
                p.terminate()
        sys.exit(0)

    signal.signal(signal.SIGINT, kill_both)
    signal.signal(signal.SIGTERM, kill_both)

    for p in procs:
        p.wait()

if __name__ == "__main__":
    main()
