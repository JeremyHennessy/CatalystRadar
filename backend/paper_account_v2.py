"""Private, local-only immutable genesis for the isolated USD 500 paper V2.

Caller supplies an already durable dedicated mode-0700 directory outside any
repo or hosted path. Requires a cooperating local POSIX filesystem with
ordinary file/dir fsync and atomic hard-link publication. No order, activation,
brokerage, prices, position changes, legacy ledger, UI, or network access.

The opening clock is the local system clock, not authenticated external time.
The payload hash detects accidental corruption; it cannot protect against a
writer replacing both payload and hash, or deleting both opening files/the whole directory. On
lost or corrupt state, stop; never invoke the initializer as recovery for an
account that was already opened.
"""
from contextlib import contextmanager
from datetime import datetime, timezone
import hashlib
import json
import os
import re
import secrets
import stat

_FILENAME = "genesis-v2.json"
_SEAL = "opening-v2.seal"
_MAX_BYTES = 2048
_OPEN = {
    "version": 2,
    "account": "PAPER_V2",
    "account_state": "OPEN",
    "readiness": "AWAITING_MARKET_DATA",
    "opening_cash_cents": 50000,
    "cash_cents": 50000,
    "currency": "USD",
    "clock_basis": "LOCAL_SYSTEM_CLOCK_NOT_AUTHENTICATED",
    "order_count": 0,
    "fill_count": 0,
    "position_count": 0,
    "realized_pnl_cents": None,
    "execution_enabled": False,
    "brokerage_connected": False,
}
_FILE_FLAGS = os.O_NOFOLLOW | os.O_NONBLOCK | os.O_CLOEXEC


class OpeningUncertain(RuntimeError):
    """State may be visible; use the exact same designated directory to check."""


@contextmanager
def _directory(directory):
    fd = os.open(directory, os.O_DIRECTORY | os.O_RDONLY | _FILE_FLAGS)
    try:
        s = os.fstat(fd)
        if s.st_uid != os.geteuid() or stat.S_IMODE(s.st_mode) != 0o700:
            raise ValueError("paper V2 requires an owner-only mode-0700 directory")
        yield fd
    finally:
        os.close(fd)


def _encoded(value):
    return (json.dumps(value, sort_keys=True, separators=(",", ":"),
                       ensure_ascii=True, allow_nan=False) + "\n").encode("utf-8")


def _envelope(status):
    return _encoded({"status": status, "status_sha256": hashlib.sha256(_encoded(status)).hexdigest()})


def _validate(raw):
    try:
        data = json.loads(raw)
        status = data["status"]
        opened = status["opened_utc"]
        if (not re.fullmatch(r"[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}\.[0-9]{6}Z", opened)
                or _encoded(status) != _encoded(_OPEN | {"opened_utc": opened})):
            raise ValueError("paper V2 opening policy mismatch")
        datetime.fromisoformat(opened.replace("Z", "+00:00"))
        # Full canonical byte comparison rejects duplicate/extra keys, wrong
        # types, trailing bytes and digest mismatch, not just a parsed subset.
        if raw != _envelope(status):
            raise ValueError("paper V2 genesis integrity mismatch")
    except (ValueError, AttributeError, RecursionError, UnicodeError, KeyError, TypeError) as error:
        raise ValueError("invalid paper V2 genesis") from error
    return status


def _read(dfd, name):
    fd = os.open(name, os.O_RDONLY | _FILE_FLAGS, dir_fd=dfd)
    with os.fdopen(fd, "rb") as file:
        s = os.fstat(file.fileno())
        if (not stat.S_ISREG(s.st_mode) or s.st_uid != os.geteuid()
                or stat.S_IMODE(s.st_mode) != 0o600 or not 1 <= s.st_size <= _MAX_BYTES):
            raise ValueError("paper V2 requires a bounded owner-only regular file")
        raw = file.read(_MAX_BYTES + 1)
    if len(raw) > _MAX_BYTES:
        raise ValueError("paper V2 genesis exceeds size bound")
    return _validate(raw), (s.st_dev, s.st_ino)


