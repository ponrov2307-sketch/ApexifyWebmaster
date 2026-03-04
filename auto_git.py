import subprocess
import time
from datetime import datetime


def run_git(args, check=True, capture_output=False):
    return subprocess.run(
        ["git", *args],
        check=check,
        capture_output=capture_output,
        text=True,
    )


def auto_push():
    while True:
        now = datetime.now().strftime("%H:%M:%S")
        print(f"[{now}] Starting Auto-Sync...")

        try:
            run_git(["fetch", "origin"])

            run_git(["add", "."])
            commit_message = f"Auto-sync at {now}"
            commit_result = run_git(["commit", "-m", commit_message], check=False, capture_output=True)

            output = f"{commit_result.stdout}\n{commit_result.stderr}".lower()
            if commit_result.returncode != 0 and "nothing to commit" not in output:
                raise RuntimeError(commit_result.stderr or commit_result.stdout)

            # Merge remote changes first; avoid interactive editor during pull.
            run_git(["pull", "--no-rebase", "--no-edit", "--autostash", "origin", "main"])
            run_git(["push", "origin", "main"])
            print(f"[{now}] Cloud Updated! Next sync in 3 minutes...")
        except Exception as e:
            print(f"[{now}] Sync failed: {e}")

        time.sleep(180)


if __name__ == "__main__":
    auto_push()
