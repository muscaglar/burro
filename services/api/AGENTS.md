# services/api

Burro's HTTP API: FastAPI over one data release held in memory. It has no database. It is built to [docs/design/contract.md](../../docs/design/contract.md), sections 8 to 11; if the two disagree, change one of them in the same commit.

```
make api                     run it on this machine, on the synthetic release, at 127.0.0.1:8000
make openapi                 rewrite contracts/openapi.json after a route or a record changes
make test ARGS="-m full"     run the generated tests in full, which `make ci` samples
```

Settings come from the environment: `BURRO_RELEASE_DIR`, `BURRO_MODEL_ID`, `BURRO_MODEL_TIMEOUT_S`, `BURRO_MODEL_MAX_TOKENS`, `BURRO_HOST`, `BURRO_PORT`, `BURRO_ALLOWED_ORIGINS`. With none set it serves the committed synthetic release with the rule-based interpreter, to a browser on `http://localhost:3000` and no other.

## Privacy comes first

Raw prompt text and destination strings are never written to a log, an exception message, an error response or a call record (ADR 0005). This is kept by construction. Do not weaken any of these to make a change pass.

- **Logs.** `logs.event()` is the only way a line is written, and `logs.log_failure()` the only way an exception is, at the level of an error. A field that is not in `LOGGABLE` cannot be logged. No message is ever formatted, and a library's record is cut down to where it came from. Never call `logging` directly, never `print`, never `str(error)`.
- **Nothing of a spec.** No hash of a spec is logged or kept, plain or under a key, and nothing else that is worked out from one. The plain hash gives the spec back to anyone who can try specs, and a keyed one confirms a guess for whoever reads the log and can call the service. `spec_hash` goes in a response and nowhere else. There is no key in the service: do not add one to tell two calls apart without a new decision (ADR 0011).
- **Errors.** `message` is fixed text for the code. `fields` is built from pydantic's `loc` and `type` only, and a part of a path is kept only if it is one of our own field names. Raise `ApiError` with a code; never put a value in it.
- **The edge.** `boundary.Boundary` catches whatever a route lets fall and answers 500. It never raises again, because the server would print the message. The server's access log is off; the request line names the route template, never the path. No response is a redirect: `redirect_slashes` is off, because a redirect repeats the path in a header.
- **The model.** Only `claude.py` sends a person's words anywhere, and only to the model. A failure leaves as a `ModelFailure` with no message and no cause. `destination_text`, `area_text` and `words` are what a model copied from the person: each is held in a field that no `repr` shows, looked for in the text and dropped. What is withheld from a model's answer is counted and never named.
- **Where the words stand.** `rests_on` is served by route 1 to the caller, who holds the text: offsets, never words. It is never logged, never kept about a call and never stored in a share, and no other route takes or returns it. `logs.LOGGABLE` and `CallRecord` have no field for it, and a test says so.
- **Text in bodies.** Anything a person types travels in a `POST` body. A path holds an id from the release or an opaque share id. There are no query parameters.
- **Tests.** `tests/test_privacy.py` plants a canary in every route and every failure path, and looks for it in every log record, every line, standard output, every call record and every response. A new route or a new failure path gets a case there before it is merged.
- **What route 1's line depends on.** Its counts of edits and of rejections, and its codes of what was assumed and unmet, depend on the words and the spec together. They hold no id, no name and no number. Whether to go on logging them is an open point of the contract (section 13) and is not yours to settle by adding a field.

## Rules

- `Deps` holds everything a test may need to fake. A route reads the release, the clock and the ids from it, never from a module or the system.
- Ranking, the reducer, facts and the verifier live in `burro_core`. A route calls them; it never works out a score, a percentile or a sentence of its own. If a route needs arithmetic, the arithmetic belongs in core.
- Never import `burro_pipeline`. The API and the pipeline meet at the release folder. `loading.py` reads bytes and leaves every check to `open_release` in core.
- Only `claude_sdk.py` imports the provider's SDK, and `app.py` imports it inside a function, so a service with no key never loads it. A test checks both.
- A route is declared with its whole path (`/v1/...`) on its own router. `boundary.py` matches against the routes as declared, because how the framework nests included routers has changed between versions.
- Every response that holds data from the release carries `meta.synthetic` and the `X-Burro-Synthetic` header. Errors too.
- Missing data is `null`, never zero. Nothing is filled in on the way out.
- `contracts/openapi.json` is generated and committed. A test fails if it is out of date: run `make openapi`.
- Sign-in has one place, `identify` in `app.py`. Quotas and rate limits have one place, `admit`, beside it. Both are empty in this build.
- A request body is a `wire.Body`, and is listed in `wire.BODIES`. A number in it must be sent as a number: `Body` refuses `true` and `"0.5"` where the validator alone would read 1 and 0.5. A body may hold a field that is a number or `null`, and no other choice of types; a test says so. A model's answer is a `Body` too, so `true` is never position 1.
- A route that takes edits applies them first and checks the spec they leave, so a spec that names what the release has dropped can be put right by the edit that takes it out.
- The origins a browser may call from are a list in `Deps`, compared exactly. `Boundary` answers for them on every response, its own refusals included. Never a pattern, never `*`, never credentials. An entry that no browser would send, `https://burro.example:443`, is refused when the service starts, because it would match nothing and nobody would be told. Do not add the framework's CORS middleware beside it: it answers a browser it refuses outside the error envelope.
- `CallLog.add` lets go of what is too old, wherever it stands in the log. Nothing in the service reads the log, so a log that expired records only on reading would expire none.

