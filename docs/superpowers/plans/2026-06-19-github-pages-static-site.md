# GitHub Pages Static Site Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make the Bali wedding research site publishable from GitHub Pages branch-based hosting without a runtime database.

**Architecture:** Keep the existing site generator as the source of truth, add one Pages-oriented wrapper that writes the static site into `docs/`, then add root-level redirect and `.nojekyll` files so both `main /docs` and `main /root` Pages configurations can resolve to the generated site. Expose the wrapper through a dedicated CLI command so deployment stays explicit.

**Tech Stack:** Python 3, `unittest`, existing static-site generator in `bali_wedding_research.site`

---

### Task 1: Lock the Pages output contract with tests

**Files:**
- Modify: `tests/test_site.py`
- Modify: `tests/test_cli.py`

- [ ] **Step 1: Write the failing tests**

```python
written = write_pages_site(root)
assert written == [
    docs_dir / "index.html",
    docs_dir / "assets" / "site.css",
    docs_dir / "assets" / "site.js",
    docs_dir / "venues" / "example-cliffside-resort.html",
    docs_dir / ".nojekyll",
    root / "index.html",
    root / ".nojekyll",
]
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `python3 -m unittest tests.test_site.StaticSiteTest.test_write_pages_site_writes_docs_site_and_root_redirect tests.test_cli.CliTest.test_build_pages_site_writes_docs_site_and_redirect_files -v`
Expected: `ImportError` for `write_pages_site` and CLI failure because `build-pages-site` is unsupported.

### Task 2: Implement the Pages-oriented generator and CLI entrypoint

**Files:**
- Modify: `bali_wedding_research/site.py`
- Modify: `bali_wedding_research/cli.py`

- [ ] **Step 1: Add the new Pages wrapper in the site module**

```python
def write_pages_site(root: Path, docs_dir: Path | None = None) -> list[Path]:
    target_docs_dir = docs_dir or root / "docs"
    written = write_static_site(root, target_docs_dir)
    (target_docs_dir / ".nojekyll").write_text("", encoding="utf-8")
    (root / "index.html").write_text(_render_pages_redirect_page(), encoding="utf-8")
    (root / ".nojekyll").write_text("", encoding="utf-8")
    return [
        *written,
        target_docs_dir / ".nojekyll",
        root / "index.html",
        root / ".nojekyll",
    ]
```

- [ ] **Step 2: Add the dedicated CLI command**

```python
pages_parser = subparsers.add_parser("build-pages-site")
pages_parser.add_argument("--root", default=".")

if args.command == "build-pages-site":
    outputs = write_pages_site(root)
    for path in outputs:
        print(path)
    return 0
```

- [ ] **Step 3: Run the targeted tests**

Run: `python3 -m unittest tests.test_site.StaticSiteTest.test_write_pages_site_writes_docs_site_and_root_redirect tests.test_cli.CliTest.test_build_pages_site_writes_docs_site_and_redirect_files -v`
Expected: both tests pass.

### Task 3: Generate and verify the publishable Pages output

**Files:**
- Generate: `docs/index.html`
- Generate: `docs/assets/site.css`
- Generate: `docs/assets/site.js`
- Generate: `docs/venues/*.html`
- Generate: `docs/.nojekyll`
- Generate: `index.html`
- Generate: `.nojekyll`

- [ ] **Step 1: Build the Pages output**

Run: `python3 -m bali_wedding_research build-pages-site --root .`
Expected: prints the generated `docs/` site files plus the root redirect files.

- [ ] **Step 2: Verify the publishable artifacts exist**

Run: `find docs -maxdepth 2 \\( -name 'index.html' -o -name '.nojekyll' -o -path 'docs/assets/site.css' -o -path 'docs/assets/site.js' \\) | sort`
Expected: includes `docs/index.html`, `docs/.nojekyll`, `docs/assets/site.css`, and `docs/assets/site.js`.

- [ ] **Step 3: Run the test suite**

Run: `python3 -m unittest -v`
Expected: all tests pass.

### Task 4: Publish to the GitHub Pages branch

**Files:**
- Commit: repo changes created by Tasks 1-3

- [ ] **Step 1: Inspect branch topology before push**

Run: `git branch -a && git remote show origin`
Expected: confirms local work is on `master`, Pages branch exists as `origin/main`, and push target can be chosen deliberately.

- [ ] **Step 2: Create the publish commit**

```bash
git add bali_wedding_research/cli.py bali_wedding_research/site.py tests/test_cli.py tests/test_site.py docs index.html .nojekyll
git commit -m "Add GitHub Pages-compatible static site output"
```

- [ ] **Step 3: Push the commit to the branch GitHub Pages reads**

Run: `git push origin <local-branch>:main`
Expected: push succeeds so GitHub Pages can publish from the generated static files.
