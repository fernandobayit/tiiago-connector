#!/usr/bin/env python3
"""Apply the TI•IA•GO brand layer on top of upstream a0-connector sources.

This fork (fernandobayit/tiiago-connector) tracks upstream agent0ai/a0-connector.
Upstream merges land on ``main`` through ``.github/workflows/sync-upstream.yml``,
which re-runs this script afterwards. Everything in the brand layer is:

- **Cosmetic or additive**: package/CLI rename, titles, URLs, docs, tests.
- **Idempotent**: safe to run repeatedly; every edit is a no-op once applied.
- **Protocol-safe**: never renames shared identifiers with Agent Zero Core —
  plugin ``_a0_connector``, protocol ``a0-connector.v1``, routes
  ``/api/plugins/_a0_connector/v1/``, env vars ``A0_*``/``AGENT_ZERO_*``,
  ``constraints/a0-*.txt`` filenames, or the ``agent_zero_cli`` package.

Usage:
    python3 devtools/apply_tiiago_brand.py [--check]

``--check`` reports pending changes without writing and exits 1 when any
patch would be applied.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
BRAND = "TI•IA•GO"
CLI_NAME = "tiiago"
FORK_REPO = "fernandobayit/tiiago-connector"
UPSTREAM_REPO = "agent0ai/a0-connector"

FORK_URL = f"https://github.com/{FORK_REPO}"
UPSTREAM_URL = f"https://github.com/{UPSTREAM_REPO}"

# (relative_path, old, new, count). count=None replaces every occurrence.
# A patch whose ``old`` is gone but ``new`` present is already applied;
# one whose ``old`` is absent entirely is reported as MISSING (upstream
# drift) and never fails the run.
PATCHES: list[tuple[str, str, str, int | None]] = [
    # --- pyproject.toml: distribution identity --------------------------------
    (
        "pyproject.toml",
        'name = "a0"',
        f'name = "{CLI_NAME}"',
        1,
    ),
    (
        "pyproject.toml",
        'description = "Terminal chat interface for Agent Zero"',
        f'description = "{BRAND} — Terminal chat interface for Agent Zero"',
        1,
    ),
    (
        "pyproject.toml",
        '    { name = "agent0ai" },',
        f'    {{ name = "{BRAND}" }},',
        1,
    ),
    (
        "pyproject.toml",
        'keywords = ["agent-zero", "a0", "cli", "textual", "tui"]',
        f'keywords = ["agent-zero", "a0", "{CLI_NAME}", "cli", "textual", "tui"]',
        1,
    ),
    (
        "pyproject.toml",
        f'Homepage = "{UPSTREAM_URL}"',
        f'Homepage = "{FORK_URL}"',
        1,
    ),
    (
        "pyproject.toml",
        f'Repository = "{UPSTREAM_URL}"',
        f'Repository = "{FORK_URL}"',
        1,
    ),
    (
        "pyproject.toml",
        f'Issues = "{UPSTREAM_URL}/issues"',
        f'Issues = "{FORK_URL}/issues"',
        1,
    ),
    (
        "pyproject.toml",
        '[project.scripts]\na0 = "agent_zero_cli.__main__:main"',
        '[project.scripts]\n'
        f'{CLI_NAME} = "agent_zero_cli.__main__:main"\n'
        'a0 = "agent_zero_cli.__main__:main"',
        1,
    ),
    # --- __main__.py: CLI identity + default-host/autoconnect help ------------
    (
        "src/agent_zero_cli/__main__.py",
        'prog="a0",',
        f'prog="{CLI_NAME}",',
        1,
    ),
    (
        "src/agent_zero_cli/__main__.py",
        'description="Terminal chat interface for Agent Zero.",',
        f'description="{BRAND} — Terminal chat interface for Agent Zero.",',
        1,
    ),
    (
        "src/agent_zero_cli/__main__.py",
        'help="Print the installed a0 version and exit.",',
        f'help="Print the installed {CLI_NAME} version and exit.",',
        1,
    ),
    (
        "src/agent_zero_cli/__main__.py",
        '"Connection defaults resolve from --host, then AGENT_ZERO_HOST, then "',
        '"Connection defaults resolve from --host, then AGENT_ZERO_HOST / TIIAGO_DEFAULT_HOST, then "',
        1,
    ),
    (
        "src/agent_zero_cli/__main__.py",
        'f"Defaults to AGENT_ZERO_HOST or {DEFAULT_HOST}."',
        'f"Defaults to AGENT_ZERO_HOST / TIIAGO_DEFAULT_HOST or {DEFAULT_HOST}."',
        1,
    ),
    (
        "src/agent_zero_cli/__main__.py",
        'help="Connect to the configured host immediately instead of opening the host picker.",',
        'help=(\n'
        '            "Connect to the configured host immediately instead of opening the host picker. "\n'
        '            "Auto-connect is the default; set TIIAGO_AUTOCONNECT=0 to disable."\n'
        '        ),',
        1,
    ),
    # v1->v2 repair: early fork builds used opt-in auto-connect wording/condition.
    (
        "src/agent_zero_cli/__main__.py",
        '"TIIAGO_AUTOCONNECT=1 makes this the default."',
        '"Auto-connect is the default; set TIIAGO_AUTOCONNECT=0 to disable."',
        0,
    ),
    (
        "src/agent_zero_cli/__main__.py",
        "if connect_configured_host or (not host and autoconnect_default_enabled()):",
        "if connect_configured_host or autoconnect_default_enabled():",
        0,
    ),
    (
        "src/agent_zero_cli/__main__.py",
        'help="Update the installed a0 tool and exit.",',
        f'help="Update the installed {CLI_NAME} tool and exit.",',
        1,
    ),
    # Feature: TIIAGO_AUTOCONNECT=1 skips the host picker for the configured host.
    (
        "src/agent_zero_cli/__main__.py",
        (
            "    config = load_config()\n"
            "    if host:\n"
            "        config.instance_url = host\n"
            "    if chat:\n"
            "        config.default_context_id = chat\n"
            "    elif chat_last:\n"
            '        config.default_context_id = ""\n'
            "    app = AgentZeroCLI("
        ),
        (
            "    config = load_config()\n"
            "    if host:\n"
            "        config.instance_url = host\n"
            "    if chat:\n"
            "        config.default_context_id = chat\n"
            "    elif chat_last:\n"
            '        config.default_context_id = ""\n'
            "    from agent_zero_cli.config import autoconnect_default_enabled\n"
            "\n"
            "    if connect_configured_host or autoconnect_default_enabled():\n"
            "        connect_configured_host = True\n"
            "    app = AgentZeroCLI("
        ),
        1,
    ),
    # --- config.py: TIIAGO_DEFAULT_HOST fallback + autoconnect reader ---------
    (
        "src/agent_zero_cli/config.py",
        '_VALID_HOST_BROWSER_RELAUNCH_PREFERENCES = {"ask", "manual"}',
        '_VALID_HOST_BROWSER_RELAUNCH_PREFERENCES = {"ask", "manual"}\n'
        '_DEFAULT_HOST_KEY = "TIIAGO_DEFAULT_HOST"\n'
        '_AUTOCONNECT_KEY = "TIIAGO_AUTOCONNECT"',
        1,
    ),
    (
        "src/agent_zero_cli/config.py",
        '    instance_url = os.environ.get("AGENT_ZERO_HOST") or dotenv.get("AGENT_ZERO_HOST", "")',
        "    instance_url = (\n"
        '        os.environ.get("AGENT_ZERO_HOST")\n'
        "        or os.environ.get(_DEFAULT_HOST_KEY)\n"
        '        or dotenv.get("AGENT_ZERO_HOST", "")\n'
        '        or dotenv.get(_DEFAULT_HOST_KEY, "")\n'
        "    )",
        1,
    ),
    # --- client.py: compiled-in default host -----------------------------------
    (
        "src/agent_zero_cli/client.py",
        'DEFAULT_HOST = "http://localhost:5080"',
        'DEFAULT_HOST = "https://a0.bayit.me"',
        1,
    ),
    # --- config.py: autoconnect reader (defaults ON) -----------------------------
    (
        "src/agent_zero_cli/config.py",
        "def load_config() -> CLIConfig:",
        (
            "def autoconnect_default_enabled() -> bool:\n"
            '    """Auto-connect the configured host on startup unless TIIAGO_AUTOCONNECT disables it."""\n'
            "    return _parse_bool(\n"
            "        os.environ.get(_AUTOCONNECT_KEY, _read_dotenv().get(_AUTOCONNECT_KEY, \"\")),\n"
            "        default=True,\n"
            "    )\n"
            "\n"
            "\n"
            "def load_config() -> CLIConfig:"
        ),
        1,
    ),
    # --- app.py: TUI identity --------------------------------------------------
    (
        "src/agent_zero_cli/app.py",
        'TITLE = "Agent Zero CLI"',
        f'TITLE = "{BRAND}"',
        1,
    ),
    (
        "src/agent_zero_cli/app.py",
        'title="a0 CLI update available",',
        f'title="{CLI_NAME} CLI update available",',
        1,
    ),
    # --- splash_view.py: user-visible strings ----------------------------------
    (
        "src/agent_zero_cli/widgets/splash_view.py",
        'Static("Local Agent Zero instances", classes="splash-panel-title")',
        f'Static("Local {BRAND} instances", classes="splash-panel-title")',
        1,
    ),
    (
        "src/agent_zero_cli/widgets/splash_view.py",
        '"Detected Agent Zero WebUI endpoints. Manual URL entry is available below.",',
        f'"Detected {BRAND} WebUI endpoints. Manual URL entry is available below.",',
        1,
    ),
    (
        "src/agent_zero_cli/widgets/splash_view.py",
        '"Use this for remote Agent Zero hosts or anything Docker cannot see. Standard ports are optional.",',
        f'"Use this for remote {BRAND} hosts or anything Docker cannot see. Standard ports are optional.",',
        1,
    ),
    (
        "src/agent_zero_cli/widgets/splash_view.py",
        'return Text("Checking Docker for local Agent Zero instances...", style="#9aa7b4")',
        f'return Text("Checking Docker for local {BRAND} instances...", style="#9aa7b4")',
        1,
    ),
    (
        "src/agent_zero_cli/widgets/splash_view.py",
        'return Text(f"{message} Install Agent Zero: http://agent-zero.ai", style="#9aa7b4")',
        f'return Text(f"{{message}} {BRAND} runs on Agent Zero — install it from http://agent-zero.ai", style="#9aa7b4")',
        1,
    ),
    (
        "src/agent_zero_cli/widgets/splash_view.py",
        '"Sign in to the Agent Zero instance below.",',
        f'"Sign in to the {BRAND} instance below.",',
        1,
    ),
    (
        "src/agent_zero_cli/widgets/splash_view.py",
        '"Use the same username and password you use in the Agent Zero Web UI."',
        f'"Use the same username and password you use in the {BRAND} Web UI."',
        1,
    ),
    (
        "src/agent_zero_cli/widgets/splash_view.py",
        'else "Login with the Agent Zero endpoint below."',
        f'else "Login with the {BRAND} endpoint below."',
        1,
    ),
    # --- computer_use_banner.py -------------------------------------------------
    (
        "src/agent_zero_cli/widgets/computer_use_banner.py",
        '"Computer use needs re-arming before Agent Zero can control your computer again."',
        f'"Computer use needs re-arming before {BRAND} can control your computer again."',
        1,
    ),
    (
        "src/agent_zero_cli/widgets/computer_use_banner.py",
        'return "Agent Zero CLI can control your computer in this session."',
        f'return "{BRAND} can control your computer in this session."',
        1,
    ),
    # --- self_update.py: update channel points at the fork ---------------------
    (
        "src/agent_zero_cli/self_update.py",
        'PACKAGE_NAME = "a0"',
        f'PACKAGE_NAME = "{CLI_NAME}"',
        1,
    ),
    (
        "src/agent_zero_cli/self_update.py",
        f'GITHUB_REPOSITORY = "{UPSTREAM_REPO}"',
        f'GITHUB_REPOSITORY = "{FORK_REPO}"',
        1,
    ),
    (
        "src/agent_zero_cli/self_update.py",
        '"User-Agent": "a0-cli-self-update",',
        f'"User-Agent": "{CLI_NAME}-cli-self-update",',
        1,
    ),
    (
        "src/agent_zero_cli/self_update.py",
        "a0 CLI update available",
        f"{CLI_NAME} CLI update available",
        None,
    ),
    (
        "src/agent_zero_cli/self_update.py",
        "run `a0 update`",
        f"run `{CLI_NAME} update`",
        1,
    ),
    (
        "src/agent_zero_cli/self_update.py",
        "Run `a0 update`",
        f"Run `{CLI_NAME} update`",
        1,
    ),
    (
        "src/agent_zero_cli/self_update.py",
        "uv is required for `a0 update`",
        f"uv is required for `{CLI_NAME} update`",
        None,
    ),
    (
        "src/agent_zero_cli/self_update.py",
        'detect_install_provenance(distribution_name: str = "a0")',
        f"detect_install_provenance(distribution_name: str = \"{CLI_NAME}\")",
        1,
    ),
    (
        "src/agent_zero_cli/self_update.py",
        "                    \"a0\",\n",
        f"                    \"{CLI_NAME}\",\n",
        1,
    ),
    (
        "src/agent_zero_cli/self_update.py",
        "Warning: running a0 update without dependency locks.",
        f"Warning: running {CLI_NAME} update without dependency locks.",
        None,
    ),
    (
        "src/agent_zero_cli/self_update.py",
        "Failed to resolve a locked a0 update target",
        f"Failed to resolve a locked {CLI_NAME} update target",
        1,
    ),
    (
        "src/agent_zero_cli/self_update.py",
        "a0-update-locks-",
        f"{CLI_NAME}-update-locks-",
        1,
    ),
    # --- install.sh --------------------------------------------------------------
    (
        "install.sh",
        "https://api.github.com/repos/agent0ai/a0-connector/releases/latest",
        f"https://api.github.com/repos/{FORK_REPO}/releases/latest",
        1,
    ),
    (
        "install.sh",
        "https://raw.githubusercontent.com/agent0ai/a0-connector/refs/tags",
        f"https://raw.githubusercontent.com/{FORK_REPO}/refs/tags",
        1,
    ),
    (
        "install.sh",
        'PACKAGE_SPEC="a0 @ https://github.com/agent0ai/a0-connector/archive/refs/tags/$RELEASE_TAG.zip"',
        f'PACKAGE_SPEC="{CLI_NAME} @ {FORK_URL}/archive/refs/tags/$RELEASE_TAG.zip"',
        1,
    ),
    (
        "install.sh",
        "--upgrade-package a0",
        f"--upgrade-package {CLI_NAME}",
        1,
    ),
    (
        "install.sh",
        "a0-cli-installer",
        f"{CLI_NAME}-cli-installer",
        None,
    ),
    (
        "install.sh",
        "latest a0 release",
        f"latest {CLI_NAME} release",
        None,
    ),
    (
        "install.sh",
        "installing a0 without dependency locks",
        f"installing {CLI_NAME} without dependency locks",
        1,
    ),
    (
        "install.sh",
        "a0-install-locks.",
        f"{CLI_NAME}-install-locks.",
        1,
    ),
    (
        "install.sh",
        "a0 is installed.",
        f"{CLI_NAME} is installed.",
        1,
    ),
    (
        "install.sh",
        "  a0\n",
        f"  {CLI_NAME}\n",
        1,
    ),
    (
        "install.sh",
        "If 'a0' is not available",
        f"If '{CLI_NAME}' is not available",
        1,
    ),
    # --- install.ps1 ---------------------------------------------------------------
    (
        "install.ps1",
        "https://api.github.com/repos/agent0ai/a0-connector/releases/latest",
        f"https://api.github.com/repos/{FORK_REPO}/releases/latest",
        1,
    ),
    (
        "install.ps1",
        "https://raw.githubusercontent.com/agent0ai/a0-connector/refs/tags",
        f"https://raw.githubusercontent.com/{FORK_REPO}/refs/tags",
        1,
    ),
    (
        "install.ps1",
        '"a0 @ https://github.com/agent0ai/a0-connector/archive/refs/tags/$escapedTag.zip"',
        f'"{CLI_NAME} @ {FORK_URL}/archive/refs/tags/$escapedTag.zip"',
        1,
    ),
    (
        "install.ps1",
        '"--upgrade-package", "a0"',
        f'"--upgrade-package", "{CLI_NAME}"',
        1,
    ),
    (
        "install.ps1",
        '"a0-cli-installer"',
        f'"{CLI_NAME}-cli-installer"',
        1,
    ),
    (
        "install.ps1",
        "latest a0 release",
        f"latest {CLI_NAME} release",
        1,
    ),
    (
        "install.ps1",
        'Join-Path ((& uv tool dir).Trim()) "a0"',
        f'Join-Path ((& uv tool dir).Trim()) "{CLI_NAME}"',
        1,
    ),
    (
        "install.ps1",
        "Installing a0 without dependency locks.",
        f"Installing {CLI_NAME} without dependency locks.",
        1,
    ),
    (
        "install.ps1",
        '"a0 is installed."',
        f'"{CLI_NAME} is installed."',
        1,
    ),
    (
        "install.ps1",
        'Write-Host "  a0"',
        f'Write-Host "  {CLI_NAME}"',
        1,
    ),
    (
        "install.ps1",
        "If 'a0' is not available",
        f"If '{CLI_NAME}' is not available",
        1,
    ),
    # --- tests: align branding assertions with the brand layer ---------------------
    (
        "tests/test_installers.py",
        '{ name = "agent0ai" }',
        f'{{ name = "{BRAND}" }}',
        1,
    ),
    (
        "tests/test_installers.py",
        "raw.githubusercontent.com/agent0ai/a0-connector/main/install.sh",
        f"raw.githubusercontent.com/{FORK_REPO}/main/install.sh",
        1,
    ),
    (
        "tests/test_installers.py",
        "raw.githubusercontent.com/agent0ai/a0-connector/main/install.ps1",
        f"raw.githubusercontent.com/{FORK_REPO}/main/install.ps1",
        1,
    ),
    (
        "tests/test_self_update.py",
        "a0 @ https://github.com/agent0ai/a0-connector/archive",
        f"{CLI_NAME} @ {FORK_URL}/archive",
        None,
    ),
    (
        "tests/test_self_update.py",
        '"https://raw.githubusercontent.com/agent0ai/a0-connector/"',
        f'"https://raw.githubusercontent.com/{FORK_REPO}/"',
        None,
    ),
    (
        "tests/test_app.py",
        "Agent Zero CLI can control your computer in this session.",
        f"{BRAND} can control your computer in this session.",
        None,
    ),
    (
        "tests/test_app.py",
        "before Agent Zero can control your computer again",
        f"before {BRAND} can control your computer again",
        1,
    ),
    (
        "tests/test_chat_input.py",
        "Agent Zero CLI composer",
        f"{BRAND} composer",
        1,
    ),
    # --- tests: update-channel branding ------------------------------------------
    (
        "tests/test_self_update.py",
        '"`a0 update`"',
        f'"`{CLI_NAME} update`"',
        None,
    ),
    (
        "tests/test_self_update.py",
        "Failed to resolve a locked a0 update target",
        f"Failed to resolve a locked {CLI_NAME} update target",
        None,
    ),
    (
        "tests/test_self_update.py",
        '"--upgrade-package",\n                "a0",',
        f'"--upgrade-package",\n                "{CLI_NAME}",',
        None,
    ),
    (
        "tests/test_app.py",
        "a0 CLI update available",
        f"{CLI_NAME} CLI update available",
        None,
    ),
    (
        "tests/test_app.py",
        "Run `a0 update`",
        f"Run `{CLI_NAME} update`",
        None,
    ),
    # --- tests: installer branding -----------------------------------------------
    (
        "tests/test_installers.py",
        "'--upgrade-package a0' in installer",
        f"'--upgrade-package {CLI_NAME}' in installer",
        1,
    ),
    (
        "tests/test_installers.py",
        '"--managed-python", "--upgrade-package", "a0")',
        f'"--managed-python", "--upgrade-package", "{CLI_NAME}")',
        1,
    ),
    (
        "tests/test_installers.py",
        "Close all A0 CLI terminal windows",
        f"Close all TIIAGO CLI terminal windows",
        1,
    ),
    (
        "tests/test_installers.py",
        "Computer-use backends are embedded in the `a0` wheel",
        f"Computer-use backends are embedded in the `{CLI_NAME}` wheel",
        1,
    ),
    (
        "tests/test_installers.py",
        '"`a0 update`" in readme',
        f'"`{CLI_NAME} update`" in readme',
        1,
    ),
    (
        "tests/test_splash_view.py",
        "Install Agent Zero: http://agent-zero.ai",
        f"{BRAND} runs on Agent Zero — install it from http://agent-zero.ai",
        1,
    ),
    (
        "tests/test_entrypoint.py",
        "usage: a0",
        "usage: tiiago",
        None,
    ),
    # --- install.ps1: A0 CLI process-guard messages --------------------------------
    (
        "install.ps1",
        "A0 CLI is still running from",
        "TIIAGO CLI is still running from",
        1,
    ),
    (
        "install.ps1",
        "Close all A0 CLI terminal windows",
        "Close all TIIAGO CLI terminal windows",
        1,
    ),
]

AGENTS_BRAND_SECTION = """
## TI•IA•GO Brand Layer