## The model-backed interpreter

It is selected only when `ANTHROPIC_API_KEY` is present. Settings record that a key is there and never the key; the SDK reads it for itself. It is tested against a fake `ModelClient`, and `claude_sdk.py` against the real SDK with a transport that answers in the provider's place. **No test calls the provider, and it has never been run against the live API.** Before relying on it: run the 150 golden queries of the plan, and check that the schema in `claude.SCHEMA` is accepted as it stands.

From a model's answer the code keeps only what it can justify without trusting the model, because instructions are not a guarantee. The model must say which words of the person's each edit rests on. The code looks for them in the text as typed, and asks core what the rule-based reader made of the sentence they stand in (contract, section 8.2):

1. an edit whose words are not in the text, as typed and in one sentence, is left out;
2. a place or an area is kept only if the words of its name stand in that sentence side by side, and are the whole of a name or an alias: never across a bracket, a hyphen, a slash, quotes or a line break;
3. in a sentence the reader knows, an edit is kept only if the reader makes one of the same kind there, and what is applied is the reader's own edit;
4. in a sentence the reader does not know, a model may read a wish for a thing the reader has no phrase for, and no more: raised only where the sentence holds no word the reader has a rule for and no word of core's written list of doubt, taken away only where it holds a word of doubt or one that turns a wish away, and always as `inferred`;
5. a journey, a budget and a rule about an area are the reader's alone;
6. on a request about who lives somewhere, only the edits the reader also makes are kept, in every group;
7. a weight on recorded crime is applied only where the reader makes a stated edit that raises it;
8. a model that answers off topic does not overrule the reader;
9. a number in the answer must be a number.

Nothing in `claude.py` decides what a word means. Where a sentence ends, which words are known, which turn and which are doubt are core's, through `sentences_of`, `LEXICON`, the sets of `burro_core.vocabulary`, `prepare` and the reader's own `rests_on`. Do not write a list of words here, and do not split a sentence here. If a wish is read backwards through a model, find which of the rules let it through and write a test with a stand-in that answers wrongly. Changing `SYSTEM` alone is never the fix. Rules 3, 4 and 5 are stricter than the decision they were built to, and the contract says what that was measured to cost and to buy: do not loosen one without moving the floor and the ceiling in `tests/test_claude_kept.py`.

What code does not check is held in `tests/test_claude_kept.py` as tests that are expected to fail: a request about people that both the lexicon and the model miss, and a wish turned round, of a thing in words the reader has no phrase for, in words core does not list as doubt ("boozers on every corner would finish me off").

## Keeping the contract true

What the code does beyond the first draft of the contract has been written into it: the extra error and problem codes, `area_id` in route 4, `facts` and `weight` in route 7, `coarsened` in route 10, the limits route 11 serves, the deadline around the interpreter, `X-Request-Id`, logging as a list of what may be written, that nothing of a spec is logged, the headers a browser is answered with, what makes an origin one a browser sends, what is kept from a model's answer, and `rests_on` on route 1 with what its offsets count. If you add something the contract does not say, write it in where it applies, in the same change.

## What is not here yet

- A comparison shows no journey for an area that was not ranked. Which journey drives the score is decided by `rank()`, and working it out here would be a second copy of that arithmetic.
- `ETag` is sent, but a request with `If-None-Match` is answered in full. A `HEAD` is answered 405.
- The web app's real address. Until `BURRO_ALLOWED_ORIGINS` names it, only a page on `http://localhost:3000` may read an answer.
- It has not yet answered over a real socket. Every test and every check so far went through the test client, which calls the same app. Run `make api` and drive it with `curl` before the first deploy.
- The server's own answer to a request that is not valid HTTP is not the error envelope, and carries no synthetic flag. It never reaches the app.
