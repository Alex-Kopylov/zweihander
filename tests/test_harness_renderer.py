"""Stage-2 renderer unit behavior on the fixture plugin tree.

Covers the harness-dist-build spec: action resolution, the wrapper filter's
two name shapes, narrative conditionals, file rules, fail-loud errors,
dev-file exclusion, mode-bit preservation, metadata stripping, and
manifest-driven membership.
"""

import json
import os
import re
from pathlib import Path

import pytest

from plugin_maintenance.render import (
    DEV_FILE_NAMES,
    FRONTMATTER_MATRIX_NAME,
    BuildError,
    render_tree,
)


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


class TestFrontmatterPortability:
    """`allowed-tools` is a key the harnesses place differently.

    Claude Code reads it at the top level; Codex documents no support for it,
    so the matrix sends it to `metadata`. The template declares it once and
    the renderer places it.
    """

    HEAD = '---\nname: demo\ndescription: "Demo skill."\n'

    def write_skill(self, repo: Path, frontmatter_tail: str) -> None:
        demo_template(repo).write_text(
            f"{self.HEAD}{frontmatter_tail}---\n\n# Demo\n", encoding="utf-8"
        )

    def test_claude_takes_allowed_tools_at_the_top_level(
        self, fixture_repo, fixture_matrix
    ):
        self.write_skill(fixture_repo, '{{ allowed_tools("Bash(git:*) Read") }}\n')

        text = demo_skill(render(fixture_repo, fixture_matrix, "ClaudeCode"))

        assert "\nallowed-tools: Bash(git:*) Read\n" in text
        assert "metadata:" not in text

    def test_codex_takes_allowed_tools_under_metadata(
        self, fixture_repo, fixture_matrix
    ):
        self.write_skill(fixture_repo, '{{ allowed_tools("Bash(git:*) Read") }}\n')

        text = demo_skill(render(fixture_repo, fixture_matrix, "Codex"))

        assert "\nmetadata:\n  allowed-tools: Bash(git:*) Read\n" in text
        assert "\nallowed-tools:" not in text

    @pytest.mark.parametrize("harness", ["ClaudeCode", "Codex"])
    def test_list_argument_joins_with_spaces(
        self, fixture_repo, fixture_matrix, harness
    ):
        self.write_skill(
            fixture_repo, '{{ allowed_tools(["Bash(git:*)", "Read"]) }}\n'
        )

        text = demo_skill(render(fixture_repo, fixture_matrix, harness))

        assert "allowed-tools: Bash(git:*) Read\n" in text

    @pytest.mark.parametrize("argument", ['""', "[]"])
    @pytest.mark.parametrize("harness", ["ClaudeCode", "Codex"])
    def test_empty_argument_emits_no_key(
        self, fixture_repo, fixture_matrix, harness, argument
    ):
        self.write_skill(fixture_repo, f"{{{{- allowed_tools({argument}) }}}}\n")

        text = demo_skill(render(fixture_repo, fixture_matrix, harness))

        assert "allowed-tools" not in text
        assert text == f"{self.HEAD}---\n\n# Demo\n"

    @pytest.mark.parametrize(
        "value", ["Bash(git: *)", "*Read", "Read # comment", "Read\nWrite"]
    )
    @pytest.mark.parametrize("harness", ["ClaudeCode", "Codex"])
    def test_unquotable_value_fails_the_build(
        self, fixture_repo, fixture_matrix, harness, value
    ):
        self.write_skill(fixture_repo, f"{{{{ allowed_tools({value!r}) }}}}\n")

        with pytest.raises(BuildError, match="allowed-tools"):
            render(fixture_repo, fixture_matrix, harness)


