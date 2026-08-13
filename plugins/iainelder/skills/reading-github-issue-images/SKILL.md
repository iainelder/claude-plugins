---
name: reading-github-issue-images
description: Reads images and screenshots attached to a GitHub issue, pull request, or comment. Use when the user gives a GitHub issue or PR URL or number and asks what an attached image shows, or says things like "read the images in this issue", "what does the screenshot in #123 show", "look at the attachment on that PR", "can you see the image I attached".
---

# Reading images attached to GitHub issues

GitHub stores issue and pull request attachments at `https://github.com/user-attachments/assets/<uuid>`. For a private repository these URLs are **not** publicly readable: an unauthenticated request returns a short text body rather than image data. The attachment must be fetched with authentication, saved to a file, and then read.

## Steps

### 1. Get the issue or PR content

Read the body and comments as JSON, so the raw Markdown with its image tags is visible:

```bash
gh issue view <number> --repo <owner>/<repo> --json title,body,comments
```

For a pull request, use `gh pr view` with the same flags. If the user supplied a full URL, the owner, repo, and number can be parsed from it.

### 2. Find the attachment URLs

Attachments appear in the body and in each comment's `body` field, in either of two forms:

```html
<img width="1080" height="797" alt="Image" src="https://github.com/user-attachments/assets/9304d376-1a60-4cc0-9c51-2bb6a963757b" />
```

```markdown
![alt text](https://github.com/user-attachments/assets/9304d376-1a60-4cc0-9c51-2bb6a963757b)
```

Collect every `user-attachments/assets/<uuid>` URL. Check the comments as well as the body — attachments are easy to miss when they appear only in a later comment.

### 3. Download each attachment

Use `gh api` with the full URL, redirecting the bytes to a file:

```bash
gh api "https://github.com/user-attachments/assets/<uuid>" > image.png
```

Write the files somewhere temporary, not into the user's repository.

**Do not** build a `curl` command that interpolates a token, such as
`curl -H "Authorization: token $(gh auth token)" ...`. The shell expands that
before `curl` runs, leaving the credential in the process arguments where any
local user can read it via `ps`, and in shell history. `gh api` looks the
credential up in-process, so nothing sensitive reaches the command line.

### 4. Confirm the download is really an image

An auth or network failure produces a small text file rather than an error exit code:

```bash
file image.png
```

Expect something like `PNG image data, 1080 x 797`. If it reports `ASCII text`, the download failed — inspect the file's contents for the error message rather than trying to read it as an image.

### 5. Read the image

Use the Read tool on each downloaded file to view it, then describe what it shows, attributing each image to the body or to a specific comment.

## Notes

- Works the same for issues and pull requests, and for attachments in review comments.
- A public repository's attachments can often be fetched without authentication, but `gh api` works for both, so there is no reason to branch on visibility.
- Attachments the user pasted as GitHub-hosted images from another repository they cannot access will fail; report that rather than guessing at the content.
