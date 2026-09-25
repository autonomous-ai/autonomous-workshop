// Parallel Planner with Review — four-phase orchestration loop
//
// This template drives a multi-phase workflow:
//   Phase 1 (Plan):             An opus agent analyzes open issues, builds a
//                               dependency graph, and outputs a <plan> JSON
//                               listing unblocked issues with branch names.
//   Phase 2 (Execute + Review): For each issue, a sandbox is created via
//                               createSandbox(). The implementer runs first
//                               (100 iterations). If it produces commits, a
//                               reviewer runs in the same sandbox on the same
//                               branch (1 iteration). All issue pipelines run
//                               concurrently via Promise.allSettled().
//   Phase 3 (Squash):           The host squashes each completed branch onto
//                               the current branch as exactly one commit,
//                               "<issue title> (#<id>)", closes finished
//                               issues, and deletes the branch. An agent runs
//                               only to resolve a squash that conflicts.
//
// The outer loop repeats up to MAX_ITERATIONS times so that newly unblocked
// issues are picked up after each round of merges.
//
// Usage:
//   npx tsx .sandcastle/main.ts
// Or add to package.json:
//   "scripts": { "sandcastle": "npx tsx .sandcastle/main.ts" }

import { execFileSync, spawnSync } from "node:child_process";
import * as sandcastle from "@ai-hero/sandcastle";
import { docker } from "@ai-hero/sandcastle/sandboxes/docker";
import { z } from "zod";

// The planner emits its plan as JSON inside <plan> tags; Output.object extracts
// and validates it against this schema. We use Zod here, but any Standard
// Schema validator works just as well — Valibot, ArkType, etc. See
// https://standardschema.dev.
const planSchema = z.object({
  issues: z.array(
    z.object({ id: z.string(), title: z.string(), branch: z.string() }),
  ),
});

// ---------------------------------------------------------------------------
// Configuration
// ---------------------------------------------------------------------------

// The `origin` remote uses a custom SSH host alias (e.g. `git@gh-rein:...`),
// which `gh` cannot resolve to a GitHub host. GH_REPO names the repository
// explicitly so `gh` skips remote detection entirely, both in the sandbox
// (where the plan prompt's `!gh issue list ...` expansion runs) and on the
// host for any `gh` call this script makes directly.
const GH_REPO = "autonomous-ai/autonomous-workshop";
process.env.GH_REPO ??= GH_REPO;

// Env injected into each sandbox container. GH_TOKEN comes from
// .sandcastle/.env via the env resolver, so it does not need repeating here.
const sandboxEnv = { GH_REPO };

// Maximum number of plan→execute→merge cycles before stopping.
// Raise this if your backlog is large; lower it for a quick smoke-test run.
const MAX_ITERATIONS = 10;

// Hooks run inside the sandbox before the agent starts each iteration.
// npm install ensures the sandbox always has fresh dependencies.
const hooks = {
  sandbox: { onSandboxReady: [{ command: "npm install" }] },
};

// Copy node_modules from the host into the worktree before each sandbox
// starts. Avoids a full npm install from scratch; the hook above handles
// platform-specific binaries and any packages added since the last copy.
const copyToWorktree = ["node_modules"];

// The implementer ends with exactly one of these. Only COMPLETE closes the
// issue; INCOMPLETE work still lands, and the issue stays open.
const COMPLETE = "<promise>COMPLETE</promise>";
const INCOMPLETE = "<promise>INCOMPLETE</promise>";

// ---------------------------------------------------------------------------
// Squash helpers (host-side git, deterministic)
// ---------------------------------------------------------------------------

function git(...args: string[]): string {
  return execFileSync("git", args, { encoding: "utf8" }).trim();
}