class TestArgumentFrontmatter:
    """`argument-hint` and `arguments` are Claude Code keys.

    The frontmatter matrix places both under `metadata` for Codex, which
    documents `name` and `description` only, the same way it places an
    `allowed-tools` grant.
    """

    HEAD = "---\nname: demo\n"

    def write_skill(self, repo: Path, frontmatter_tail: str) -> None:
        demo_template(repo).write_text(
            f"{self.HEAD}{frontmatter_tail}---\n\n# Demo\n", encoding="utf-8"
        )

    def test_claude_takes_both_keys_at_the_top_level(
        self, fixture_repo, fixture_matrix
    ):
        self.write_skill(
            fixture_repo,
            '{{ argument_hint("[items] to walk") }}\n{{ arguments("items") }}\n',
        )

        text = demo_skill(render(fixture_repo, fixture_matrix, "ClaudeCode"))

        assert '\nargument-hint: "[items] to walk"\n' in text
        assert "\narguments: items\n" in text
        assert "metadata:" not in text

    def test_codex_takes_both_keys_under_one_metadata_block(
        self, fixture_repo, fixture_matrix
    ):
        self.write_skill(
            fixture_repo,
            '{{ argument_hint("[items] to walk") }}\n{{ arguments("items") }}\n',
        )

        text = demo_skill(render(fixture_repo, fixture_matrix, "Codex"))

        assert text.count("metadata:") == 1
        assert '  argument-hint: "[items] to walk"\n' in text
        assert "  arguments: items\n" in text
        assert "\nargument-hint:" not in text
        assert "\narguments:" not in text

    @pytest.mark.parametrize("harness", ["ClaudeCode", "Codex"])
    def test_hint_is_quoted_so_yaml_reads_it_as_one_string(
        self, fixture_repo, fixture_matrix, harness
    ):
        """`argument-hint: [file] [format]` would otherwise parse as a list."""
        self.write_skill(fixture_repo, '{{ argument_hint("[file] [format]") }}\n')

        text = demo_skill(render(fixture_repo, fixture_matrix, harness))

        assert 'argument-hint: "[file] [format]"\n' in text

    @pytest.mark.parametrize("harness", ["ClaudeCode", "Codex"])
    def test_quotes_inside_a_hint_are_escaped(
        self, fixture_repo, fixture_matrix, harness
    ):
        self.write_skill(fixture_repo, """{{ argument_hint('say "hi"') }}\n""")

        text = demo_skill(render(fixture_repo, fixture_matrix, harness))

        assert 'argument-hint: "say \\"hi\\""\n' in text

    @pytest.mark.parametrize("harness", ["ClaudeCode", "Codex"])
    def test_argument_list_joins_with_spaces(
        self, fixture_repo, fixture_matrix, harness
    ):
        self.write_skill(fixture_repo, '{{ arguments(["issue", "branch"]) }}\n')

        text = demo_skill(render(fixture_repo, fixture_matrix, harness))

        assert "arguments: issue branch\n" in text

    @pytest.mark.parametrize("global_call", ["argument_hint", "arguments"])
    @pytest.mark.parametrize("argument", ['""', "[]"])
    @pytest.mark.parametrize("harness", ["ClaudeCode", "Codex"])
    def test_empty_argument_emits_no_key(
        self, fixture_repo, fixture_matrix, harness, global_call, argument
    ):
        self.write_skill(fixture_repo, f"{{{{- {global_call}({argument}) }}}}\n")

        text = demo_skill(render(fixture_repo, fixture_matrix, harness))

        assert text == f"{self.HEAD}---\n\n# Demo\n"

    @pytest.mark.parametrize("harness", ["ClaudeCode", "Codex"])
    def test_multi_line_hint_fails_the_build(
        self, fixture_repo, fixture_matrix, harness
    ):
        self.write_skill(fixture_repo, "{{ argument_hint('one\\ntwo') }}\n")

        with pytest.raises(BuildError, match="argument-hint"):
            render(fixture_repo, fixture_matrix, harness)

    @pytest.mark.parametrize("name", ["Items", "two words", "1st", "items!"])
    @pytest.mark.parametrize("harness", ["ClaudeCode", "Codex"])
    def test_name_that_cannot_spell_a_placeholder_fails_the_build(
        self, fixture_repo, fixture_matrix, harness, name
    ):
        self.write_skill(fixture_repo, f"{{{{ arguments([{name!r}]) }}}}\n")

        with pytest.raises(BuildError, match="placeholder"):
            render(fixture_repo, fixture_matrix, harness)


