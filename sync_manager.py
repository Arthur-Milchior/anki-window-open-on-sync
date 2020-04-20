import gc
from typing import Optional

from anki.lang import _
from aqt.sync import SyncManager, SyncThread

old_init = SyncManager.__init__


def __init__(self, *args, action: Optional[str] = None, **kwargs):
    old_init(self, *args, **kwargs)
    self.action = action


SyncManager.__init__ = __init__


def _sync(self, auth=None):
    # to avoid gui widgets being garbage collected in the worker thread,
    # run gc in advance
    self._didFullUp = False
    self._didError = False
    gc.collect()
    # create the thread, setup signals and start running
    t = self.thread = SyncThread(
        self.pm.collectionPath(),
        self.pm.profile["syncKey"],
        auth=auth,
        hostNum=self.pm.profile.get("hostNum"),
        col=self.mw.col,
        action=self.action,
    )
    t._event.connect(self.onEvent)
    t.progress_event.connect(self.on_progress)
    self.label = _("Connecting...")
    prog = self.mw.progress.start(immediate=True, label=self.label)
    self.sentBytes = self.recvBytes = 0
    self._updateLabel()
    self.thread.start()
    while not self.thread.isFinished():
        if prog.wantCancel:
            self.thread.flagAbort()
            # make sure we don't display 'upload success' msg
            self._didFullUp = False
            # abort may take a while
            self.mw.progress.update(_("Stopping..."))
        self.mw.app.processEvents()
        self.thread.wait(100)
    self.mw.progress.finish()
    if self.thread.syncMsg:
        showText(self.thread.syncMsg)
    if self.thread.uname:
        self.pm.profile["syncUser"] = self.thread.uname
    self.pm.profile["hostNum"] = self.thread.hostNum

    def delayedInfo():
        if self._didFullUp and not self._didError:
            showInfo(
                _(
                    """\
Your collection was successfully uploaded to AnkiWeb.

If you use any other devices, please sync them now, and choose \
to download the collection you have just uploaded from this computer. \
After doing so, future reviews and added cards will be merged \
automatically."""
                )
            )

    self.mw.progress.timer(1000, delayedInfo, False, requiresCollection=False)


SyncManager._sync = _sync

old_onEvent = SyncManager.onEvent


def onEvent(self, evt, *args, **kwargs):
    if evt == "restart":
        choice = args[0]
        if choice in ("upload", "download"):
            self.mw.onSync(choice)
        else:
            assert self.thread.fullSyncChoice == "cancel"
    else:
        return old_onEvent(self, evt, *args, **kwargs)


SyncManager.onEvent = onEvent
