from pathlib import Path

from theia_parse.util.files import with_suffix


class TestFiles:
    def test_with_suffix(self):
        path = Path("/a/test/path/file.tar.gz")

        mod_path = with_suffix(path, [".json.zip"])

        assert mod_path == Path("/a/test/path/file.tar.json.zip")

        mod_path = with_suffix(path, ".json.zip", [".tar", ".gz"])

        assert mod_path == Path("/a/test/path/file.json.zip")

        mod_path = with_suffix(
            path,
            ".json.zip",
            [".tar", ".gz"],
            keep_original_suffix=True,
        )

        assert mod_path == Path("/a/test/path/file.gz.json.zip")

        mod_path = with_suffix(
            path,
            [".json", ".zip"],
            keep_original_suffix=True,
        )

        assert mod_path == Path("/a/test/path/file.tar.gz.json.zip")
