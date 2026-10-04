"""Behavior tests with stubbed system commands; never mutate the host network."""
import os
from pathlib import Path
import subprocess
import tempfile
import unittest

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "travel-egress"


class TravelEgressTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        root = Path(self.tmp.name)
        self.log = root / "commands.log"
        stubs = {
            "tailscale": '''#!/bin/sh
printf 'tailscale %s\n' "$*" >> "$MOCK_LOG"
''',
            "route": '''#!/bin/sh
printf 'route %s\n' "$*" >> "$MOCK_LOG"
if [ "$1 $2 $3" = '-n get -ifscope' ]; then
  if [ "${MOCK_NO_GATEWAY:-0}" = 0 ]; then printf '   gateway: 192.0.2.1\n  interface: en0\n'; fi
fi
''',
            "sudo": '''#!/bin/sh
printf 'sudo %s\n' "$*" >> "$MOCK_LOG"
if [ "$1" != '-v' ]; then "$@"; fi
''',
        }
        for name, body in stubs.items():
            path = root / name
            path.write_text(body)
            path.chmod(0o755)
        self.env = os.environ.copy()
        for name in ("TRAVEL_EXIT_NODE", "TRAVEL_BYPASS_CIDR", "TRAVEL_INTERFACE"):
            self.env.pop(name, None)
        self.env.update(PATH=f"{root}:/usr/bin:/bin", MOCK_LOG=str(self.log))

    def run_tool(self, *args, **env):
        return subprocess.run([str(SCRIPT), *args], env={**self.env, **env},
                              text=True, capture_output=True, check=False)

    def commands(self):
        return self.log.read_text().splitlines() if self.log.exists() else []

    def test_on_off(self):
        self.assertEqual(self.run_tool("on", "--exit-node", "my-node").returncode, 0)
        self.assertEqual(self.run_tool("off").returncode, 0)
        self.assertEqual(self.commands(), [
            "tailscale set --exit-node=my-node --exit-node-allow-lan-access=true",
            "tailscale set --exit-node=",
        ])

    def test_route_add_uses_physical_gateway(self):
        result = self.run_tool("route-add", "--bypass-cidr", "203.0.113.0/24")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(self.commands(), [
            "route -n get -ifscope en0 default",
            "sudo -v",
            "sudo route -n delete -net 203.0.113.0/24",
            "route -n delete -net 203.0.113.0/24",
            "sudo route -n add -net 203.0.113.0/24 192.0.2.1",
            "route -n add -net 203.0.113.0/24 192.0.2.1",
        ])

    def test_no_gateway_does_not_mutate(self):
        result = self.run_tool("route-add", "--bypass-cidr", "203.0.113.0/24", MOCK_NO_GATEWAY="1")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("no gateway", result.stderr)
        self.assertEqual(self.commands(), ["route -n get -ifscope en0 default"])

    def test_cidr_is_required_and_validated(self):
        self.assertNotEqual(self.run_tool("route-add").returncode, 0)
        self.assertNotEqual(self.run_tool("route-add", "-c", "bad;rm -rf /").returncode, 0)
        self.assertNotEqual(self.run_tool("route-add", "-c", "0.0.0.0/0").returncode, 0)
        self.assertEqual(self.commands(), [])

    def test_route_delete(self):
        result = self.run_tool("route-del", "-c", "203.0.113.0/24")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("sudo route -n delete -net 203.0.113.0/24", self.commands())


if __name__ == "__main__":
    unittest.main()
