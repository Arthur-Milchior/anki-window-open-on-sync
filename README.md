# Keep window open during sync
## Rationale
It's nice to avoid the window closed. It can be avoided, unless for
full sync. Unless I overlooked something, which might well be the
case.

## Warning

It's in Alpha. If I overlooked anything, please let me know so that I
may correct it.

## Technical

The problem with keeping windows open in Anki is that a lot of windows
have directly saved the collection instead of accessing it through the
main window.

Before and after sync, anki close and open the collection. This means
that all of those windows have a pointer to a closed
collection. Closing those windows is an easy solution to avoid this
problem. That would require to rewrite a big part of anki (but it
would be easy to do) and probably a bunch of add-ons.

Avoiding to close the collection is another solution. It may be less
safe if I overlooked a problem somewhere, but still worth a try.

## Links, licence and credits

Key         |Value
------------|-------------------------------------------------------------------
Copyright   | Arthur Milchior <arthur@milchior.fr>
Based on    | Anki code by Damien Elmes <anki@ichi2.net>
License     | GNU GPL, version 3 or later; http://www.gnu.org/licenses/gpl.html
Source in   | https://github.com/Arthur-Milchior/anki-window-open-on-sync
Addon number| [937448353](https://ankiweb.net/shared/info/937448353)
