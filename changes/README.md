# Change fragments

Add one Markdown file per pull request:

```text
changes/<issue-or-short-slug>.<kind>.md
```

Allowed kinds are `added`, `changed`, `deprecated`, `removed`, `fixed`, and
`security`. Use the pull request number when known, for example:

```text
changes/482.changed.md
```

The file contains one concise bullet written for users or contributors:

```markdown
- Move Make-owned skills into the installed Make component without changing
  their locked bytes.
```

Name commands, public imports, schemas, state versions, or migration actions
when they matter. Do not describe an offline fixture as live evidence. Security
fragments may remain deliberately vague until coordinated disclosure.
