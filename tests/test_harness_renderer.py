"""Stage-2 renderer unit behavior on the fixture plugin tree.

Covers the harness-dist-build spec: action resolution, the wrapper filter's
two name shapes, narrative conditionals, file rules, fail-loud errors,
dev-file exclusion, mode-bit preservation, metadata stripping, and
manifest-driven membership.
"""

import os
import re
from pathlib import Path

import pytest

from plugin_maintenance.render import DEV_FILE_NAMES, BuildError, render_tree


def render(repo: Path, matrix: Path, harness: str) -> Path:
    output = repo / "dist-under-test" / harness
    render_tree(repo, harness, output, matrix_path=matrix)
    return output


def demo_skill(output: Path) -> str:
    return (output / "demo-plugin" / "skills" / "demo" / "SKILL.md").read_text(
        encoding="utf-8"
    )


def demo_template(repo: Path) -> Path:
    return repo / "plugins" / "demo-plugin" / "skills" / "demo" / "SKILL.md.j2"


class TestActionResolution:
    def test_claude_actions_resolve_to_claude_names(self, fixture_repo, fixture_matrix):
        text = demo_skill(render(fixture_repo, fixture_matrix, "ClaudeCode"))

        assert "Skill(AskUserQuestion)" in text
        assert "the AskUserQuestion mechanism" in text
        assert "Skill(Agent)" in text

    def test_codex_actions_resolve_to_codex_names(self, fixture_repo, fixture_matrix):
        text = demo_skill(render(fixture_repo, fixture_matrix, "Codex"))

        assert "$request_user_input" in text
        assert "the request_user_input mechanism" in text
        assert "$spawn_agent" in text


class TestWrapperFilter:
    @pytest.mark.parametrize(
        ("harness", "bare", "qualified"),
        [
            ("ClaudeCode", "Skill(commit)", "Skill(dev-workflow:commit)"),
            ("Codex", "$commit", "$dev-workflow:commit"),
        ],
    )
    def test_wrapper_covers_bare_and_qualified_names(
        self, fixture_repo, fixture_matrix, harness, bare, qualified
    ):
        text = demo_skill(render(fixture_repo, fixture_matrix, harness))

        assert bare in text
        assert qualified in text


class TestNarrativeConditional:
    def test_each_harness_keeps_only_its_own_narrative(
        self, fixture_repo, fixture_matrix
    ):
        claude = demo_skill(render(fixture_repo, fixture_matrix, "ClaudeCode"))
        codex = demo_skill(render(fixture_repo, fixture_matrix, "Codex"))

        assert "Claude Code-specific narrative." in claude
        assert "Codex-specific narrative." not in claude
        assert "Codex-specific narrative." in codex
        assert "Claude Code-specific narrative." not in codex


class TestFileRules:
    def test_plain_file_copied_byte_for_byte(self, fixture_repo, fixture_matrix):
        source = (
            fixture_repo
            / "plugins"
            / "demo-plugin"
            / "skills"
            / "demo"
            / "references"
            / "plain.md"
        )
        output = render(fixture_repo, fixture_matrix, "ClaudeCode")
        copied = output / "demo-plugin" / "skills" / "demo" / "references" / "plain.md"

        assert copied.read_bytes() == source.read_bytes()

    def test_template_suffix_stripped_and_absent_from_output(
        self, fixture_repo, fixture_matrix
    ):
        output = render(fixture_repo, fixture_matrix, "ClaudeCode")

        assert (output / "demo-plugin" / "skills" / "demo" / "SKILL.md").is_file()
        assert not list(output.rglob("*.j2"))

    def test_raw_block_emits_literal_braces(self, fixture_repo, fixture_matrix):
        text = demo_skill(render(fixture_repo, fixture_matrix, "ClaudeCode"))

        assert "{{COMPANY}}" in text

    @pytest.mark.parametrize(
        ("open_tag", "close_tag"),
        [
            ("{% raw %}", "{% endraw %}"),
            ("{%raw%}", "{%endraw%}"),
            ("{%- raw -%}", "{%- endraw -%}"),
            ("{% raw -%}", "{%- endraw %}"),
        ],
    )
    def test_every_raw_spelling_emits_literal_braces(
        self, fixture_repo, fixture_matrix, open_tag, close_tag
    ):
        template = demo_template(fixture_repo)
        template.write_text(
            f"Ask via {{{{ actions.AskUser | call }}}}.\n"
            f"{open_tag}\nKeep the literal {{{{COMPANY}}}} placeholder.\n{close_tag}\n",
            encoding="utf-8",
        )

        text = demo_skill(render(fixture_repo, fixture_matrix, "ClaudeCode"))

        assert "Skill(AskUserQuestion)" in text
        assert "{{COMPANY}}" in text

    def test_rendered_output_has_no_leftover_markers(
        self, fixture_repo, fixture_matrix
    ):
        text = demo_skill(render(fixture_repo, fixture_matrix, "ClaudeCode"))

        for marker in ("{%", "%}", "{{ actions", "| call"):
            assert marker not in text

    def test_plain_template_collision_fails_naming_the_path(
        self, fixture_repo, fixture_matrix
    ):
        colliding = (
            fixture_repo / "plugins" / "demo-plugin" / "skills" / "demo" / "SKILL.md"
        )
        colliding.write_text("collides\n", encoding="utf-8")

        with pytest.raises(BuildError, match="SKILL.md"):
            render(fixture_repo, fixture_matrix, "ClaudeCode")

    def test_executable_bit_survives(self, fixture_repo, fixture_matrix):
        output = render(fixture_repo, fixture_matrix, "ClaudeCode")
        hook = output / "demo-plugin" / "scripts" / "hook.sh"

        assert os.access(hook, os.X_OK)


