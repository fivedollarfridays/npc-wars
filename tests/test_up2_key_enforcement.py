"""UP-2: submission key enforcement + delegated identity (service key + ref).

Covers:
  * keyless submissions rejected unless the exact dev opt-in is set
  * unknown API keys stay 401
  * delegated identity via NPCWARS_SERVICE_API_KEY + X-Player-Ref
"""

from __future__ import annotations

import uuid
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from server.app import app
from server.db import create_api_key, create_player, get_bot
from server.routes.submit import clear_rate_limits

SERVICE_KEY = "svc_up2_test_key"
VALID_REF = "ref_ABCdef123456"

VALID_SOURCE = (
    'BOT_NAME = "TestUP2"\n'
    'BOT_EMOJI = "U"\n'
    "def decide(state):\n"
    '    return "north"\n'
)


@pytest.fixture(autouse=True)
def _clear() -> None:
    clear_rate_limits()


@pytest.fixture()
def client() -> TestClient:
    return TestClient(app)


@pytest.fixture()
def enforced(monkeypatch: pytest.MonkeyPatch) -> None:
    """Production-shaped env: no keyless opt-in, service key provisioned."""
    monkeypatch.delenv("NPCWARS_ALLOW_KEYLESS", raising=False)
    monkeypatch.setenv("NPCWARS_SERVICE_API_KEY", SERVICE_KEY)


@pytest.fixture()
def player_key() -> str:
    """A real, non-service player API key."""
    player_id = uuid.uuid4().hex
    create_player(app.state.db, player_id, f"player_{player_id[:8]}")
    return create_api_key(app.state.db, player_id)


def _player_of(bot_id: int) -> str:
    """Return the player id that owns *bot_id* (identity binding probe)."""
    bot = get_bot(app.state.db, bot_id)
    assert bot is not None
    return bot["player_id"]


def _submit(client: TestClient, **headers: str):
    """POST a valid bot source with the given headers."""
    return client.post(
        "/api/submit-bot", json={"source": VALID_SOURCE}, headers=headers or None
    )


# ── 1. Keyless submissions ───────────────────────────────────────────