class TestPlacementComesFromTheMatrix:
    """Placement is data the renderer reads, not a branch it carries."""

    def repoint(self, matrix_path: Path, key: str, harness: str, placement: str) -> None:
        path = matrix_path.with_name(FRONTMATTER_MATRIX_NAME)
        matrix = json.loads(path.read_text(encoding="utf-8"))
        matrix["keys"][key][harness]["placement"] = placement
        path.write_text(json.dumps(matrix, indent=2) + "\n", encoding="utf-8")

    def write_skill(self, repo: Path, frontmatter_tail: str) -> None:
        demo_template(repo).write_text(
            f"---\nname: demo\n{frontmatter_tail}---\n\n# Demo\n", encoding="utf-8"
        )

    def test_flipping_a_placement_moves_the_key(self, fixture_repo, fixture_matrix):
        self.repoint(fixture_matrix, "argument-hint", "ClaudeCode", "metadata")
        self.write_skill(fixture_repo, '{{ argument_hint("[items]") }}\n')

        text = demo_skill(render(fixture_repo, fixture_matrix, "ClaudeCode"))

        assert '\nmetadata:\n  argument-hint: "[items]"\n' in text

    def test_a_key_outside_the_matrix_has_no_global(self, fixture_repo, fixture_matrix):
        self.write_skill(fixture_repo, '{{ model("opus") }}\n')

        with pytest.raises(BuildError, match="model"):
            render(fixture_repo, fixture_matrix, "ClaudeCode")

    def test_a_verbatim_key_has_no_global(self, fixture_repo, fixture_matrix):
        """`name` is written literally, so nothing places it."""
        self.write_skill(fixture_repo, '{{ name("demo") }}\n')

        with pytest.raises(BuildError, match="name"):
            render(fixture_repo, fixture_matrix, "ClaudeCode")


class TestFrontmatterMetadataMerge:
    """A Codex `allowed-tools` grant emits its own `metadata:` block.

    A skill that also hand-writes one would render a duplicate YAML key, so
    the renderer folds every block into the first.
    """

    BOTH_BLOCKS = (
        "---\n"
        "name: demo\n"
        '{{ allowed_tools("Read") }}\n'
        "metadata:\n"
        '  references:\n    "references/plain.md": "Load for the plain case."\n'
        "---\n\n# Demo\n"
    )

    def test_codex_folds_both_blocks_into_one(self, fixture_repo, fixture_matrix):
        demo_template(fixture_repo).write_text(self.BOTH_BLOCKS, encoding="utf-8")

        text = demo_skill(render(fixture_repo, fixture_matrix, "Codex"))

        assert text.count("metadata:") == 1
        assert "  allowed-tools: Read\n" in text
        assert '    "references/plain.md": "Load for the plain case."\n' in text

    def test_claude_keeps_the_hand_written_block_alone(
        self, fixture_repo, fixture_matrix
    ):
        demo_template(fixture_repo).write_text(self.BOTH_BLOCKS, encoding="utf-8")

        text = demo_skill(render(fixture_repo, fixture_matrix, "ClaudeCode"))

        assert text.count("metadata:") == 1
        assert "\nallowed-tools: Read\n" in text

    @pytest.mark.parametrize("harness", ["ClaudeCode", "Codex"])
    def test_single_block_file_is_untouched(
        self, fixture_repo, fixture_matrix, harness
    ):
        source = (
            "---\nname: demo\nmetadata:\n"
            '  origin:\n    url: "https://example.invalid/demo"\n'
            "---\n\n# Demo\n"
        )
        demo_template(fixture_repo).write_text(source, encoding="utf-8")

        text = demo_skill(render(fixture_repo, fixture_matrix, harness))

        assert text == source

    @pytest.mark.parametrize("harness", ["ClaudeCode", "Codex"])
    def test_duplicate_of_another_key_fails_the_build(
        self, fixture_repo, fixture_matrix, harness
    ):
        demo_template(fixture_repo).write_text(
            "---\nname: demo\ndescription: first\ndescription: second\n---\n",
            encoding="utf-8",
        )

        with pytest.raises(BuildError, match="description"):
            render(fixture_repo, fixture_matrix, harness)


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
