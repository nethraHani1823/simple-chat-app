# Security Scanning Tools for a Startup CI Pipeline

A comparison of the options across four areas, and what to actually pick.

**Written for:** a small engineering team with no dedicated security person, no budget for tooling, and services that ship as Docker images onto Kubernetes.

**Date:** September 2026

---

## How the tools were judged

A startup has different constraints from a large company. The tool that wins a feature comparison often loses in real life. These are the things that decided the picks below.

| What matters | Why |
|---|---|
| Free, genuinely | Not "free tier for 200 tests a month". Free forever, for private company repos. |
| Single binary | No server to run. No database to maintain. Nobody has time. |
| Runs anywhere | The same command works on a laptop and in CI. This matters more than it sounds. |
| Quiet by default | A tool that reports 400 findings gets ignored within a week. A tool that reports 4 gets fixed. |
| Fails the build usefully | It must be able to stop a bad build, but only on things worth stopping for. |

The last two are the ones teams get wrong. A noisy scanner is worse than no scanner, because it teaches everyone to ignore the red X.

---

## 1. Secret scanning

**The problem:** someone pastes a password, an API key, or a token into the code and commits it. Once pushed, it is stolen. Deleting it later does not help, because the old commit still holds it and every clone has that commit.

### The options

| Tool | What it does well | Weak point | Cost |
|---|---|---|---|
| **Gitleaks** | Scans full git history. About 170 built-in rules. Custom rules via `.gitleaks.toml`. Outputs SARIF for the GitHub Security tab. | Only pattern matching. Cannot tell a live key from a dead one. | CLI is free (MIT). The official GitHub Action needs a paid licence key for org-owned repos. |
| **TruffleHog** | Verifies findings. It actually calls the AWS or Stripe API to check whether the key still works. Cuts false positives enormously. | Verification makes network calls out of your CI runner. Some teams dislike that. | Free and open source. Paid enterprise version exists. |
| **GitHub secret scanning** | Built in. Push protection blocks the secret at push time, before it ever lands. Also notifies the provider so they can revoke it. | Free only for public repos. Private repos need paid Secret Protection. Only knows partner patterns, not your internal formats. | Free (public). Paid per committer (private). |
| **detect-secrets** (Yelp) | Baseline file approach. Records existing findings so you only see new ones. Good for adding to an old messy repo. | Less actively developed. Fewer rules. | Free. |
| **Trivy** | Also does secret scanning as a side feature. | Fewer rules, and it scans files, not git history. Misses the old-commit problem entirely. | Free. |

### The important distinction

Pattern matching versus verification.

Gitleaks says *"this looks like an AWS key."* TruffleHog says *"this **is** an AWS key and it currently works."*

That difference decides how people react. A list of 60 maybe-secrets gets skimmed and closed. A list of 3 confirmed-live keys gets someone out of their chair.

### Pick

**Gitleaks CLI, plus a pre-commit hook.**

- Install the binary in CI directly. Do not use the official GitHub Action, because org-owned repos need a paid licence key for it.
- Also install it as a git pre-commit hook on every laptop. This is the part most teams skip, and it is the part that actually prevents the problem instead of reporting it afterwards.
- Add TruffleHog later if false positives become annoying. Its verification is the cure for that specific pain.

### Two traps

**The fetch-depth trap.** `actions/checkout` downloads only the newest commit by default. Gitleaks then scans one commit, finds nothing, and passes in two seconds. It looks great and checks almost nothing. You need `fetch-depth: 0` for a real history scan.

Practical split:
- Pull requests: scan the diff only. Seconds.
- Nightly cron: full history with `fetch-depth: 0`. Slow, but nobody is waiting.

**Detection is not remediation.** Once a secret is pushed, rotate the key. That is the only real fix. Gitleaks will keep flagging it because the history still holds it. Cleaning history means `git filter-repo` and a force push, which forces everyone to re-clone. Most teams rotate and move on, and that is the right call.

### Note on project status

The Gitleaks maintainer has declared the project feature-complete, with future releases limited to security patches. Not disqualifying for a stable scanner, but worth checking the repo before committing to it long term.

---

## 2. Dockerfile misconfiguration

**The problem:** the Dockerfile builds fine and the app runs fine, but the image runs as root, uses a floating `:latest` base tag, or bakes a secret into a layer. Nothing fails. It is just quietly unsafe.

### The options

| Tool | What it does well | Weak point | Cost |
|---|---|---|---|
| **Hadolint** | Purpose-built Dockerfile linter. Also runs ShellCheck against your `RUN` lines, so it catches shell bugs too. Tiny binary, instant. | Only Dockerfiles. Nothing else. | Free. |
| **Trivy config** | Checks Dockerfiles alongside Kubernetes and Terraform. One tool, one config. | Shallower on Dockerfiles than Hadolint. Misses shell-level issues. | Free. |
| **Checkov** | Very broad IaC coverage. Terraform, Kubernetes, Helm, Dockerfiles, CloudFormation. Large policy library. | Python, slower to start. Noisy out of the box. Overkill if you only have a few Dockerfiles. | Free. |
| **Dockle** | Checks the built image against CIS benchmarks, not the Dockerfile text. Catches things only visible after build. | Different job from the others. Not a replacement. | Free. |

