# Cross Host Submodule Sync Test

Synthetic fixture for a **public GitHub.com root** with a **private
github.qualcomm.com submodule**. No internal project source is copied into
this public repository.

## Topology

```text
github.com/zgeorge-dev/profiles-cross-host-submodule-test
  qgenie-profile.yaml                     root profile, version 1.1.1
  skills/root-control/SKILL.md            public control skill
  msw/skills/review-ext/SKILL.md           public Review Ext test skill
  skills/shared-enterprise-marker         tracked relative Git symlink
    -> ../enterprise-child/skills/enterprise-marker
  enterprise-child                       real Git submodule, mode 160000
    github.qualcomm.com/zgeorge/profiles-cross-host-enterprise-fixture
      qgenie-profile.yaml                 enterprise child, version 1.1.0
      skills/enterprise-marker/SKILL.md    private marker skill
```

The test exercises submodule hydration, child-profile discovery, and a relative
symlink into the hydrated enterprise content. A GitHub archive of the public
root alone does not contain the enterprise files.

## Clone and verify locally

You need GitHub Enterprise access to the private child repository:

```sh
git clone --recurse-submodules https://github.com/zgeorge-dev/profiles-cross-host-submodule-test.git
cd profiles-cross-host-submodule-test
python -m pip install -r scripts/requirements.txt
python scripts/verify_fixture.py
git submodule status
```

For an existing clone:

```sh
git submodule update --init --recursive
python scripts/verify_fixture.py
```

On Windows, Git can check out symlinks as small text files when native symlinks
are disabled. The verifier checks the actual Git symlink object. Registry
hydration must use its tracked `120000` mode and link target, not a developer's
Windows checkout behavior.

## Registry test setup

Use a disposable DEV/TST profile, not an existing production profile.

1. Create a root profile:
   - **Name:** `Cross Host Submodule Test`
   - **Slug:** `cross-host-submodule-test`
   - **Initial registry version:** `1.0.0` (the authored `1.1.1` is newer).
2. Connect its GitHub sync configuration:
   - **Repository:** `https://github.com/zgeorge-dev/profiles-cross-host-submodule-test`
   - **Branch:** `main`
   - **Subdirectory:** empty / repository root
   - **Root access mode:** anonymous / public repository
3. Confirm `qgeniecoregitsvc` has **Read** access to the enterprise child.
   The deployment must also have a valid `QGENIE_GITHUB_ENTERPRISE_PAT` for
   that account. Do not put tokens in this repository or in profile YAML.
4. Run repository validation and a manual sync. Complete any normal review
   steps; do not bypass scanner or governance requirements.

The fixture disables pruning and profile deletion in both YAML manifests.
Use a new disposable profile to avoid version conflicts with earlier test runs.

## Expected assertions

After a completed, applied sync:

- Root version is `1.1.1`.
- Root has its authored `root-control` skill with marker `ROOT_CONTROL_V1`.
- Root has its authored `review-ext` skill with marker `PUBLIC_REVIEW_EXT_V1`.
- The direct child `cross-host-enterprise-child` exists at version `1.1.0`.
- The child's `enterprise-marker` skill contains `ENTERPRISE_MARKER_V1`.
- The root's linked `enterprise-marker` skill contains the same enterprise
  marker, materialized through the tracked relative symlink.
- The child content comes from the exact commit shown by
  `git ls-tree HEAD enterprise-child`, not the enterprise branch's latest HEAD.
- A private dependency failure is reported explicitly; a root-only import is
  not a passing result.

Local verification proves fixture structure and developer-account readability,
not that the deployed registry service account authenticated or applied a sync.

## Public Review Ext submodule content

The skill at `msw/skills/review-ext/SKILL.md` also lets another repository use
this public repository as a skill provider. For a submodule checked out at
`vendor/msw-review-stack`, a symlink at `skills/review-ext` can point to:

```text
../vendor/msw-review-stack/msw/skills/review-ext
```

That relative target starts from the symlink's containing `skills/` directory.
The parent must pin a commit containing this skill; pushing a newer provider
commit alone does not update the parent's submodule pointer. Public access to
this repository does not grant access to its private enterprise child.

## Follow-up pinning test

1. In a separate enterprise checkout, update the marker and increment the
   enterprise profile version, then commit and push.
2. Leave this parent's submodule pointer unchanged: its synced content must
   remain at the original pinned enterprise commit.
3. Update the parent's enterprise submodule checkout to the new child commit.
4. Match the declared child version in this root manifest and increment the
   root profile version.
5. Commit and push the root manifest and submodule pointer, then sync again.

Keep all future fixture content synthetic. Never commit credentials, private
project source, or production configuration here.