- This fork applies a mechanical brand layer on top of upstream: package/CLI name `tiiago` (alias `a0` kept), `TI•IA•GO` titles, URLs pointing at `fernandobayit/tiiago-connector`.
- The layer lives in `devtools/apply_tiiago_brand.py` and is re-applied by `.github/workflows/sync-upstream.yml` after every upstream merge; run it manually with `python3 devtools/apply_tiiago_brand.py`.
- Do NOT rename shared protocol identifiers: plugin `_a0_connector`, protocol `a0-connector.v1`, `/api/plugins/_a0_connector/v1/` routes, `A0_*`/`AGENT_ZERO_*` env vars, `constraints/a0-*.txt` paths, or the `agent_zero_cli` package. They are the contract with Agent Zero Core.
- Fork-only additions: `DEFAULT_HOST` compiled to `https://a0.bayit.me` (client.py), `TIIAGO_DEFAULT_HOST` (host fallback override), and `TIIAGO_AUTOCONNECT` (auto-connect on startup, default ON; set `=0` to disable). Auto-connect lands on the login panel when no saved session exists.
"""

README_UPSTREAM_SECTION = """
---

## Upstream

TI•IA•GO Connector is a branded fork of the upstream [`agent0ai/a0-connector`](https://github.com/agent0ai/a0-connector) project (MIT License). It tracks upstream releases automatically via a scheduled GitHub Action and re-applies the TI•IA•GO brand layer on top. The wire protocol shared with Agent Zero Core is unchanged.
"""

ENTRYPOINT_BRAND_TESTS = '''

def test_brand_parser_prog_is_tiiago() -> None:
    parser = __main__._build_parser()

    assert parser.prog == "tiiago"


def test_brand_tiiago_default_host_fallback(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    from agent_zero_cli import config as config_module

    monkeypatch.setenv("TIIAGO_DEFAULT_HOST", "http://tiiago.example:5080")
    monkeypatch.delenv("AGENT_ZERO_HOST", raising=False)
    monkeypatch.setattr(config_module, "_ENV_FILE", tmp_path / "missing.env")

    config = config_module.load_config()

    assert config.instance_url == "http://tiiago.example:5080"


def test_brand_agent_zero_host_wins_over_tiiago_default(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    from agent_zero_cli import config as config_module

    monkeypatch.setenv("AGENT_ZERO_HOST", "http://primary.example:5080")
    monkeypatch.setenv("TIIAGO_DEFAULT_HOST", "http://fallback.example:5080")
    monkeypatch.setattr(config_module, "_ENV_FILE", tmp_path / "missing.env")

    config = config_module.load_config()

    assert config.instance_url == "http://primary.example:5080"


def test_brand_autoconnect_flag(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    from agent_zero_cli import config as config_module

    monkeypatch.setattr(config_module, "_ENV_FILE", tmp_path / "missing.env")

    monkeypatch.setenv("TIIAGO_AUTOCONNECT", "1")
    assert config_module.autoconnect_default_enabled() is True

    monkeypatch.setenv("TIIAGO_AUTOCONNECT", "0")
    assert config_module.autoconnect_default_enabled() is False

    monkeypatch.delenv("TIIAGO_AUTOCONNECT")
    assert config_module.autoconnect_default_enabled() is True
'''

README_WORD_A0_RE = re.compile(r"(?<![A-Za-z0-9_/.-])a0(?![A-Za-z0-9_-])")
README_UPSTREAM_MARKER = "## Upstream"


def _apply_text(path: Path, old: str, new: str, count: int | None) -> str:
    """Return 'applied', 'already', or 'missing' for one textual patch."""
    content = path.read_text(encoding="utf-8")
    if new in content:
        # Append-style patches leave ``old`` in place after applying, so the
        # presence of ``new`` is the authoritative already-applied signal.
        return "already"
    if old not in content:
        if count == 0:
            # Repair entry for intermediate fork states that may never have
            # existed on this tree (e.g. fresh upstream checkout): skip silently.
            return "skipped"
        return "missing"
    if count is None:
        content = content.replace(old, new)
    else:
        # count == 0 marks a repair entry that may not exist on every tree;
        # when its target text IS present it must still be replaced once.
        content = content.replace(old, new, count or 1)
    path.write_text(content, encoding="utf-8", newline="")
    return "applied"


def _append_once(path: Path, section: str, marker: str) -> str:
    content = path.read_text(encoding="utf-8")
    if marker in content:
        return "already"
    if not content.endswith("\n"):
        content += "\n"
    content += section
    path.write_text(content, encoding="utf-8", newline="")
    return "applied"


def _rebrand_readme(path: Path) -> str:
    """Rebrand README head (everything before the Upstream section); tail untouched."""
    content = path.read_text(encoding="utf-8")
    if README_UPSTREAM_MARKER in content:
        head, tail = content.split(README_UPSTREAM_MARKER, 1)
        tail = README_UPSTREAM_MARKER + tail
    else:
        head, tail = content, ""

    original_head = head
    head = head.replace(f"# {UPSTREAM_REPO}", f"# {BRAND} Connector")
    head = head.replace("# a0-connector", f"# {BRAND} Connector")
    head = head.replace(UPSTREAM_REPO, FORK_REPO)
    head = head.replace("Agent Zero CLI", f"{BRAND} CLI")
    head = README_WORD_A0_RE.sub(CLI_NAME, head)

    if head != original_head:
        path.write_text(head + tail, encoding="utf-8", newline="")
        return "applied"
    if tail:
        return "already"
    return "missing"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--check",
        action="store_true",
        help="Report pending changes without writing; exit 1 when changes are pending.",
    )
    args = parser.parse_args()

    applied: list[str] = []
    already: list[str] = []
    missing: list[str] = []

    for rel_path, old, new, count in PATCHES:
        path = REPO_ROOT / rel_path
        if not path.exists():
            missing.append(f"{rel_path} (file absent)")
            continue
        result = _apply_text(path, old, new, count)
        label = f"{rel_path}: {old.splitlines()[0][:60]!r}"
        if result == "applied":
            applied.append(label)
        elif result == "already":
            already.append(label)
        else:
            missing.append(label)

    readme = REPO_ROOT / "README.md"
    readme_result = _rebrand_readme(readme)
    if readme_result == "applied":
        applied.append("README.md (brand rewrite)")
    elif readme_result == "already":
        already.append("README.md (brand rewrite)")
    else:
        missing.append("README.md (brand rewrite)")

    agents_section = _append_once(
        REPO_ROOT / "AGENTS.md",
        AGENTS_BRAND_SECTION,
        "## TI•IA•GO Brand Layer",
    )
    if agents_section == "applied":
        applied.append("AGENTS.md (brand section)")
    elif agents_section == "already":
        already.append("AGENTS.md (brand section)")
    else:
        missing.append("AGENTS.md (brand section)")

    entrypoint_tests = REPO_ROOT / "tests/test_entrypoint.py"
    tests_section = _append_once(
        entrypoint_tests,
        ENTRYPOINT_BRAND_TESTS,
        "test_brand_parser_prog_is_tiiago",
    )
    if tests_section == "applied":
        applied.append("tests/test_entrypoint.py (brand tests)")
    elif tests_section == "already":
        already.append("tests/test_entrypoint.py (brand tests)")
    else:
        missing.append("tests/test_entrypoint.py (brand tests)")

    readme_upstream = _append_once(readme, README_UPSTREAM_SECTION, README_UPSTREAM_MARKER)
    if readme_upstream == "applied":
        applied.append("README.md (upstream section)")
    elif readme_upstream == "already":
        already.append("README.md (upstream section)")
    else:
        missing.append("README.md (upstream section)")

    print(f"applied: {len(applied)}")
    for line in applied:
        print(f"  + {line}")
    print(f"already: {len(already)}")
    for line in already:
        print(f"  = {line}")
    if missing:
        print(f"MISSING (upstream drift — review manually): {len(missing)}")
        for line in missing:
            print(f"  ! {line}")

    if args.check and applied:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())