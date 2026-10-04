---
name: tailscale-travel-egress
description: Diagnose and configure a personal Tailscale exit node for a macOS client on restrictive hotel Wi-Fi, including captive portals, narrow route exceptions, verification, and cleanup. Use for travel network egress troubleshooting.
compatibility: macOS client with Tailscale; trusted Linux exit node; Bash 3.2+.
---

# Tailscale travel egress

This skill accompanies [`../../scripts/travel-egress`](../../scripts/travel-egress) and the [README](../../README.md). Resolve script paths relative to this `SKILL.md` directory. Do not assume the host has this repository installed.

## Decision flow

1. **Inspect, don't guess.** Identify the active interface, physical gateway, captive-portal state, Tailscale connection, exit-node approval, and whether the user already has other VPN filters. Do not print auth keys or private tailnet inventories in public artifacts.
2. **Portal first.** Disconnect any exit node, complete the Wi-Fi portal, confirm ordinary internet access. Test blocked and unblocked sites separately; failures may have several causes.
3. **Server setup is opt-in.** Before changing a remote server, confirm the chosen node and its role. Follow [official exit-node setup](https://tailscale.com/docs/features/exit-nodes/how-to/setup) for persistent forwarding, advertisement, admin approval, firewall, and grants. Do not mint or approve interactive account-auth links for the user.
4. **Client exit node.** Ask before changing the default route. Run `travel-egress on --exit-node NAME` and verify the public egress IP, ordinary HTTPS, and the user's actual app. If it fails, run `travel-egress off` and restore connectivity. Avoid equating a `route get` result with proof of a specific installed route.
5. **Narrow exceptions only when proven necessary.** A direct route leaks matching destinations to the local ISP. Check all apps that share an IP range (especially CDNs). Use `travel-egress route-add --bypass-cidr CIDR`, inspect routing *while the exit node is on*, then test both the affected app and other apps. Do not hardcode a user's tailnet IP, hostname, hotel gateway, domain, or CDN range into reusable scripts.
6. **Cleanup.** Remove only routes/configuration introduced for this task. Restore DNS separately if it was changed. Leave Tailscale installed if it serves other purposes.

A relay path and exit-node IP do not prove every protocol works. Report observed results and uncertainty. If the node is ephemeral or has key expiry enabled, explain the reliability risk; the admin console owner decides the key-expiry policy.
