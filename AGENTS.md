# Agent instructions

## Objective

Keep this corpus source-verified, reproducible and internally consistent. A
change is complete only when the record, stored text/units, manifest, tests,
documentation and generated build agree.

## Workflow

- **Batch independent work.** Send related reads, searches and edits together;
  read several relevant files in one pass instead of one file per turn.
- **Delegate blocking work.** Give independent research or checks that wait on
  the network, a browser, a long build or another process to a subagent, and
  continue useful non-blocking work in the main thread. Collect the result at a
  checkpoint.
- **Do not idle on long-running processes.** Run persistent servers, watchers
  and long jobs in the background with stdout/stderr redirected to a log and a
  recorded PID; inspect readiness before using the result.
- **Verify once, narrowly.** Prefer the smallest check that covers the change,
  and rerun only the failed check after a repair. Do not repeat passing full
  suites or broaden validation without a concrete reason.
- **Make known edits together**, then run their checks in one batch.

## Repository invariants

- `catalog/instruments/*.json` is the source of truth. `units.jsonl` is
  generated from `text/en.txt`; never hand-edit units.
- Every acquired original has a URL, access date, byte count and SHA-256 in
  `catalog/acquisitions.json`.
- Every stored file is listed in the instrument manifest with a role, size and
  hash; `make validate` must pass.
- Unit text must be an exact slice of `text/en.txt`; labels must be unique.
  Never fabricate a source, date, party, declaration, quotation or hash.
- When segmentation changes, update the record, README, docs and tests together.
- Preserve third-party rights: official texts are not relicensed under the
  repository licence.

## Commands

```bash
make test                                  # build + integrity/determinism tests
make build                                 # regenerate build/
python3 tools/validate.py                  # schema and corpus validation
python3 tools/acquire.py --check           # verify stored original hashes
python3 tools/segment.py <id> --mode ...   # regenerate units after text changes
python3 tools/make_manifest.py             # regenerate manifests after file changes
```

## Git and publication

- The sole author for every commit is `Avvohacker <avvohacker@gmail.com>`.
- Do not add tool, assistant or co-author attribution to commits, source,
  documentation, generated files or GitHub metadata.
- Do not commit caches, virtual environments, secrets or files outside the
  repository.

## Output

- Keep responses concise and sectioned: what changed, what was checked, and
  what remains.
- State assumptions and unresolved gaps plainly. Never present an unverified
  claim as verified.
