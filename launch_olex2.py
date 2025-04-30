from subprocess import run, Popen
import argparse
import signal
import sys

def launch_olex(location: str) -> None:
    # Start Olex2
    process = Popen([location])

    def sigint_handler(_signo, _stack_frame):
        print("\nReceived SIGINT, terminating Olex2...")
        process.terminate()  # Send SIGTERM
        run(["pkill", "olex2"])
        sys.exit(0)

    signal.signal(signal.SIGINT, sigint_handler)

    # Wait for process to complete
    process.wait()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Run Olex2."
    )
    parser.add_argument(
        "olex2_path",
        help="The path containing olex2 start file",
    )
    args = parser.parse_args()

    launch_olex(args.olex2_path)