// Squash message: the issue title as subject, then each branch commit's
// message (implementer and reviewer) with the `RALPH:` prefix and trailers
// removed, then the de-duplicated trailers once at the end.
function squashMessage(issue: { id: string; title: string }, branch: string) {
  const id = issue.id.replace(/^#/, "");
  const bodies: string[] = [];
  const trailers = new Set<string>();
  const shas = git("rev-list", "--reverse", `HEAD..${branch}`)
    .split("\n")
    .filter(Boolean);
  for (const sha of shas) {
    const lines = git("log", "-1", "--format=%B", sha)
      .replace(/^RALPH:\s*/, "")
      .split("\n");
    const kept: string[] = [];
    for (const line of lines) {
      if (/^Co-Authored-By:/i.test(line)) trailers.add(line);
      else kept.push(line);
    }
    bodies.push(kept.join("\n").trim());
  }
  return [`${issue.title} (#${id})`, ...bodies, [...trailers].join("\n")]
    .filter(Boolean)
    .join("\n\n");
}

function hasConflicts(): boolean {
  return git("diff", "--name-only", "--diff-filter=U") !== "";
}

// ---------------------------------------------------------------------------
// Main loop
// ---------------------------------------------------------------------------

for (let iteration = 1; iteration <= MAX_ITERATIONS; iteration++) {
  console.log(`\n=== Iteration ${iteration}/${MAX_ITERATIONS} ===\n`);

  // -------------------------------------------------------------------------
  // Phase 1: Plan
  //
  // The planning agent (opus, for deeper reasoning) reads the open issue list,
  // builds a dependency graph, and selects the issues that can be worked in
  // parallel right now (i.e., no blocking dependencies on other open issues).
  //
  // It outputs a <plan> JSON block — Output.object parses and validates it.
  // -------------------------------------------------------------------------
  const plan = await sandcastle.run({
    hooks,
    sandbox: docker({ env: sandboxEnv }),
    name: "planner",
    // One iteration is enough: the planner just needs to read and reason,
    // not write code. (Structured output requires maxIterations: 1.)
    maxIterations: 1,
    // Opus for planning: dependency analysis benefits from deeper reasoning.
    agent: sandcastle.claudeCode("claude-opus-5-5", { effort: "medium" }),
    promptFile: "./.sandcastle/plan-prompt.md",
    // Extract and validate the <plan> JSON into a typed object. Throws
    // StructuredOutputError if the tag is missing, the JSON is malformed, or
    // validation fails — which aborts the loop.
    output: sandcastle.Output.object({ tag: "plan", schema: planSchema }),
  });

  const issues = plan.output.issues;

  if (issues.length === 0) {
    // No unblocked work — either everything is done or everything is blocked.
    console.log("No unblocked issues to work on. Exiting.");
    break;
  }

  console.log(
    `Planning complete. ${issues.length} issue(s) to work in parallel:`,
  );
  for (const issue of issues) {
    console.log(`  ${issue.id}: ${issue.title} → ${issue.branch}`);
  }

  // -------------------------------------------------------------------------
  // Phase 2: Execute + Review
  //
  // For each issue, create a sandbox via createSandbox() so the implementer
  // and reviewer share the same sandbox instance per branch. The implementer
  // runs first; if it produces commits, the reviewer runs in the same sandbox.
  //
  // Promise.allSettled means one failing pipeline doesn't cancel the others.
  // -------------------------------------------------------------------------

  const settled = await Promise.allSettled(
    issues.map(async (issue) => {
      const sandbox = await sandcastle.createSandbox({
        branch: issue.branch,
        sandbox: docker({ env: sandboxEnv }),
        hooks,
        copyToWorktree,
      });

      try {
        // Run the implementer
        const implement = await sandbox.run({
          name: "implementer",
          maxIterations: 100,
          agent: sandcastle.claudeCode("claude-sonnet-5", { effort: "medium" }),
          promptFile: "./.sandcastle/implement-prompt.md",
          completionSignal: [COMPLETE, INCOMPLETE],
          promptArgs: {
            TASK_ID: issue.id,
            ISSUE_TITLE: issue.title,
            BRANCH: issue.branch,
          },
        });

        // Only review if the implementer produced commits
        if (implement.commits.length > 0) {
          const review = await sandbox.run({
            name: "reviewer",
            maxIterations: 1,
            agent: sandcastle.claudeCode("claude-opus-5-5", { effort: "medium" }),
            promptFile: "./.sandcastle/review-prompt.md",
            promptArgs: {
              BRANCH: issue.branch,
            },
          });

          // Merge commits from both runs so the merge phase sees all of them.
          // Each sandbox.run() only returns commits from its own run.
          return {
            ...review,
            completed: implement.completionSignal === COMPLETE,
            commits: [...implement.commits, ...review.commits],
          };
        }

        return {
          ...implement,
          completed: implement.completionSignal === COMPLETE,
        };
      } finally {
        await sandbox.close();
      }
    }),
  );

  // Log any agents that threw (network error, sandbox crash, etc.).
  for (const [i, outcome] of settled.entries()) {
    if (outcome.status === "rejected") {
      console.error(
        `  ✗ ${issues[i]!.id} (${issues[i]!.branch}) failed: ${outcome.reason}`,
      );
    }
  }

  // Only pass branches that actually produced commits to the merge phase.
  // An agent that ran successfully but made no commits has nothing to merge.
  const completedIssues = settled
    .map((outcome, i) => ({ outcome, issue: issues[i]! }))
    .filter(
      (entry) =>
        entry.outcome.status === "fulfilled" &&
        entry.outcome.value.commits.length > 0,
    )
    .map((entry) => ({
      ...entry.issue,
      completed:
        entry.outcome.status === "fulfilled" && entry.outcome.value.completed,
    }));

  const completedBranches = completedIssues.map((i) => i.branch);

  console.log(
    `\nExecution complete. ${completedBranches.length} branch(es) with commits:`,
  );
  for (const branch of completedBranches) {
    console.log(`  ${branch}`);
  }

  if (completedBranches.length === 0) {
    // All agents ran but none made commits — nothing to merge this cycle.
    console.log("No commits produced. Nothing to merge.");
    continue;
  }

  // -------------------------------------------------------------------------
  // Phase 3: Squash
  //
  // Each branch lands as exactly one commit on the current branch, in plan
  // order, so history stays linear: one issue, one commit, "<title> (#<id>)".
  // The host does the git work itself; an agent only runs when a squash
  // conflicts, and it resolves and verifies without committing.
  // -------------------------------------------------------------------------
  if (git("status", "--porcelain", "--untracked-files=no") !== "") {
    throw new Error(
      "Working tree has uncommitted changes; refusing to squash branches.",
    );
  }

  for (const issue of completedIssues) {
    const id = issue.id.replace(/^#/, "");
    const message = squashMessage(issue, issue.branch);
    const squash = spawnSync("git", ["merge", "--squash", issue.branch], {
      encoding: "utf8",
    });

    if (squash.status !== 0) {
      if (!hasConflicts()) {
        throw new Error(`git merge --squash ${issue.branch} failed:\n${squash.stderr}`);
      }
      console.log(`  ${issue.branch}: conflicts, running resolver`);
      await sandcastle.run({
        hooks,
        sandbox: docker({ env: sandboxEnv }),
        name: `resolver-${id}`,
        maxIterations: 1,
        agent: sandcastle.claudeCode("claude-opus-5-5", { effort: "medium" }),
        promptFile: "./.sandcastle/resolve-prompt.md",
        promptArgs: { BRANCH: issue.branch, ISSUE: `#${id}: ${issue.title}` },
      });
      if (hasConflicts()) {
        // Leave the branch for a human; restore the clean tree and move on.
        git("reset", "--hard", "HEAD");
        console.error(`  ✗ ${issue.branch}: conflicts unresolved, left unmerged`);
        continue;
      }
      git("add", "-A");
    }

    if (git("diff", "--cached", "--name-only") === "") {
      console.log(`  ${issue.branch}: no net changes, nothing to commit`);
    } else {
      execFileSync("git", ["commit", "--quiet", "-F", "-"], { input: message });
      console.log(`  ${issue.branch} → ${git("log", "-1", "--format=%h %s")}`);
    }

    if (issue.completed) {
      execFileSync("gh", [
        "issue",
        "close",
        id,
        "--comment",
        `Completed by Sandcastle in ${git("rev-parse", "HEAD")}`,
      ]);
    } else {
      console.log(`  #${id} left open: implementer reported it incomplete`);
    }

    // Squashed branches are fully represented by their commit; keep none.
    git("worktree", "prune");
    git("branch", "-D", issue.branch);
  }

  console.log("\nBranches squashed.");
}

console.log("\nAll done.");
