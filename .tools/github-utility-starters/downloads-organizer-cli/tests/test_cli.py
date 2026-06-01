from pathlib import Path
import tempfile
import unittest

from downloads_organizer.cli import build_plan, category_for


class DownloadsOrganizerTests(unittest.TestCase):
    def test_category_for_known_extensions(self) -> None:
        self.assertEqual(category_for(Path("photo.png")), "Images")
        self.assertEqual(category_for(Path("archive.zip")), "Archives")
        self.assertEqual(category_for(Path("unknown.custom")), "Other")

    def test_build_plan_does_not_move_files_already_in_target_folder(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            images = root / "Images"
            images.mkdir()
            photo = images / "photo.png"
            photo.write_text("image", encoding="utf-8")

            plans = build_plan(root, strategy="category")

        self.assertEqual(plans, [])

    def test_build_plan_chooses_category_destination(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            document = root / "notes.pdf"
            document.write_text("pdf", encoding="utf-8")

            plans = build_plan(root, strategy="category")

        self.assertEqual(len(plans), 1)
        self.assertEqual(plans[0].destination.name, "notes.pdf")
        self.assertEqual(plans[0].destination.parent.name, "Documents")


if __name__ == "__main__":
    unittest.main()

