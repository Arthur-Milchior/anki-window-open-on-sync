import gc
from typing import Optional

from anki.lang import _
from aqt.sync import SyncManager, SyncThread
from aqt.utils import askUserDialog

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
        col=self.mw.col, #new
        action=self.action, #new
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
def _confirmFullSync(self):
    self.mw.progress.finish()
    if self.thread.localIsEmpty:
        diag = askUserDialog(
            _("Local collection has no cards. Download from AnkiWeb?"),
            [_("Download from AnkiWeb"), _("Cancel")],
        )
        diag.setDefault(1)
    else:
        diag = askUserDialog(
            _(
                """\
Your decks here and on AnkiWeb differ in such a way that they can't \
be merged together, so it's necessary to overwrite the decks on one \
side with the decks from the other.

If you choose download, Anki will download the collection from AnkiWeb, \
and any changes you have made on your computer since the last sync will \
be lost.

If you choose upload, Anki will upload your collection to AnkiWeb, and \
any changes you have made on AnkiWeb or your other devices since the \
last sync to this device will be lost.

After all devices are in sync, future reviews and added cards can be merged \
automatically."""
            ),
            [_("Upload to AnkiWeb"), _("Download from AnkiWeb"), _("Cancel")],
        )
        diag.setDefault(2)
    self.mw.progress.start(immediate=True)
    ret = diag.run()
    if ret == _("Upload to AnkiWeb"):
        self.thread.fullSyncChoice = "upload"
        self.mw.onSyncForce("upload") # new call
    elif ret == _("Download from AnkiWeb"):
        self.thread.fullSyncChoice = "download"
        self.mw.onSyncForce("download") # new call
    else:
        self.thread.fullSyncChoice = "cancel"
    # case cancel removed
SyncManager._confirmFullSync = _confirmFullSync
