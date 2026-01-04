import os
import subprocess
import sys

# --- SETTINGS ---
SERVER_FILE = "vscode-server-linux-x64.tar.gz"
CLI_FILE = "vscode-cli-alpine-x64.tar.gz"
USB_ROOT = os.path.dirname(os.path.abspath(__file__))

def get_commit_id():
    """Detects the Commit ID from the local VS Code installation."""
    for cmd in ["code", "code-insiders"]:
        try:
            output = subprocess.check_output(f"{cmd} --version", shell=True, text=True, stderr=subprocess.DEVNULL)
            return output.splitlines()[1].strip()
        except Exception:
            continue
    return None

print("\033[96m--- VS Code Server Airgap Injector ---\033[0m")

# 1. Version Detection
commit_id = get_commit_id()
if not commit_id:
    print("\033[93m[!] Automatic detection failed.\033[0m")
    commit_id = input("Please paste your Commit ID manually: ").strip()
else: 
    print(f"\033[95m[+] Local VS Code version detected: {commit_id}\033[0m")

# 2. Local File Validation
local_dir = os.path.join(USB_ROOT, commit_id)
server_path = os.path.join(local_dir, SERVER_FILE)
cli_path = os.path.join(local_dir, CLI_FILE)

if not os.path.exists(server_path) or not os.path.exists(cli_path):
    print(f"\033[91m[!] Error: Required assets missing in: {local_dir}\033[0m")
    sys.exit(1)

# 3. Connection Setup
remote_user = input("Enter Remote Username: ").strip()
remote_ip = input("Enter Remote IP/Hostname: ").strip()
remote_target = f"{remote_user}@{remote_ip}"

# 4. Data Transfer
print(f"\n\033[92m[1/2] Transferring server and CLI binaries to {remote_ip}...\033[0m")
try:
    subprocess.run(["scp", server_path, cli_path, f"{remote_target}:/tmp/"], check=True)
    print("\033[32m[✓] Transfer completed successfully.\033[0m")
except subprocess.CalledProcessError:
    print("\033[91m[x] SCP Transfer failed! Please check your connection and credentials.\033[0m")
    sys.exit(1)

# 5. Remote Environment Configuration
# Placing image tag here to visualize the directory structure we are about to create


remote_script = rf"""
# Setup internal variables
COMMIT_ID="{commit_id}"
SERVER_TAR="/tmp/{SERVER_FILE}"
CLI_TAR="/tmp/{CLI_FILE}"

# Target destination paths
CLI_BIN_PATH="$HOME/.vscode-server/code-$COMMIT_ID"
SERVER_DIR="$HOME/.vscode-server/cli/servers/Stable-$COMMIT_ID/server"

echo "  -> Preparing remote directory: $SERVER_DIR"
mkdir -p "$SERVER_DIR"

if [ -f "$SERVER_TAR" ]; then
    echo "  -> Extracting Server binaries..."
    tar -xzf "$SERVER_TAR" -C "$SERVER_DIR" --strip-components 1
else
    echo "  [!!] Error: Server tarball not found at $SERVER_TAR"
    exit 1
fi

if [ -f "$CLI_TAR" ]; then
    echo "  -> Extracting CLI components..."
    mkdir -p /tmp/cli_unpack_tmp
    tar -xzf "$CLI_TAR" -C /tmp/cli_unpack_tmp
    mv /tmp/cli_unpack_tmp/code "$CLI_BIN_PATH"
    chmod +x "$CLI_BIN_PATH"
    rm -rf /tmp/cli_unpack_tmp
    echo "  -> CLI binary installed at: $CLI_BIN_PATH"
else
    echo "  [!!] Error: CLI tarball not found at $CLI_TAR"
    exit 1
fi

echo "  -> Validating Node.js runtime..."
if "$SERVER_DIR/node" -v > /dev/null 2>&1; then
    # Create the '0' flag to signal success to VS Code
    touch "$SERVER_DIR/0"
    rm "$SERVER_TAR" "$CLI_TAR"
    echo "  [✓] Environment validation passed."
else
    echo "  [!!] ERROR: Node.js failed to execute. The remote OS may be missing glibc or libstdc++."
    exit 1
fi
"""

print(f"\n\033[92m[2/2] Configuring remote environment at {remote_ip}...\033[0m")
try:
    subprocess.run(["ssh", "-T", remote_target, remote_script], check=True)
    print(f"\n\033[95m[COMPLETE] VS Code Server successfully injected for Commit: {commit_id}\033[0m")
    print("\033[95mYou can now connect via the 'Remote-SSH' extension in VS Code.\033[0m")
except subprocess.CalledProcessError:
    print("\n\033[91m[x] Remote setup failed. Ensure the user has write permissions for /tmp and $HOME.\033[0m")