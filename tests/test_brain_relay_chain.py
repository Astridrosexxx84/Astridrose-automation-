"""Offline tests for sequential relay orchestration; no provider APIs are called."""
import json
import os
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

import brain_relay_chain as chain


class RelayChainTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.paths = {
            "PACKET_MD": self.root / "brain-relay-packet.md",
            "PACKET_JSON": self.root / "brain-relay-packet.json",
            "STATUS_JSON": self.root / "brain-relay-status.json",
        }
        self.path_patches = [
            patch.object(chain, name, path) for name, path in self.paths.items()
        ]
        for item in self.path_patches:
            item.start()
        self.old_cwd = os.getcwd()
        os.chdir(self.root)

    def tearDown(self):
        os.chdir(self.old_cwd)
        for item in reversed(self.path_patches):
            item.stop()
        self.temp.cleanup()

    def test_successful_workers_receive_previous_successful_packet(self):
        observed = []

        def fake_run(command, env, check):
            provider = env["AI_RELAY_PROVIDER"]
            observed.append((provider, env.get("AI_RELAY_PRIOR_PACKET", "")))
            answer = "artifact from " + provider
            record = {
                "provider": provider,
                "model": "mock-model",
                "outcome": "success",
                "worker_output": answer,
                "next_action": "Continue after " + provider,
            }
            chain.PACKET_JSON.write_text(json.dumps(record), encoding="utf-8")
            chain.PACKET_MD.write_text(answer, encoding="utf-8")
            return SimpleNamespace(returncode=0)

        with patch.dict(os.environ, {
            "AI_RELAY_TASK": "test goal",
            "AI_RELAY_PROVIDER": "auto",
            "AI_RELAY_ROLE": "create",
            "AI_RELAY_PRIOR_PACKET": "seed packet",
        }, clear=False), patch.object(chain.subprocess, "run", side_effect=fake_run):
            chain.main()

        self.assertEqual([x[0] for x in observed], ["groq", "gemini", "openrouter"])
        self.assertEqual(observed[0][1], "seed packet")
        self.assertEqual(observed[1][1], "artifact from openrouter")
        self.assertEqual(observed[2][1], "artifact from groq")
        final = json.loads(self.paths["PACKET_JSON"].read_text(encoding="utf-8"))
        self.assertEqual(final["overall_outcome"], "success")
        self.assertEqual(final["successful_turns"], 3)
        self.assertEqual(final["total_turns"], 3)

    def test_failed_worker_does_not_reuse_previous_packet_as_its_result(self):
        observed = []

        def fake_run(command, env, check):
            provider = env["AI_RELAY_PROVIDER"]
            observed.append((provider, env.get("AI_RELAY_PRIOR_PACKET", "")))
            if provider == "groq":
                record = {
                    "provider": provider, "model": "mock", "outcome": "success",
                    "worker_output": "first artifact", "next_action": "next",
                }
                chain.PACKET_JSON.write_text(json.dumps(record), encoding="utf-8")
                chain.PACKET_MD.write_text("first artifact", encoding="utf-8")
                return SimpleNamespace(returncode=0)
            if provider == "gemini":
                # Simulate a worker exiting before it can write its own packet.
                return SimpleNamespace(returncode=1)
            record = {
                "provider": provider, "model": "mock", "outcome": "success",
                "worker_output": "third artifact", "next_action": "done",
            }
            chain.PACKET_JSON.write_text(json.dumps(record), encoding="utf-8")
            chain.PACKET_MD.write_text("third artifact", encoding="utf-8")
            return SimpleNamespace(returncode=0)

        with patch.dict(os.environ, {
            "AI_RELAY_TASK": "test goal",
            "AI_RELAY_PROVIDER": "auto",
            "AI_RELAY_ROLE": "create",
            "AI_RELAY_PRIOR_PACKET": "",
        }, clear=False), patch.object(chain.subprocess, "run", side_effect=fake_run):
            chain.main()

        self.assertEqual(observed[2][1], "first artifact")
        final = json.loads(self.paths["PACKET_JSON"].read_text(encoding="utf-8"))
        self.assertEqual(final["successful_turns"], 2)
        self.assertEqual(final["turns"][1]["outcome"], "error")
        self.assertIn("without producing its own readable packet", final["turns"][1]["error_category"])


if __name__ == "__main__":
    unittest.main()
