"""Kept: what becomes of a release once it is built.

A release of London is built in a hosted run, on a machine that is thrown
away. It is kept in a bucket of its own, approved by its lock, and taken from
the bucket to the folder an image is built from. Nothing here builds a release
and nothing here serves one.

| Module | Gives |
|---|---|
| `store.py` | Where releases are kept: a bucket, or a folder that stands in for one |
| `lock.py` | The lock of a release, as the one that is committed is read |
| `cli.py` | The steps `keep` and `take` |

The bucket of releases is not the store of publishers' files. It is named by
variables of its own, and opened by keys of its own: the key that writes a
release opens no publisher's file, and the key that reads a publisher's file
writes no release.

A release that is kept is served nowhere for being kept. To approve it is to
commit its lock, and `take` takes no release of London but the one a committed
lock names, with every file held to the hash the lock gives.
"""
