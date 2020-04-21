from dataclasses import dataclass
from typing import Optional

from aqt import AnkiQt
from aqt.sync import SyncManager


@dataclass
class State:
    state: str
    did: int
    mid: int


def onSyncForce(self, action: str): #new method
    self.unloadCollection(lambda: self._onSync(action=action))
AnkiQt.onSyncForce = onSyncForce

def onSync(self):
    if self.media_syncer.is_syncing():
        self.media_syncer.show_sync_log()
    else:
        # new else branch.
        self.col.save(trx=False)
        self._onSync()


AnkiQt.onSync = onSync


def _onSync(self, action: Optional[str] = None):
    state_before_sync = self._current_state()
    self._sync(action)
    if action:
        if not self.loadCollection():
            return
    else:
        self.col.load()
        self._set_state(state_before_sync)
        self.reset()
    self.media_syncer.start()


AnkiQt._onSync = _onSync


def _sync(self, action: Optional[str] = None):
    """Return -- Whether the sync was cancelled"""
    from aqt.sync import SyncManager

    self.state = "sync"
    self.app.setQuitOnLastWindowClosed(False)
    self.syncer = SyncManager(self, self.pm, action=action)# new "action"
    self.syncer.sync()
    self.app.setQuitOnLastWindowClosed(True)


AnkiQt._sync = _sync

# New methods
###########

def _current_state(self):
    if not self.col:
        return None
    return State(
        state=self.state,
        did=self.col.decks.selected(),
        mid=self.col.models.current()["id"]
    )


AnkiQt._current_state = _current_state


def _set_state(self, state):
    if state is None:
        return
    self.state = state.state
    if state.did in self.col.decks.decks:
        self.col.decks.select(state.did)
    if state.mid in self.col.models.models:
        self.col.models.setCurrent(self.col.models.get(state.mid))
    self.reset()


AnkiQt._set_state = _set_state
