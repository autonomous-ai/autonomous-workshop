# Deep compaction ceiling lowered to 192k

Forge and Quest sessions on deep profiles v9 through v13 now compact at
192,000 tokens instead of 256,000. On `gpt-6-astra` the higher ceiling never
fired and Make turns failed once the thread passed about 210k tokens. Existing
runs keep their frozen identity and resume with the new ceiling. See ADR 0051.
