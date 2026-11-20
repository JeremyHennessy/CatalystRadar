"""Optional local POSIX storage for the pure ABSTAIN research journal.

No application integration, provider access or authenticated time. Intended
only for cooperating processes on one local filesystem supporting flock,
atomic same-directory rename and file/directory fsync. The user supplies a
dedicated, already durably created 0700 directory outside the public/app tree.
Do not move, delete, rewrite or share that directory or its lock inode while
in use. No protection against a hostile same-UID writer, rollback of the
entire directory, or storage hardware/filesystem that misreports durability.
Keep an independently protected expected tip if rollback must be detected.
"""
from contextlib import contextmanager
import fcntl
import os
import re
import secrets
import stat

import research_abstention_journal as journal

_LOCK = "writer.lock"
_STATE = "abstentions.ndjson"
_LOCAL_ONLY_FLAGS = os.O_NOFOLLOW | os.O_NONBLOCK | os.O_CLOEXEC
_MAX_BYTES = 2_000_000  # Pure replay's bound; no additional serialized envelope.


class JournalBusy(RuntimeError):
    """Another local operation holds the lock; retry with the same command/tip."""


class CommitUncertain(RuntimeError):
    """Replacement may be visible; reopen and retry the exact command and tip."""


def _check_file(fd):
    s = os.fstat(fd)
    if (not stat.S_ISREG(s.st_mode) or stat.S_IMODE(s.st_mode) != 0o600
            or s.st_uid != os.geteuid() or s.st_nlink != 1):
        raise ValueError("journal requires a regular, owner-only, unlinked-from-other-paths file")
    return s


@contextmanager
def _locked(directory, *, create=False):
    dfd = os.open(directory, os.O_DIRECTORY | os.O_RDONLY | _LOCAL_ONLY_FLAGS)
    try:
        s = os.fstat(dfd)
        if stat.S_IMODE(s.st_mode) != 0o700 or s.st_uid != os.geteuid():
            raise ValueError("journal requires a dedicated 0700 owner directory")
        if create:
            # Do not install a new lock inode over an extant transcript. Other
            # cooperating initializers are still serialized by exclusive creation.
            _require_missing_state(dfd)
        flags = os.O_RDWR | _LOCAL_ONLY_FLAGS | (os.O_CREAT | os.O_EXCL if create else 0)
        lock = os.open(_LOCK, flags, 0o600, dir_fd=dfd)
        try:
            _check_file(lock)
            try:
                fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
            except BlockingIOError:
                raise JournalBusy("journal lock held; retry the exact request") from None
            yield dfd
        finally:
            os.close(lock)
    finally:
        os.close(dfd)


def _load(dfd):
    fd = os.open(_STATE, os.O_RDONLY | _LOCAL_ONLY_FLAGS, dir_fd=dfd)
    with os.fdopen(fd, "rb") as file:
        if _check_file(file.fileno()).st_size > _MAX_BYTES:
            raise ValueError("persisted journal exceeds size limit")
        raw = file.read(_MAX_BYTES + 1)
    if len(raw) > _MAX_BYTES or (raw and not raw.endswith(b"\n")):
        raise ValueError("persisted journal length or framing mismatch")
    if raw.count(b"\n") > journal.MAX_RECORDS:
        raise ValueError("persisted journal record count exceeds limit")
    rows = [part + b"\n" for part in raw.split(b"\n")[:-1]]
    # Reuse pure validation; its return values never represent authenticated timing.
    return rows, journal.replay(rows)


def _sync_visible(dfd):
    try:
        os.fsync(dfd)
    except OSError as error:
        raise CommitUncertain("journal visibility observed, directory sync not confirmed") from error


def _commit(dfd, rows):
    name = ".abstentions-" + secrets.token_hex(16) + ".tmp"
    fd = os.open(name, os.O_WRONLY | os.O_CREAT | os.O_EXCL | _LOCAL_ONLY_FLAGS,
                 0o600, dir_fd=dfd)
    try:
        with os.fdopen(fd, "wb") as file:
            _check_file(file.fileno())
            for row in rows:
                file.write(row)
            file.flush()
            os.fsync(file.fileno())
        try:
            os.replace(name, _STATE, src_dir_fd=dfd, dst_dir_fd=dfd)
        except OSError as error:
            raise CommitUncertain("journal replacement not confirmed; reopen and retry") from error
        _sync_visible(dfd)
    finally:
        # A real process crash before replacement may leave an inert temp file.
        # Our loader never restores, scans, or interprets it.
        try:
            os.unlink(name, dir_fd=dfd)
        except FileNotFoundError:
            pass


def _require_missing_state(dfd):
    try:
        os.stat(_STATE, dir_fd=dfd, follow_symlinks=False)
    except FileNotFoundError:
        return
    raise FileExistsError("journal already exists")


def initialize(directory):
    """Create the empty transcript, never reset an existing one.

    Call only for a new dedicated journal directory, not as rollback recovery.
    A preexisting lock is an initialization marker, even if the state is
    missing. After a lost initial acknowledgment use read(); if unreadable,
    stop and designate a new directory separately rather than resetting.
    """
    with _locked(directory, create=True) as dfd:
        _require_missing_state(dfd)
        _commit(dfd, [])


def read(directory):
    """Replay visible bytes under the writer lock, without modifying storage."""
    with _locked(directory) as dfd:
        return _load(dfd)[1]


def append(directory, *, expected_tip, **source_inputs):
    """Revalidate sources, append via pure CAS, and return the saved record.

    Preserve the same command and expected tip after an uncertain acknowledgment.
    A same-command retry returns the existing record before CAS, but still syncs
    the directory before acknowledging it. Different commands need exact tip.
    Host-local time is recorded by the pure journal and remains unauthenticated.
    """
    if type(expected_tip) is not str or not re.fullmatch(r"[a-f0-9]{64}", expected_tip):
        raise ValueError("expected tip must be a lowercase SHA-256")
    if "clock" in source_inputs:
        raise ValueError("the persistent adapter does not accept a caller clock")
    with _locked(directory) as dfd:
        prior, _ = _load(dfd)
        out, result = journal.append(prior, expected_tip=expected_tip, **source_inputs)
        if len(out) == len(prior):
            _sync_visible(dfd)  # Retry can follow a rename with a lost directory sync.
        else:
            _commit(dfd, out)
        return result
