# VS Code Offline Airgap Injector

This project provides a robust, two-part solution for using **VS Code Remote-SSH** on servers with **no internet access**. It automates the process of matching the correct VS Code Server and CLI versions, downloading them to a USB drive, and injecting them into the remote environment.

## 🚀 The Workflow

1. **Stage 1 (Online):** Run `sync_downloader.py` on a machine with internet to fetch matching Server and CLI pairs.
2. **Stage 2 (Offline):** Plug the USB into your workstation and run `inject_vscode_server.py` to push the correct version to your air-gapped remote via SSH.

---

## 📂 Project Structure

* `sync_downloader.py`: Scans Microsoft APIs for matching Commit IDs and downloads assets in parallel.
* `inject_vscode_server.py`: Detects your local VS Code version and installs the matching assets on the remote server.
* `{Commit_ID}/`: Folders created automatically by the downloader to store specific version pairs.

---

## 🛠 Prerequisites

### Local Machine (Windows or Linux)

* **Python 3.x**
* **Requests library:** `pip install requests`
* **OpenSSH Client:** (Built-in on Windows 10/11 and most Linux distros)

### Remote Machine (Air-gapped)

* **Linux OS** (x64)
* **SSH Access**
* **Glibc / Libstdc++:** (Standard on most distros like Ubuntu, Debian, Arch, and RHEL)

---

## 📖 Usage Instructions

### 1. Download Assets (On Internet-Connected Machine)

Run the sync script to populate your USB drive. It only downloads IDs where both the Server and CLI are available.

```bash
python sync_downloader.py

```

### 2. Inject to Remote (On Offline Workstation)

Connect your USB drive to the machine you use to access the remote server. Run the injector script:

```bash
python inject_vscode_server.py

```

* The script will automatically detect your local VS Code version.
* It will ask for the remote **Username** and **IP/Hostname**.
* It transfers the files to `/tmp`, extracts them to the correct `.vscode-server` paths, and creates the required `0` success flag.

### 3. Connect via VS Code

Once the script says `[COMPLETE]`:

1. Open VS Code.
2. Press `F1` -> **Remote-SSH: Connect to Host...**
3. The connection will initialize instantly without trying to download anything from the internet.

---

## 💡 Troubleshooting

### `UnpackFailed` or `Permission Denied`

If the remote setup fails, ensure your remote user has write permissions to their own `$HOME` directory and the `/tmp` folder.

### "Node.js failed to execute"

VS Code Server requires a relatively modern Linux environment. If you see this error, your remote server might be missing `libstdc++` or `glibc`. On Arch, ensure `gcc-libs` is installed.