### What Hadolint catches that matters

- `FROM node:latest` — an unpinned base means your build is not reproducible, and a poisoned upstream tag reaches you silently.
- No `USER` instruction — the container runs as root. On Kubernetes that is a meaningful escalation path.
- `apt-get install` without `--no-install-recommends` and without cleaning the cache — bigger image, more packages, more CVEs to triage later.
- Multiple `RUN` lines that should be one — more layers, larger image.
- Shell mistakes inside `RUN`, via ShellCheck. Unquoted variables, missing error handling.

### Pick

**Hadolint.**

- It does one job and does it better than the general-purpose tools.
- It is fast enough to run on every pull request without anyone noticing.
- Being narrow is a feature here. It will never flood you.
- Add Trivy's config scanning separately for Kubernetes and Helm files, since you need that anyway for other reasons.

Skip Checkov until you have real Terraform. It is a good tool aimed at a bigger problem than you currently have.

---

## 3. Dependency vulnerabilities

**The problem:** most of your application is other people's code. One `npm install` pulls in hundreds of packages written by strangers, and nobody reads them.

There are two separate threats here, and mixing them up leads to bad tool choices.

- **Accidental:** a real library has a genuine bug. This becomes a CVE. Most tools focus here.
- **Deliberate:** someone hijacks a package and adds code to steal your credentials. This is not a CVE. Nobody files a bug report admitting they stole your keys.

### The options

| Tool | What it does well | Weak point | Cost |
|---|---|---|---|
| **Dependabot** | Built into GitHub. Zero setup. Opens pull requests with the fix already applied, which is the part that actually gets things upgraded. | Reactive only. Noisy on old repos. Knows nothing about deliberately malicious packages. | Free, all repos. |
| **Trivy** | Lockfiles plus OS packages plus images plus IaC. One tool for most of the pipeline. | CVE-focused. Weak on the deliberate-attack side. | Free (Apache 2.0). |
| **OSV-Scanner** | Google's scanner over the OSV database. Also pulls the OpenSSF Malicious Packages feed, so it covers the deliberate side. | Lockfiles only. No images, no IaC. Still reactive. | Free. |
| **Socket** | Judges packages by behaviour: install scripts, network calls, obfuscated code. Does not wait for a report. Catches new attacks. | Deepest on npm and PyPI, lighter elsewhere. | Free for open source. Paid per developer for private work. |
| **Grype** | Fast, pairs with Syft for SBOMs. Solid CVE scanner. | Overlaps Trivy almost entirely. Little reason to run both. | Free. |
| **Snyk** | Good fix advice and developer experience. | Free tier has monthly test limits that a real team hits. | Limited free tier. |

### The gap that matters

Trivy, OSV-Scanner, Grype and Snyk are all reactive. They match your packages against a list of things already known to be bad. During the window between an attack starting and anyone reporting it, they all correctly report clean.

That window is where the damage happens. Socket is the only option here that closes it, because it looks at what a package does rather than waiting for a verdict.

### The part CI cannot fix

This is the most important paragraph in the document.

A malicious package usually runs its payload in a `postinstall` script. That script runs on the developer's laptop, the moment they type `npm install`. It reads `~/.ssh`, `~/.aws`, and `~/.npmrc` and sends the contents out.

By the time CI scans the repository, the laptop was already robbed. Hours earlier.

CI dependency scanning is worth doing. It is just not a shield against this. The shield has to sit before the install.

### Pick

**Dependabot plus Trivy plus OSV-Scanner. All free.**

- Dependabot: turn it on today. It is free, needs one YAML file, and it opens the upgrade PRs for you.
- Trivy: in CI, covering lockfiles and images together.
- OSV-Scanner: in CI, for the malicious packages feed that Trivy is weak on.

Yes, Trivy and OSV-Scanner overlap on lockfiles. That overlap is cheap and the malicious feed is worth it on its own.

### Free things worth more than another scanner

- `npm ci --ignore-scripts` blocks postinstall scripts entirely. This single flag stops the main attack mechanism. Use it locally and in CI.
- Commit lockfiles and pin versions. Several 2026 attacks only hit projects installing unpinned versions.
- Pin GitHub Actions to commit SHAs, not tags like `@v1`. A moving tag can be repointed at poisoned code. A commit SHA cannot. Trivy's own action was compromised twice in March 2026, which is exactly why this matters.

---

## 4. Docker image scanning after build

**The problem:** you scanned your code and it was clean. But the image also contains a whole operating system, a language runtime, and every system library they depend on. Most of your CVE count lives there, not in your code.

