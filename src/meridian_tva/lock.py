"""Verrou d'exécution : une seule campagne ou un seul chargement à la fois.

Deux campagnes lancées en parallèle (double-clic, relance impatiente, lanceur qui exécute deux fois) doubleraient les
appels à VIES, ce que sa limite globale par État membre sanctionne immédiatement. Le verrou est un fichier ouvert en
exclusif (msvcrt sous Windows, fcntl ailleurs), libéré automatiquement à la fin du processus, même après un Ctrl+C.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path


class AlreadyRunning(Exception):
    pass


class RunLock:
    def __init__(self, path: Path):
        self.path = path
        self._fh = None

    def __enter__(self) -> "RunLock":
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._fh = open(self.path, "a+")
        try:
            if sys.platform == "win32":
                import msvcrt

                self._fh.seek(0)
                msvcrt.locking(self._fh.fileno(), msvcrt.LK_NBLCK, 1)
            else:
                import fcntl

                fcntl.flock(self._fh.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        except OSError as exc:
            self._fh.close()
            self._fh = None
            raise AlreadyRunning(f"une autre exécution est en cours (verrou {self.path})") from exc
        self._fh.seek(0)
        self._fh.truncate()
        self._fh.write(str(os.getpid()))
        self._fh.flush()
        return self

    def __exit__(self, *exc) -> None:
        if self._fh is None:
            return
        try:
            if sys.platform == "win32":
                import msvcrt

                self._fh.seek(0)
                msvcrt.locking(self._fh.fileno(), msvcrt.LK_UNLCK, 1)
            else:
                import fcntl

                fcntl.flock(self._fh.fileno(), fcntl.LOCK_UN)
        finally:
            self._fh.close()
            self._fh = None
