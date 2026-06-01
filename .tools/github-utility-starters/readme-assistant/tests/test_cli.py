from pathlib import Path
import json
import tempfile
import unittest

from readme_assistant.cli import ProjectInfo, load_project_info, render_readme


class ReadmeAssistantTests(unittest.TestCase):
    def test_render_readme_contains_core_sections(self) -> None:
        readme = render_readme(
            ProjectInfo(
                name="Test Tool",
                description="A focused test helper.",
                features=["Fast", "Small"],
                usage="test-tool --help",
            )
        )

        self.assertIn("# Test Tool", readme)
        self.assertIn("## Features", readme)
        self.assertIn("- Fast", readme)
        self.assertIn("test-tool --help", readme)

    def test_load_project_info_from_json(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "project.json"
            path.write_text(
                json.dumps({"name": "JSON Tool", "features": ["Portable"]}),
                encoding="utf-8",
            )

            info = load_project_info(path)

        self.assertEqual(info.name, "JSON Tool")
        self.assertEqual(info.features, ["Portable"])


if __name__ == "__main__":
    unittest.main()

