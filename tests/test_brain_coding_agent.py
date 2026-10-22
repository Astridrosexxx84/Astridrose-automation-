import unittest

from brain_coding_agent import validate_patch


class GuardedCodeBuilderTests(unittest.TestCase):
    def test_allows_existing_app_ui_file(self):
        patch = "diff --git a/brain-app/app.js b/brain-app/app.js\n--- a/brain-app/app.js\n+++ b/brain-app/app.js\n@@ -1 +1 @@\n-old\n+new\n"
        self.assertEqual(validate_patch(patch), ["brain-app/app.js"])

    def test_rejects_workflow_changes(self):
        patch = "diff --git a/.github/workflows/brain-app-relay.yml b/.github/workflows/brain-app-relay.yml\n--- a/.github/workflows/brain-app-relay.yml\n+++ b/.github/workflows/brain-app-relay.yml\n@@ -1 +1 @@\n-old\n+new\n"
        with self.assertRaises(ValueError):
            validate_patch(patch)

    def test_rejects_new_files(self):
        patch = "diff --git a/brain-app/new.js b/brain-app/new.js\n--- /dev/null\n+++ b/brain-app/new.js\n@@ -0,0 +1 @@\n+new\n"
        with self.assertRaises(ValueError):
            validate_patch(patch)

    def test_rejects_credential_like_content(self):
        patch = "diff --git a/brain-app/app.js b/brain-app/app.js\n--- a/brain-app/app.js\n+++ b/brain-app/app.js\n@@ -1 +1 @@\n-old\n+ghp_abcdefghijklmnopqrstuvwxyz0123456789\n"
        with self.assertRaises(ValueError):
            validate_patch(patch)


if __name__ == "__main__":
    unittest.main()