class TestFailLoud:
    def test_missing_action_names_action_and_harness(
        self, fixture_repo, fixture_matrix
    ):
        template = (
            fixture_repo
            / "plugins"
            / "demo-plugin"
            / "skills"
            / "demo"
            / "SKILL.md.j2"
        )
        template.write_text("{{ actions.NoSuchAction | call }}\n", encoding="utf-8")

        with pytest.raises(BuildError, match=r"NoSuchAction.*ClaudeCode"):
            render(fixture_repo, fixture_matrix, "ClaudeCode")

    @pytest.mark.parametrize(
        ("open_tag", "close_tag"),
        [("{% raw %}", "{% endraw %}"), ("{%- raw -%}", "{%- endraw -%}")],
    )
    def test_marker_outside_a_raw_block_fails_the_build(
        self, fixture_repo, fixture_matrix, open_tag, close_tag
    ):
        """A raw block exempts its own text only, never the whole file."""
        template = demo_template(fixture_repo)
        template.write_text(
            f"{open_tag}\nKeep the literal {{{{COMPANY}}}} placeholder.\n{close_tag}\n"
            "Ask via {{ '{{ actions.AskUser | call }}' }}.\n",
            encoding="utf-8",
        )

        with pytest.raises(BuildError, match=re.escape("Jinja marker '{{'")):
            render(fixture_repo, fixture_matrix, "ClaudeCode")

        assert not (fixture_repo / "dist-under-test" / "ClaudeCode").exists()

    def test_unknown_harness_fails_before_rendering(
        self, fixture_repo, fixture_matrix
    ):
        with pytest.raises(BuildError, match="Gemini"):
            render(fixture_repo, fixture_matrix, "Gemini")

        assert not (fixture_repo / "dist-under-test" / "Gemini").exists()

    def test_failed_build_leaves_no_partial_tree(self, fixture_repo, fixture_matrix):
        template = (
            fixture_repo
            / "plugins"
            / "demo-plugin"
            / "skills"
            / "demo"
            / "SKILL.md.j2"
        )
        template.write_text("{{ actions.NoSuchAction | call }}\n", encoding="utf-8")

        with pytest.raises(BuildError):
            render(fixture_repo, fixture_matrix, "ClaudeCode")

        assert not (fixture_repo / "dist-under-test" / "ClaudeCode").exists()


class TestTreeMembership:
    def test_dev_files_never_emitted(self, fixture_repo, fixture_matrix):
        for harness in ("ClaudeCode", "Codex"):
            output = render(fixture_repo, fixture_matrix, harness)
            emitted = {path.name for path in output.rglob("*") if path.is_file()}

            assert not emitted & {"AGENTS.md", "CLAUDE.md", "README.md"}

    @pytest.mark.parametrize("dev_name", sorted(DEV_FILE_NAMES))
    @pytest.mark.parametrize("harness", ["ClaudeCode", "Codex"])
    def test_dev_file_template_fails_instead_of_emitting(
        self, fixture_repo, fixture_matrix, harness, dev_name
    ):
        template = fixture_repo / "plugins" / "plain-plugin" / f"{dev_name}.j2"
        template.write_text("Rendered for {{ harness }}.\n", encoding="utf-8")

        with pytest.raises(BuildError, match=re.escape(f"{dev_name}.j2")):
            render(fixture_repo, fixture_matrix, harness)

        assert not (fixture_repo / "dist-under-test" / harness).exists()

    def test_foreign_runtime_metadata_stripped(self, fixture_repo, fixture_matrix):
        claude = render(fixture_repo, fixture_matrix, "ClaudeCode")
        codex = render(fixture_repo, fixture_matrix, "Codex")

        assert (claude / "demo-plugin" / ".claude-plugin" / "plugin.json").is_file()
        assert not list(claude.rglob(".codex-plugin"))
        assert (codex / "demo-plugin" / ".codex-plugin" / "plugin.json").is_file()
        assert not list(codex.rglob(".claude-plugin"))

    def test_membership_follows_each_harness_manifest(
        self, fixture_repo, fixture_matrix
    ):
        claude = render(fixture_repo, fixture_matrix, "ClaudeCode")
        codex = render(fixture_repo, fixture_matrix, "Codex")

        assert (claude / "plain-plugin" / "skills" / "plain" / "SKILL.md").is_file()
        assert (codex / "plain-plugin" / "skills" / "plain" / "SKILL.md").is_file()
        assert (codex / "codex-only-plugin").is_dir()
        assert not (claude / "codex-only-plugin").exists()
        assert not (claude / "unlisted-plugin").exists()
        assert not (codex / "unlisted-plugin").exists()


