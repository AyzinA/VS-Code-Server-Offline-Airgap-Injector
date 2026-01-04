import os
import requests
import concurrent.futures

# API URLs
SERVER_API = "https://update.code.visualstudio.com/api/commits/stable/server-linux-x64"
CLI_API = "https://update.code.visualstudio.com/api/commits/stable/cli-alpine-x64"

# Configuration
MAX_WORKERS = 10

def download_task(args):
    """Worker to download a single file with simple status logging."""
    url, folder, filename = args
    path = os.path.join(folder, filename)
    
    if os.path.exists(path):
        # We don't print anything for skipped files to keep the console clean
        return

    try:
        print(f"  [STARTING] ID: {os.path.basename(folder)}")
        with requests.get(url, stream=True, timeout=30) as r:
            r.raise_for_status()
            with open(path, 'wb') as f:
                for chunk in r.iter_content(chunk_size=1024 * 128): # 128KB chunks
                    if chunk:
                        f.write(chunk)
        print(f"  [FINISHED] ID: {os.path.basename(folder)}")
    except Exception as e:
        print(f"  [FAILED] ID: {os.path.basename(folder)}: {e}")
        if os.path.exists(path):
            os.remove(path)

def main():
    print("\033[96m--- VS Code Server Offline Sync ---\033[0m")
    
    try:
        # 1. Fetch IDs
        # We fetch both, but use cli_ids as the base because it's smaller
        cli_ids = requests.get(CLI_API).json()
        server_ids = requests.get(SERVER_API).json()
        
        # 2. Convert server list to a set for O(1) lookup speed
        server_set = set(server_ids)
        
        # 3. Only keep IDs found in both, but iterate through the CLI list
        common_ids = [cid for cid in cli_ids if cid in server_set]
        
        print(f"Server API has {len(server_ids)} IDs.")
        print(f"CLI API has {len(cli_ids)} IDs.")
        print(f"\033[92mSyncing {len(common_ids)} matching versions to USB...\033[0m")
    except Exception as e:
        print(f"API Connection Error: {e}")
        return

    script_root = os.path.dirname(os.path.abspath(__file__))
    queue = []

    # 4. Prepare download queue
    for cid in common_ids:
        folder_path = os.path.join(script_root, cid)
        if not os.path.exists(folder_path):
            os.makedirs(folder_path)
            
        queue.append((f"https://update.code.visualstudio.com/commit:{cid}/server-linux-x64/stable", 
                      folder_path, "vscode-server-linux-x64.tar.gz"))
        queue.append((f"https://update.code.visualstudio.com/commit:{cid}/cli-alpine-x64/stable", 
                      folder_path, "vscode-cli-alpine-x64.tar.gz"))

    # 5. Run Parallel Downloads
    with concurrent.futures.ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        executor.map(download_task, queue)

    print("\n\033[96mUSB Sync Complete. All matched CLI/Server pairs are ready.\033[0m")

if __name__ == "__main__":
    main()