class TestKeylessRejected:
    """No X-API-Key header must be rejected unless opted in exactly."""

    @pytest.mark.parametrize("value", [None, "", " ", "true", "yes", "0", "11", " 1"])
    def test_keyless_rejected_without_exact_optin(
        self, client: TestClient, monkeypatch: pytest.MonkeyPatch, value: str | None
    ) -> None:
        if value is None:
            monkeypatch.delenv("NPCWARS_ALLOW_KEYLESS", raising=False)
        else:
            monkeypatch.setenv("NPCWARS_ALLOW_KEYLESS", value)
        resp = _submit(client)
        assert resp.status_code == 401

    def test_keyless_allowed_with_exact_optin(
        self, client: TestClient, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setenv("NPCWARS_ALLOW_KEYLESS", "1")
        resp = _submit(client)
        assert resp.status_code == 202
        assert "api_key" in resp.json()


# ── 2. Unknown keys ──────────────────────────────────────────────────


class TestUnknownKey:
    """Unknown API keys stay 401 with enforcement on (pinning test)."""

    def test_unknown_key_rejected(self, client: TestClient, enforced: None) -> None:
        resp = _submit(client, **{"X-API-Key": "definitely-not-a-real-key"})
        assert resp.status_code == 401


# ── 3. Delegated identity (service key + X-Player-Ref) ───────────────


class TestDelegatedIdentity:
    """The PSC relay authenticates once and acts on behalf of a player ref."""

    def test_service_key_with_ref_accepted(
        self, client: TestClient, enforced: None
    ) -> None:
        resp = _submit(
            client, **{"X-API-Key": SERVICE_KEY, "X-Player-Ref": VALID_REF}
        )
        assert resp.status_code == 202
        # The relay never receives a per-player credential.
        assert "api_key" not in resp.json()

    def test_same_ref_is_stable_across_submissions(
        self, client: TestClient, enforced: None
    ) -> None:
        headers = {"X-API-Key": SERVICE_KEY, "X-Player-Ref": "ref_stable_0001"}
        first = _submit(client, **headers)
        clear_rate_limits()
        second = _submit(client, **headers)
        assert first.status_code == 202
        assert second.status_code == 202
        assert _player_of(first.json()["bot_id"]) == _player_of(
            second.json()["bot_id"]
        )

    def test_distinct_refs_are_distinct_players(
        self, client: TestClient, enforced: None
    ) -> None:
        base = {"X-API-Key": SERVICE_KEY}
        one = _submit(client, **base, **{"X-Player-Ref": "ref_alpha_00001"})
        clear_rate_limits()
        two = _submit(client, **base, **{"X-Player-Ref": "ref_bravo_00001"})
        assert one.status_code == 202
        assert two.status_code == 202
        assert _player_of(one.json()["bot_id"]) != _player_of(two.json()["bot_id"])


# ── 4. Delegation rejection matrix ───────────────────────────────────


class TestDelegationRejected:
    """Delegation is loud: no silent ignores, no unattributed service calls."""

    def test_service_key_without_ref_is_400(
        self, client: TestClient, enforced: None
    ) -> None:
        resp = _submit(client, **{"X-API-Key": SERVICE_KEY})
        assert resp.status_code == 400

    def test_player_key_with_ref_is_403(
        self, client: TestClient, enforced: None, player_key: str
    ) -> None:
        resp = _submit(
            client, **{"X-API-Key": player_key, "X-Player-Ref": VALID_REF}
        )
        assert resp.status_code == 403

    def test_keyless_with_ref_is_403(
        self, client: TestClient, enforced: None
    ) -> None:
        resp = _submit(client, **{"X-Player-Ref": VALID_REF})
        assert resp.status_code == 403

    def test_unknown_key_with_ref_is_403(
        self, client: TestClient, enforced: None
    ) -> None:
        resp = _submit(
            client, **{"X-API-Key": "nope-not-a-key", "X-Player-Ref": VALID_REF}
        )
        assert resp.status_code == 403

    def test_ref_is_403_when_service_key_unset(
        self, client: TestClient, monkeypatch: pytest.MonkeyPatch, player_key: str
    ) -> None:
        monkeypatch.delenv("NPCWARS_SERVICE_API_KEY", raising=False)
        resp = _submit(
            client, **{"X-API-Key": player_key, "X-Player-Ref": VALID_REF}
        )
        assert resp.status_code == 403

    def test_service_key_value_is_not_a_bearer_when_unset(
        self, client: TestClient, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """With the env unset the service key string is just an unknown key."""
        monkeypatch.delenv("NPCWARS_SERVICE_API_KEY", raising=False)
        monkeypatch.delenv("NPCWARS_ALLOW_KEYLESS", raising=False)
        resp = _submit(client, **{"X-API-Key": SERVICE_KEY})
        assert resp.status_code == 401


# ── 5. Ref shape validation ──────────────────────────────────────────


BAD_REFS = [
    "",  # empty
    "short7",  # under 8 chars
    "ref/../../etc/passwd",  # path characters
    "ref with space",  # whitespace
    "ref.with.dots",  # disallowed punctuation
    "ref%2Fencoded",  # percent encoding
    "x" * 129,  # over 128 chars
]


class TestRefShape:
    """Only opaque [A-Za-z0-9_-]{8,128} tokens are accepted."""

    @pytest.mark.parametrize("bad", BAD_REFS)
    def test_malformed_ref_with_service_key_is_400(
        self, client: TestClient, enforced: None, bad: str
    ) -> None:
        resp = _submit(client, **{"X-API-Key": SERVICE_KEY, "X-Player-Ref": bad})
        assert resp.status_code == 400

    @pytest.mark.parametrize("bad", BAD_REFS)
    def test_malformed_ref_without_service_key_is_403(
        self, client: TestClient, enforced: None, player_key: str, bad: str
    ) -> None:
        resp = _submit(client, **{"X-API-Key": player_key, "X-Player-Ref": bad})
        assert resp.status_code == 403

    @pytest.mark.parametrize(
        "good", ["12345678", "A" * 128, "ref_with-dashes_and_UNDERSCORES"]
    )
    def test_wellformed_refs_accepted(
        self, client: TestClient, enforced: None, good: str
    ) -> None:
        resp = _submit(client, **{"X-API-Key": SERVICE_KEY, "X-Player-Ref": good})
        assert resp.status_code == 202


# ── 6. Ref opacity (no PII leakage) ──────────────────────────────────


class TestRefOpacity:
    """The ref is an opaque HMAC token — it must not surface anywhere."""

    def test_ref_not_in_response_or_player_name(
        self, client: TestClient, enforced: None
    ) -> None:
        ref = "ref_secret_marker_0001"
        resp = _submit(client, **{"X-API-Key": SERVICE_KEY, "X-Player-Ref": ref})
        assert resp.status_code == 202
        assert ref not in resp.text

        from server.db import get_player

        player = get_player(app.state.db, _player_of(resp.json()["bot_id"]))
        assert player is not None
        assert ref not in str(player)

    def test_ref_not_stored_in_plaintext(
        self, client: TestClient, enforced: None
    ) -> None:
        ref = "ref_plaintext_probe_01"
        assert (
            _submit(
                client, **{"X-API-Key": SERVICE_KEY, "X-Player-Ref": ref}
            ).status_code
            == 202
        )
        rows = app.state.db.execute("SELECT * FROM player_refs").fetchall()
        assert rows, "positive control: the ref binding row must exist"
        assert all(ref not in str(tuple(row)) for row in rows)

    def test_ref_not_logged_at_info(
        self,
        client: TestClient,
        enforced: None,
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        ref = "ref_log_probe_000001"
        with caplog.at_level("INFO"):
            _submit(client, **{"X-API-Key": SERVICE_KEY, "X-Player-Ref": ref})
            clear_rate_limits()
            # Rejection paths log warnings — they must stay ref-free too.
            _submit(client, **{"X-API-Key": "bogus", "X-Player-Ref": ref})
            clear_rate_limits()
            _submit(client, **{"X-API-Key": SERVICE_KEY, "X-Player-Ref": "bad ref"})
        assert ref not in caplog.text


# ── 7. Rate limiting is per delegated player, not per relay ──────────


class TestDelegatedRateLimit:
    """One shared service key must not rate-limit every PSC player at once."""

    def test_distinct_refs_are_limited_independently(
        self, client: TestClient, enforced: None
    ) -> None:
        base = {"X-API-Key": SERVICE_KEY}
        one = _submit(client, **base, **{"X-Player-Ref": "ref_rl_alpha_0001"})
        two = _submit(client, **base, **{"X-Player-Ref": "ref_rl_bravo_0001"})
        assert one.status_code == 202
        assert two.status_code == 202

    def test_same_ref_still_rate_limited(
        self, client: TestClient, enforced: None
    ) -> None:
        headers = {"X-API-Key": SERVICE_KEY, "X-Player-Ref": "ref_rl_same_00001"}
        assert _submit(client, **headers).status_code == 202
        assert _submit(client, **headers).status_code == 429


# ── 8. Strict-auth routes never silently ignore a ref ────────────────


class TestStrictAuthRef:
    """require_api_key routes must reject delegation too, not drop it."""

    def test_player_key_with_ref_rejected(
        self, client: TestClient, enforced: None, player_key: str
    ) -> None:
        resp = client.get(
            "/api/bots",
            headers={"X-API-Key": player_key, "X-Player-Ref": VALID_REF},
        )
        assert resp.status_code == 403

    def test_service_key_with_ref_rejected(
        self, client: TestClient, enforced: None
    ) -> None:
        """Delegation is not wired into strict-auth routes — say so loudly."""
        resp = client.get(
            "/api/bots",
            headers={"X-API-Key": SERVICE_KEY, "X-Player-Ref": VALID_REF},
        )
        assert resp.status_code == 403

    def test_player_key_without_ref_still_works(
        self, client: TestClient, enforced: None, player_key: str
    ) -> None:
        resp = client.get("/api/bots", headers={"X-API-Key": player_key})
        assert resp.status_code == 200


# ── 9. Built-in editor surfaces the new rejection ────────────────────


def test_editor_handles_auth_rejection() -> None:
    """The bundled editor must not dead-end on the new 401/403 responses."""
    editor = Path(__file__).parent.parent / "server" / "static" / "editor.html"
    content = editor.read_text(encoding="utf-8")
    assert "result.status === 401" in content
    assert "result.status === 403" in content
