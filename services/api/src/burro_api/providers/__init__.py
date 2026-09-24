"""One adapter for each provider of a model, behind the one interface the reader knows.

`interface` is that interface. Each module here named for a provider holds
one class that fits it. `base` is how any of them reaches its provider,
`terms` is what people are told about each, and `choose` picks one from the
environment, or none.

Nothing here imports a provider's own library. Each call is one HTTPS POST
made with the standard library. See `docs/design/models.md`.
"""
