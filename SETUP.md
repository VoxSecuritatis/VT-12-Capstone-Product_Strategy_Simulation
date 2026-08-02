# Environment Setup (as verified)

This file records the actual toolchain installed and verified for this capstone, with exact versions, locations, and the commands used to obtain/verify each one. It complements `README.md`'s Prerequisites (which states what's needed) by recording the as-built state.

Environment: WSL2, Ubuntu 24.04.4 LTS, on Windows.

## Summary

| Tool | Version | Location | Purpose |
|---|---|---|---|
| WSL2 | 2.7.3.0 | Windows host | Linux environment hosting n8n, Python, MCP server |
| Ubuntu | 24.04.4 LTS | WSL2 distro | Base OS |
| Python | 3.12.3 | `/usr/bin/python3.12` (symlinked as `/usr/bin/python3`) | CrewAI project runtime, MCP server |
| uv | 0.12.1 | `~/.local/bin/uv`, `~/.local/bin/uvx` | Python package/project manager (uv-structured CrewAI project per rubric) |
| nvm | 0.40.6 | `~/.nvm` | Node.js version manager |
| Node.js | 24.18.0 | `~/.nvm/versions/node/v24.18.0/bin/node` | n8n runtime |
| npm | 11.16.0 | bundled with the above Node.js install | Package manager used to install n8n |
| n8n | 2.27.4 | `~/.nvm/versions/node/v24.18.0/bin/n8n` | Workflow orchestration (one of the two required implementations) |

## Per-tool detail

### WSL2 + Ubuntu
- **What:** Windows Subsystem for Linux, running an Ubuntu 24.04.4 LTS distro. Hosts everything below.
- **Obtain:** `wsl --install` from an elevated PowerShell (Microsoft's standard installer); already provisioned here.
- **Verify:** `wsl --version` (from PowerShell); `lsb_release -d` (inside WSL).

### Python 3.12.3
- **What:** CPython interpreter. Ships preinstalled with Ubuntu 24.04 LTS — no install step was needed.
- **Obtain (if ever missing):** `sudo apt install python3`, or `uv python install 3.12` to have `uv` manage it instead.
- **Verify:** `python3 --version`

### uv 0.12.1
- **What:** Rust-based Python package/project manager. Used to scaffold and manage the CrewAI project (the rubric requires "UV structure").
- **Obtain:** `curl -LsSf https://astral.sh/uv/install.sh | sh` (installs to `~/.local/bin`; a new shell picks it up on PATH automatically).
- **Verify:** `uv --version`
- **Test (installs a real package end-to-end):**
  ```bash
  uv venv /tmp/uv_test
  uv pip install --python /tmp/uv_test/bin/python requests
  rm -rf /tmp/uv_test
  ```

### nvm 0.40.6
- **What:** Node Version Manager — manages Node.js versions inside WSL.
- **Obtain:** `curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.40.6/install.sh | bash` (adds sourcing lines to `~/.bashrc`).
- **Verify:** `nvm --version` and `nvm ls` (lists installed/default versions).

### Node.js 24.18.0
- **What:** JavaScript runtime n8n runs on. Installed and managed via nvm, not the system package manager.
- **Obtain:** `nvm install --lts` (or `nvm install 24` for this exact major version).
- **Verify:** `node --version`

### npm 11.16.0
- **What:** Node's package manager, bundled with the Node.js install above.
- **Verify:** `npm --version`

### n8n 2.27.4
- **What:** Low-code workflow automation platform — one of this project's two required implementations.
- **Obtain:** `npm install -g n8n` (installs under the active nvm Node version).
- **Verify:** `n8n --version`
- **Run:** `n8n start`, then open `http://localhost:5678`. **Must be launched from an interactive WSL shell** — see caveat below. Confirmed working: dashboard loads cleanly both via `curl` (`HTTP 200`) and manually in a browser.

## Important environment caveats

### Node/n8n only resolve correctly from an interactive WSL shell
nvm's PATH setup lives in `~/.bashrc`, which is sourced by **interactive** shells (`bash -ic "..."`, or a normal terminal you type into) but *not* by non-interactive login shells (`bash -lc "..."`, which reads `~/.profile` instead). Invoked the wrong way, `node`/`npm`/`n8n` silently fall through to whatever same-named entries exist elsewhere on the inherited Windows `PATH` (e.g. a Windows-side Node.js install), which can't execute from Linux and fail with a confusing "Permission denied". Always start n8n (or run any Node/npm command) from an actual interactive terminal, not a scripted non-interactive invocation.

### WSL networking changes made to get here
Three changes were needed to get reliable internet access working inside WSL (SerpAPI, Google APIs, and PyPI/npm registry access all depend on this):

1. **`/etc/wsl.conf`** — `generateResolvConf = false` was disabling WSL's automatic DNS configuration, leaving no DNS servers assigned at all. Commented out so WSL manages `/etc/resolv.conf` again.
2. **`/etc/sysctl.d/99-disable-ipv6.conf`** — disables IPv6 inside WSL (`net.ipv6.conf.all.disable_ipv6 = 1` and the `default` equivalent). May no longer be strictly necessary after fix #3 below, but is harmless and left in place.
3. **`C:\Users\<your-username>\.wslconfig`** — created with:
   ```ini
   [wsl2]
   networkingMode=mirrored
   dnsTunneling=true
   autoProxy=true
   firewall=true
   ```
   This, combined with disabling an active VPN, resolved a conflict where WSL2's virtual NAT adapter and the VPN interfered with each other — DNS was slow/flaky and real HTTPS connections (e.g. to PyPI) timed out after resolving, even though raw IP connectivity looked fine. Requires WSL >= 2.0 (confirmed here: 2.7.3.0). Apply changes with `wsl --shutdown` followed by reopening a WSL terminal.