### The options

| Tool | What it does well | Weak point | Cost |
|---|---|---|---|
| **Trivy** | Scans OS packages, app dependencies, secrets and misconfigurations in one pass. Wide OS coverage. Easy filtering. | Database download can be slow if not cached. | Free (Apache 2.0). Action is free too. |
| **Grype** | Fast, accurate, pairs with Syft for SBOM generation. | Narrower scope. CVEs only. | Free. |
| **Docker Scout** | Integrated into Docker Desktop and Docker Hub. Nice interface. | Tied to the Docker ecosystem. Free tier limits on repositories. | Limited free tier. |
| **Clair** | Mature, used inside registries like Quay. | Needs a server and a database. Wrong shape for a small team. | Free. |
| **Dockle** | Checks image hardening against CIS benchmarks. Root user, missing healthcheck, and so on. | Not a CVE scanner. Complements rather than competes. | Free. |

### Pick

**Trivy.**

- One tool covers images, code, Kubernetes manifests and Helm charts. For a Kubernetes shop that consolidation is worth a lot.
- Free with no licence key, including the GitHub Action, unlike Gitleaks.
- Actively developed and widely used, so problems are easy to search.

### The noise problem, and how to handle it

A normal base image produces hundreds of findings. Most come from OS packages, not your code, and many have no fix available at all. If you fail the build on everything, the team disables the check by Friday.

Start here:

```bash
trivy image --severity HIGH,CRITICAL --ignore-unfixed --exit-code 1 myapp:${GIT_SHA}
```

- `--severity HIGH,CRITICAL` drops the low-priority noise.
- `--ignore-unfixed` hides findings nobody has released a patch for. You cannot act on those anyway.
- `--exit-code 1` fails the build on what remains.

Tighten this later once the count is under control. Starting strict and loosening never works, because the team stops trusting the check before you get there.

### Cache the database

The vulnerability database is roughly 40 MB, and the Java one is around 200 MB. It refreshes every six hours, so CI keeps re-downloading it. Cache it, or the download becomes slower than the scan.

### Pin the action

The official Trivy GitHub Action was compromised twice in March 2026. Pin it to a commit SHA, not `@v1` or `@master`. This applies to every third-party action you use, not only this one.

---

## The recommended stack

Everything below is free, and every tool is a single binary that runs the same on a laptop as in CI.

| Area | Tool | Where it runs |
|---|---|---|
| Secrets | Gitleaks CLI | Pre-commit hook, PR diff scan, nightly full-history scan |
| Dockerfile | Hadolint | Every pull request |
| Dependencies | Dependabot | GitHub, always on |
| Dependencies | Trivy + OSV-Scanner | Every pull request |
| Image | Trivy | After build, before push |
| Kubernetes and Helm | Trivy config | Every pull request |

Two tools do most of the work. Trivy covers four rows. Gitleaks covers the one thing Trivy is weak at.

### Suggested rollout order

Do not turn all of this on in one week. The team will revolt and you will end up with nothing.

1. **Dependabot.** One file, zero risk, immediate value.
2. **Gitleaks in report-only mode.** Do not fail builds yet. Look at what it finds first. There will be old secrets, and those need rotating before you can enforce anything.
3. **Hadolint.** Small, quiet, easy to fix what it finds.
4. **Trivy on images, HIGH and CRITICAL only, `--ignore-unfixed`.** Report first, then enforce once the count is manageable.
5. **Gitleaks enforcing**, once the historical findings are cleaned up and rotated.
6. **OSV-Scanner and Trivy config.** By now the team is used to the checks and this is a small addition.

---

## What this stack does not cover

Being honest about the gaps matters more than the tool list, because the gaps are where the actual incidents come from.

**Your laptop.** None of these watch what you install, which browser or IDE extensions you have, or what you downloaded. That needs an agent on the machine, such as osquery with Fleet, or Wazuh. It is a device management decision, not a pipeline one, and a company handling sensitive data very likely has something already.

**Credentials sitting on your machine.** No scanner fixes this. The fix is short-lived credentials, through something like Teleport, Vault, or AWS IAM Identity Center. Malware that reads `~/.aws` then finds something already expired. This is what "reducing standing access" means.

**Brand new attacks.** Every reactive tool here reports clean during the window before an attack is reported. Socket is the only listed option that closes it, and it is the only one that costs money for private work.

**The moment before install.** All of the CI tools run after `npm install` has already happened on someone's laptop. Socket's CLI alias, or `--ignore-scripts`, is the only thing that acts earlier.

---

## Things worth verifying before you present this

Tool licensing and project status change. These are the specific claims to re-check:

- Gitleaks Action licensing for organization-owned repositories.
- Gitleaks project status and whether a successor project has taken over.
- Whether Node 20 removal from GitHub-hosted runners has broken any action you depend on.
- Socket's current pricing tiers.
- GitHub secret scanning pricing for private repositories.
