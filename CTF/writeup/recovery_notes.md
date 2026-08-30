# Recovery Notes: Crownspire Deploy Key Leak

During a forensic audit of the leaked `crownspire-deploy` repository, we successfully recovered a production credential that had been committed and subsequently removed from the visible commit history.

## Summary of Findings

- **Target File**: `reliquary.creds`
- **Leak Source**: A temporary commit made by Doran Ash (`d.ash@crownspire.valyssar`) on Wed May 27 23:47:19 2026.
- **Recovered Credentials**:
  ```ini
  RELIQUARY_ENDPOINT=https://reliquary.crownspire.valyssar:9000
  RELIQUARY_BUCKET=crownspire-reliquary-prod
  AWS_ACCESS_KEY_ID=AKIACROWNSPIRE7WARD3N
  AWS_SECRET_ACCESS_KEY=HTB{th3_r3l1qu4ry_n3v3r_f0rg3ts}
  WARDEN_SIGNING_KEY=astrael-relic-sigil-2f9c
  ```

---

## How to Solve: Forensic Methodology

When analyzing a Git repository for deleted/hidden commits or secrets in a forensic CTF challenge, follow this general workflow:

### Step 1: Check Visible History and Local Reflogs
Begin by checking standard history logs and local branch movement logs:
```bash
git log --oneline
git reflog
```
*Note: In backups or exported repositories, local reflogs are often missing or cleared, making the visible history look completely spotless.*

### Step 2: Scan for Unreachable (Dangling) Objects
When commits are removed (e.g., via `git reset --hard`, `git commit --amend`, or interactive rebases), the associated commit, tree, and blob objects are disconnected from the commit history tree. However, they remain in the Git object database (`.git/objects/`) until Git runs a garbage collection (`git gc`).

To search for these loose, unreachable objects:
```bash
git fsck --unreachable --lost-found
```
This utility will output lists of unreachable objects, categorized by type:
- `unreachable commit <hash>`
- `unreachable blob <hash>`
- `unreachable tree <hash>`

### Step 3: Inspect the Recovered Objects
Once you have the hashes, inspect them to recover the deleted files and commit messages:
* **To view a commit's metadata and the code diff it introduced**:
  ```bash
  git show <commit_hash>
  ```
* **To view the raw contents of a specific file/blob**:
  ```bash
  git show <blob_hash>
  ```

Additionally, because we used the `--lost-found` flag, Git recovers these dangling files and writes them directly to:
* `.git/lost-found/commit/` (for commit files)
* `.git/lost-found/other/` (for raw blobs and trees)

You can grep directly through these recovered files to find flags or credentials:
```bash
grep -rn "HTB{" .git/lost-found/
```

---

## Technical Recovery Methodology

Although the current branch history appeared clean, Git does not immediately prune objects that become disconnected from branch heads (dangling/unreachable objects) unless an explicit garbage collection (`git gc --prune=now`) is forced. 

### 1. Database Verification
We ran a filesystem consistency check on the repository to look for unreachable objects:
```bash
git fsck --unreachable --lost-found
```

This identified three key dangling objects:
* **Commit**: `3c8803d7146cd07c75325d6b555116200f2569ee`
* **Blob (File Content)**: `12b14971d38c09ee73fed80613951dfdd3562291`
* **Tree**: `1fe5a4a75df03ff80a3743b93b8df188ee48c06c`

### 2. Payload Extraction
By inspecting the unreachable commit, we reconstructed the exact patch that introduced the credentials:
```bash
git show 3c8803d7146cd07c75325d6b555116200f2569ee
```

This revealed the commit message:
> *temp: add reliquary.creds to debug 403 on manifest push (REVERT ME)*

---

## Remediation Recommendations

> [!WARNING]
> Simply deleting a file or resetting commits in git **does not** instantly purge the data from the repository database or clones that were pulled while the commit existed.

To prevent similar leaks or fully purge historical leaks in the future, implement the following:

1. **Rotate the Secret Immediately**: The `AWS_SECRET_ACCESS_KEY` (`HTB{th3_r3l1qu4ry_n3v3r_f0rg3ts}`) must be revoked on AWS and Cinderbound production systems.
2. **Purge Git History Completely**: If a repository must be cleaned of a sensitive file, use toolings like `git-filter-repo` or BFG Repo-Cleaner, and ensure garbage collection is forced on remote servers:
   ```bash
   git reflog expire --expire=now --all
   git gc --prune=now --aggressive
   ```
3. **Pre-commit Scanning**: Deploy pre-commit hooks (e.g., `gitleaks` or `trufflehog`) to check local code modifications for high-entropy strings and credentials before allowing a commit.