def _exists(dfd, name):
    try:
        os.stat(name, dir_fd=dfd, follow_symlinks=False)
    except FileNotFoundError:
        return False
    return True


def _sealed_status(dfd):
    try:
        status, genesis_inode = _read(dfd, _FILENAME)
    except FileNotFoundError:
        if not _exists(dfd, _SEAL):
            raise
        try:
            status, genesis_inode = _read(dfd, _FILENAME)
        except FileNotFoundError as error:
            raise ValueError("paper V2 seal remains but genesis is missing; do not reopen") from error
    try:
        sealed, seal_inode = _read(dfd, _SEAL)
    except FileNotFoundError as error:
        raise ValueError("paper V2 opening seal is missing; not open for status") from error
    if genesis_inode != seal_inode or status != sealed:
        raise ValueError("paper V2 opening seal does not match genesis")
    return status


def read_status(directory):
    """Read existing sealed private status; never create or repair state."""
    with _directory(directory) as dfd:
        return _sealed_status(dfd)


def _sync(dfd):
    try:
        os.fsync(dfd)
    except OSError as error:
        raise OpeningUncertain("paper V2 visible; opening durability not confirmed") from error


def _finish_open(dfd):
    status, _ = _read(dfd, _FILENAME)
    if not _exists(dfd, _SEAL):
        # Make genesis durable first; then publish the independent namespace
        # seal as a second reference to these exact immutable bytes.
        _sync(dfd)
        try:
            os.link(_FILENAME, _SEAL, src_dir_fd=dfd, dst_dir_fd=dfd, follow_symlinks=False)
        except FileExistsError:
            pass  # Other initializers can only link the same winning genesis.
        except OSError as error:
            raise OpeningUncertain("paper V2 opening seal not confirmed") from error
    if _sealed_status(dfd) != status:
        raise ValueError("paper V2 genesis changed during opening")
    _sync(dfd)
    return status


def open_account(directory):
    """Explicit one-time genesis or idempotent acknowledgment of the same file.

    No-clobber publication prevents replacing existing genesis or seal. If a
    process dies before genesis publication, nothing is open. If it dies
    between genesis and seal, a retry can finish that same genesis, never
    backdate or reset it. If only the durable seal remains, stop. Any orphaned
    owner-only temp names after process death are ignored, not used for restore.
    """
    with _directory(directory) as dfd:
        if _exists(dfd, _FILENAME):
            return _finish_open(dfd)
        if _exists(dfd, _SEAL):
            if _exists(dfd, _FILENAME):
                return _finish_open(dfd)
            raise ValueError("paper V2 seal remains but genesis is missing; do not reopen")

        opened = datetime.now(timezone.utc).isoformat(timespec="microseconds").replace("+00:00", "Z")
        raw = _envelope(_OPEN | {"opened_utc": opened})
        name = ".paper-v2-" + secrets.token_hex(16) + ".tmp"
        fd = os.open(name, os.O_WRONLY | os.O_CREAT | os.O_EXCL | _FILE_FLAGS,
                     0o600, dir_fd=dfd)
        try:
            with os.fdopen(fd, "wb") as file:
                s = os.fstat(file.fileno())
                if s.st_uid != os.geteuid() or stat.S_IMODE(s.st_mode) != 0o600:
                    raise ValueError("paper V2 temporary file mode mismatch")
                file.write(raw)
                file.flush()
                os.fsync(file.fileno())
            try:
                os.link(name, _FILENAME, src_dir_fd=dfd, dst_dir_fd=dfd, follow_symlinks=False)
            except FileExistsError:
                pass  # Another initializer won; validate that file, not ours.
            except OSError as error:
                raise OpeningUncertain("paper V2 publication not confirmed") from error
        finally:
            os.unlink(name, dir_fd=dfd)

        return _finish_open(dfd)
