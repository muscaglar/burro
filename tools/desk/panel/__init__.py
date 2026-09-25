"""The panel of the review desk: look through what is served, rename it, and adjust it.

It is the desk with more to it: the same server on this machine alone, one more
page, plain files. Nothing a person does here changes what is served. A change is
a line in a file of changes, and a build that is given the file applies it.

The queues of the desk need Python alone. The panel needs core and the pipeline,
to read a release as it is served and to work a band and a rank out as a build
does. So it is read only when the desk is started with the packages installed.

See docs/design/panel.md.
"""
