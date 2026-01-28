import subprocess
import sys
import argparse

def verify_release_ready(client_slug):
    print(f"==================================================")
    print(f"   VERIFY RELEASE READY: {client_slug}")
    print(f"==================================================")

    steps = [
        ("ICC (Identity Consistency)", ["python", "tools/verify_icc.py", "--client", client_slug]),
        ("Compliance (G13.1)", ["python", "tools/verify_g131.py", "--client", client_slug]),
        ("Runtime Binding (G15)", ["python", "tools/verify_runtime_profile.py", "--client", client_slug])
    ]

    for name, cmd in steps:
        print(f"\n>> RUNNING GATE: {name}...")
        try:
            subprocess.run(cmd, check=True)
            print(f"   [PASS] {name}")
        except subprocess.CalledProcessError:
            print(f"\n!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")
            print(f"   [FAIL] GATE RELEASE FAILURE: {name}")
            print(f"   Agent {client_slug} is NOT ready for release.")
            print(f"!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")
            sys.exit(1)

    print(f"\n==================================================")
    print(f"   [SUCCESS] ALL GATES PASSED. RELEASE APPROVED.")
    print(f"==================================================")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--client", required=True)
    args = parser.parse_args()
    verify_release_ready(args.client)