class TestIgnoredArtifacts:
    """`.gitignore` is the one list of paths that are not repository content.

    Tooling drops artifacts into `plugins/` — `__pycache__/` from running a
    plugin's own scripts, `.DS_Store` from a file browser, `*.local.md` from
    scratch notes. The renderer must leave every one of them behind.
    """

    IGNORE_RULES = "__pycache__/\n.DS_Store\n*.local.md\n.venv/\n"

    def _plant_artifacts(self, fixture_repo: Path) -> None:
        (fixture_repo / ".gitignore").write_text(self.IGNORE_RULES, encoding="utf-8")
        plugin = fixture_repo / "plugins" / "plain-plugin"
        skill = plugin / "skills" / "plain"
        (skill / "__pycache__").mkdir(parents=True)
        (skill / "__pycache__" / "helper.cpython-314.pyc").write_bytes(b"\x00cached")
        (plugin / ".DS_Store").write_bytes(b"\x00finder")
        (skill / "notes.local.md").write_text("scratch notes\n", encoding="utf-8")
        (plugin / ".venv" / "lib").mkdir(parents=True)
        (plugin / ".venv" / "lib" / "site.py").write_text("x = 1\n", encoding="utf-8")

    @pytest.mark.parametrize("harness", ["ClaudeCode", "Codex"])
    def test_gitignored_artifacts_never_reach_the_tree(
        self, fixture_repo, fixture_matrix, harness
    ):
        self._plant_artifacts(fixture_repo)

        output = render(fixture_repo, fixture_matrix, harness)
        emitted = sorted(
            path.relative_to(output).as_posix() for path in output.rglob("*")
        )

        assert not [name for name in emitted if "__pycache__" in name]
        assert not [name for name in emitted if name.endswith(".DS_Store")]
        assert not [name for name in emitted if name.endswith(".local.md")]
        assert not [name for name in emitted if ".venv" in name]
        assert "plain-plugin/skills/plain/SKILL.md" in emitted

    def test_untracked_generated_content_still_ships(self, fixture_repo, fixture_matrix):
        """Stage 1 writes into `plugins/` before anything is committed.

        The weekly Mermaid sync rewrites `skills/mermaid/references/` and can
        add a brand-new upstream document, then builds before the bot commits.
        Publication must follow `.gitignore`, never the git index.
        """
        (fixture_repo / ".gitignore").write_text(self.IGNORE_RULES, encoding="utf-8")
        generated = (
            fixture_repo
            / "plugins"
            / "plain-plugin"
            / "skills"
            / "plain"
            / "references"
            / "generated.md"
        )
        generated.parent.mkdir(parents=True)
        generated.write_text("# Written by stage 1\n", encoding="utf-8")

        output = render(fixture_repo, fixture_matrix, "ClaudeCode")

        shipped = output / "plain-plugin" / "skills" / "plain" / "references"
        assert (shipped / "generated.md").read_text(encoding="utf-8") == (
            "# Written by stage 1\n"
        )


class TestPublishedTreeMode:
    """The staging rename must not publish `mkdtemp`'s private 0o700 mode."""

    def test_new_tree_takes_the_parent_directory_mode(
        self, fixture_repo, fixture_matrix
    ):
        output = fixture_repo / "dist-under-test" / "ClaudeCode"
        output.parent.mkdir(parents=True)
        output.parent.chmod(0o770)

        render_tree(fixture_repo, "ClaudeCode", output, matrix_path=fixture_matrix)

        assert output.stat().st_mode & 0o777 == 0o770

    def test_rebuild_repairs_a_private_tree_mode(self, fixture_repo, fixture_matrix):
        output = render(fixture_repo, fixture_matrix, "ClaudeCode")
        output.parent.chmod(0o770)
        output.chmod(0o700)

        render_tree(fixture_repo, "ClaudeCode", output, matrix_path=fixture_matrix)

        assert output.stat().st_mode & 0o777 == 0o770

    def test_nested_directories_match_a_plain_mkdir(self, fixture_repo, fixture_matrix):
        output = render(fixture_repo, fixture_matrix, "ClaudeCode")
        reference = fixture_repo / "mkdir-reference"
        reference.mkdir()

        nested = {
            path.stat().st_mode & 0o777 for path in output.rglob("*") if path.is_dir()
        }

        assert nested == {reference.stat().st_mode & 0o777}

    def test_stray_file_at_the_output_path_is_replaced(
        self, fixture_repo, fixture_matrix
    ):
        output = fixture_repo / "dist-under-test" / "ClaudeCode"
        output.parent.mkdir(parents=True)
        output.write_text("stale artifact\n", encoding="utf-8")

        render_tree(fixture_repo, "ClaudeCode", output, matrix_path=fixture_matrix)

        assert (output / "demo-plugin" / "skills" / "demo" / "SKILL.md").is_file()
