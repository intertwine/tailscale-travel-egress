# Tailscale travel egress (macOS + Linux)

A small, opt-in toolkit for using **your own Tailscale exit node** on a restricted or unreliable network. It includes a macOS CLI, tests, and an [Agent Skill](skills/tailscale-travel-egress/SKILL.md). It does not create accounts, install Tailscale, or configure a server automatically.

Network restrictions vary. A Tailscale relay may work when direct peer-to-peer traffic does not, but this is not guaranteed. Check local laws and your network's rules. An exit node operator can see your destination metadata and any unencrypted traffic. Use a server you trust.

## Prerequisites

- An existing Tailscale tailnet and an **approved** exit node on a trusted Linux server outside the restricted network.
- Tailscale signed in on the Mac. Confirm the node appears under `tailscale exit-node list` or in the menu bar.
- A working Wi-Fi connection: complete any captive portal **before** enabling an exit node. Opening `http://neverssl.com` can trigger a hotel portal.
- macOS with Bash 3.2+ and its built-in `route` and `networksetup` tools. No package dependencies for the script. The macOS Tailscale app CLI or a `tailscale` command on `PATH` is used.

### Prepare a Linux exit node

Follow [Tailscale's official exit-node guide](https://tailscale.com/docs/features/exit-nodes/how-to/setup). In short:

1. Enable **persistent** IP forwarding on the Linux server; for IPv4, set `net.ipv4.ip_forward=1` in `/etc/sysctl.d/` and apply it. Enable IPv6 forwarding too if the server provides IPv6 egress. Review firewall/NAT configuration rather than disabling firewall protection.
2. Run `sudo tailscale set --advertise-exit-node` (follow the guide for your installed Tailscale version).
3. In the Tailscale admin console, approve **Use as exit node** for that machine. With custom ACLs/grants, ensure clients can access `autogroup:internet`.
4. Prefer a **non-ephemeral** machine. For a trusted unattended server, review [key expiry](https://tailscale.com/docs/features/access-control/key-expiry) and decide whether to disable it in the admin console. An ephemeral machine can disappear after a prolonged disconnect.

Do not put a reusable auth key in this repository. Keep the server's management access separate from its exit-node role.

## Client use

```bash
# Replace this placeholder with a node already approved in your tailnet.
export TRAVEL_EXIT_NODE=my-exit-node
./scripts/travel-egress status
./scripts/travel-egress on
# Verify a trusted site loads and check the public IP through the exit node.
curl https://api.ipify.org
./scripts/travel-egress off
```

`on` keeps local LAN access so you can reach a hotel portal/router. Enabling the exit node changes the default route and may briefly drop existing TCP connections. To re-authenticate an expired portal, turn it off, log in, then turn it back on. If the tunnel is broken, `off` restores direct routing.

### Optional: one narrow direct route

Some *unblocked* services may need to stay direct when the exit node is enabled. **This is an exception, not a privacy feature:** matching traffic is exposed to the local network/ISP. Discover the service's current IPs and choose the narrowest suitable IPv4 CIDR. Shared CDNs often host unrelated services; a broad exception can accidentally send blocked apps direct. Re-check the CIDR when DNS/CDN answers change.

```bash
# Documentation-only placeholder, not a real service route.
export TRAVEL_BYPASS_CIDR=203.0.113.0/24
./scripts/travel-egress route-add
./scripts/travel-egress status
# Later, or when no longer needed:
./scripts/travel-egress route-del
```

`route-add` uses `route -n get -ifscope en0 default` to find the **physical Wi-Fi gateway even while the exit node is on**. Set `TRAVEL_INTERFACE` (or `--interface`) if Wi-Fi is not `en0`. It requires sudo and replaces only the specified prefix. It does **not** change DNS, manage credentials, or promise a bypass will work: macOS Network Extension route policy can override traditional routes. Verify both the intended egress and the exception after any change. Route exceptions are not persistent across reboots and must be rechecked on a new network. Prefer no exception whenever possible.

To see options, run `./scripts/travel-egress --help`. You can add the script to `PATH` if you like; it never installs shell aliases itself.

### Agent Skill (optional)

The `skills/tailscale-travel-egress/SKILL.md` directory is a portable Agent Skill. In a Prime Agent setup, link or copy that directory to `~/.prime/agent/skills/tailscale-travel-egress`, or reference it explicitly with `--skill`. Keep the repo checked out if you use a symlink; its skill refers to the adjacent script and README. The skill does not execute changes on load.

## Cleanup

1. `./scripts/travel-egress off`.
2. If you added a route, `./scripts/travel-egress route-del --bypass-cidr YOUR_CIDR`. Remove any older routes you created separately using their exact prefix.
3. Restore any custom DNS you set manually, for example on macOS: `sudo networksetup -setdnsservers Wi-Fi Empty`. This script does not set DNS.
4. Tailscale may remain installed for unrelated tailnet access. Disabling or deleting the server's exit-node advertisement is a **separate** admin choice; do not do that merely to clean up one Mac.

## Development

```bash
bash -n scripts/travel-egress
shellcheck scripts/travel-egress
uv run --no-project python -m unittest discover -s tests -v
```

## License

MIT. See [LICENSE](LICENSE).
