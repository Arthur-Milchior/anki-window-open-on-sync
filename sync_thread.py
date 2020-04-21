import time
from typing import Optional

from anki import hooks
from anki.collection import _Collection
from anki.storage import Collection
from anki.sync import FullSyncer, RemoteServer, Syncer
from aqt.sync import SyncThread

old_init = SyncThread.__init__


def __init__(self, *args, col: _Collection = None, action: Optional[str] = None, **kwargs):
    self.col = col
    self.gui_col = col is not None
    self.fullSyncChoice = action
    old_init(self, *args, **kwargs)


SyncThread.__init__ = __init__
 

def run(self):
    # init this first so an early crash doesn't cause an error
    # in the main thread
    self.syncMsg = ""
    self.uname = ""
    if not self.gui_col:
        try:
            self.col = Collection(self.path)
        except Exception as e:
            traceback.print_stack()
            self.fireEvent("corrupt")
            return
    self.server = RemoteServer(self.hkey, hostNum=self.hostNum)
    self.client = Syncer(self.col, self.server)
    self.sentTotal = 0
    self.recvTotal = 0

    def syncEvent(type):
        self.fireEvent("sync", type)

    def syncMsg(msg):
        self.fireEvent("syncMsg", msg)

    def http_progress(upload: int, download: int) -> None:
        if not self._abort:
            self.sentTotal += upload
            self.recvTotal += download
            self.progress_event.emit(
                self.sentTotal, self.recvTotal)  # type: ignore
        elif self._abort == 1:
            self._abort = 2
            raise Exception("sync cancelled")

    self.server.client.progress_hook = http_progress

    hooks.sync_stage_did_change.append(syncEvent)
    hooks.sync_progress_did_change.append(syncMsg)
    # run sync and catch any errors
    try:
        self._sync()
    except:
        err = traceback.format_exc()
        self.fireEvent("error", err)
    finally:
        if not self.gui_col: #condition is new
            # don't bump mod time unless we explicitly save
            self.col.close(save=False, downgrade=False)
        hooks.sync_stage_did_change.remove(syncEvent)
        hooks.sync_progress_did_change.remove(syncMsg)


SyncThread.run = run


def _fullSync(self):
    # totally new
    if self.fullSyncChoice:
        self._fullSyncKnown()
    else:
        self._fullSyncAsk()


SyncThread._fullSync = _fullSync


def _fullSyncAsk(self):
    # tell the calling thread we need a decision on sync direction, and
    # wait for a reply
    self.localIsEmpty = self.col.isEmpty()
    self.fireEvent("fullSync")
    while not self.fullSyncChoice:
        time.sleep(0.1)


SyncThread._fullSyncAsk = _fullSyncAsk


def _fullSyncKnown(self):
    assert self.fullSyncChoice in ("upload", "download")
    self.client = FullSyncer(
        self.col, self.hkey, self.server.client, hostNum=self.hostNum
    )
    try:
        if self.fullSyncChoice == "upload":
            if not self.client.upload():
                self.fireEvent("upbad")
        else:
            ret = self.client.download()
            if ret == "downloadClobber":
                self.fireEvent(ret)
                return
    except Exception as e:
        if "sync cancelled" in str(e):
            return
        raise


SyncThread._fullSyncKnown = _fullSyncKnown
