"""scripts/validate-patches.py の単体テスト。

ファイル名にハイフンを含みモジュールとして import できないため、
importlib で直接読み込む。
"""
import importlib.util
import pathlib

SCRIPT_PATH = (
    pathlib.Path(__file__).resolve().parent.parent / "scripts" / "validate-patches.py"
)

_spec = importlib.util.spec_from_file_location("validate_patches", SCRIPT_PATH)
validate_patches = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(validate_patches)


def test_validate_patch_accepts_valid_hunk(tmp_path):
    """hunk ヘッダの行数と本文が一致していればエラーなし。"""
    patch = tmp_path / "valid.patch"
    patch.write_text(
        "diff --git a/foo.txt b/foo.txt\n"
        "--- a/foo.txt\n"
        "+++ b/foo.txt\n"
        "@@ -1,2 +1,2 @@\n"
        " line1\n"
        "-line2\n"
        "+line2-changed\n",
        encoding="utf-8",
        newline="\n",
    )

    validate_patches.errors.clear()
    validate_patches.validate_patch(str(patch))

    assert validate_patches.errors == []


def test_validate_patch_detects_corrupt_hunk(tmp_path):
    """hunk ヘッダが -2,+2 なのに本文が +3 ある(過去に09/10/13/14で実際に起きた事故)。"""
    patch = tmp_path / "corrupt.patch"
    patch.write_text(
        "diff --git a/foo.txt b/foo.txt\n"
        "--- a/foo.txt\n"
        "+++ b/foo.txt\n"
        "@@ -1,2 +1,2 @@\n"
        " line1\n"
        "-line2\n"
        "+line2-changed\n"
        "+line3-extra\n",
        encoding="utf-8",
        newline="\n",
    )

    validate_patches.errors.clear()
    validate_patches.validate_patch(str(patch))

    assert len(validate_patches.errors) == 1
    assert "corrupt hunk" in validate_patches.errors[0]
