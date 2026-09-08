---
name: mega-cmd
description: |
  Use this skill for MEGA cloud storage, encrypted file management, and workflows involving file organization, sharing, search, sync, backup, bulk transfer to/from MEGA, or MEGA automation.
compatibility: |
  - MEGA CMD CLI must be installed and accessible via `mega-` commands
  - User must have a MEGA account (free account with 20GB included)
  - MEGA CMD should be logged in via `mega-login <email>`
---

# MEGA CMD Skill

MEGA CMD is a CLI for [MEGA cloud storage](https://mega.io/cmd).

All `mega-*` commands operate on **cloud paths** rooted at `/`, not local files.

## Critical Rules

- **Only use commands documented here.** Do not invent flags or options.
- `-f` flag skips confirmations. **Only** `mega-export` and `mega-rm` accept `-f`. No other command does.
- Exit code 0 = success. Non-zero = fatal error (usually means invalid path or permission denied).
- **Save all local files in the current working directory (`./`)**, not `/tmp`. The working directory persists; `/tmp` may not be accessible.

## Account & Status

```bash
mega-whoami                    # Check logged-in account
mega-df -h                     # Show storage usage (human-readable)
```

Exit codes: 0 = logged in, 57 = not logged in

## Search & Browse

### Find Files
```bash
mega-find /path --pattern="*.pdf"                 # Find by pattern
mega-find / --pattern="*.pdf" --mtime=-30d -l     # Recent files with timestamps
mega-find / --pattern="*.jpg" -l                  # List with details
```

**Multi-extension searches:** When searching for a file category (e.g., "JPEG images"), search **all relevant extensions**:
```bash
mega-find / --pattern="*.jpg"   # Find JPEGs
mega-find / --pattern="*.jpeg"  # AND JPEGs with alternate extension
```

### List & Browse
```bash
mega-ls /path                    # List files in folder
mega-ls -l /path                 # Long format (name, size, date)
mega-ls -l /                     # List root folder with details
```

## Create & Organize

### Create Folders
```bash
mega-mkdir -p /path/to/folder    # Create folder with parents (like mkdir -p)
mega-mkdir /Invoices/2025        # Create specific folder structure
```

### Move & Copy
```bash
mega-mv /source/file.pdf /destination/    # Move file
mega-mv /Old\ Folder /New\ Folder         # Rename folder (escape spaces)
mega-cp /source/file.pdf /destination/    # Copy file
```

## Upload & Download

### Upload Files
```bash
mega-put ./local-file.pdf /remote/path/           # Upload single file
mega-put -c ./local-folder/ /remote/destination/  # Upload folder recursively
```

**Best practice for bulk uploads:** Organize files locally first, then upload the folder once with `mega-put -c`; this is faster and cleaner than per-file uploads.

Example workflow:
```bash
# 1. Organize locally
mkdir ./invoices-to-upload
cp ~/Downloads/invoice*.pdf ./invoices-to-upload/

# 2. Upload entire folder
mega-put -c ./invoices-to-upload/ /Invoices/2025/
# Creates: /Invoices/2025/invoices-to-upload/invoice1.pdf, invoice2.pdf, ...
```

### Download Files
```bash
mega-get /remote/file.pdf ./local/destination/   # Download file
mega-get /remote/folder ./local/                 # Download folder recursively
```

## Sharing & Links

### Create Public Links
```bash
mega-export -a -f /path/to/file.pdf              # Create public link (no expiry)
mega-export -a -f /path/to/folder/               # Create link to folder
mega-export -d /path/to/file                     # Remove public link
```

**Output:** A `https://mega.nz/file/...` link anyone can access.

**Pro account features** (not available on free accounts):
- Password-protected links
- Link expiry dates

### Share with Other Users
```bash
mega-share -a --with=user@email.com /path/folder    # Share folder (read-only)
mega-share /path                                     # List current shares
mega-export /path                                    # Check if path has public link
```

## Delete & Cleanup

### Delete Files
```bash
mega-rm -r -f /path/to/file                      # Delete file (no prompt)
mega-rm -r -f /path/to/folder/                   # Delete folder recursively
```

**⚠️ Warning:** Deletion is permanent. No trash/recycle bin. Use with caution.

### Clean Up Version History
```bash
mega-deleteversions -f --all                     # Remove all file versions
```

MEGA keeps version history automatically. This command reclaims space.

## Images & Thumbnails

### Download Thumbnails (Fast)
```bash
mega-thumbnail /remote/photo.jpg ./thumb.jpg    # Get thumbnail (~50KB)
```

### Download Full Quality
```bash
mega-get /remote/photo.jpg ./full-size/          # Get full original
```

**Strategy for image workflows:** Check thumbnails first, then download only the originals you need to save bandwidth and time.

## Sync & Backups

### Set Up Folder Sync
```bash
mega-sync /local/path /remote/path/              # One-way sync (local → remote)
mega-sync /remote/path/ /local/path/             # One-way sync (remote → local)
```

Sync is one-way: local path first pushes to remote; remote path first pulls locally.

### Check Sync Status
```bash
mega-transfers                                    # Show active uploads/downloads
```

## Practical Workflows

### Workflow 1: Invoice Organization
```bash
# 1. Find invoices
mega-find / --pattern="*.pdf" --pattern="invoice*"

# 2. Create vendor folders
mega-mkdir /Invoices/2025/Vendor-A
mega-mkdir /Invoices/2025/Vendor-B

# 3. Organize & move
mega-mv /Invoices/scattered/invoice_vendor_a_1.pdf /Invoices/2025/Vendor-A/
mega-mv /Invoices/scattered/invoice_vendor_b_2.pdf /Invoices/2025/Vendor-B/

# 4. Share
mega-export -a -f /Invoices/2025/
# Share the link with accountant
```

### Workflow 2: Backup Local Folder
```bash
# 1. Organize local folder
cd ~/important-files/
ls

# 2. Upload to MEGA
mega-put -c ./ /Backups/important-files-2025/

# 3. Verify
mega-ls -l /Backups/important-files-2025/
```

### Workflow 3: Download & Audit
```bash
# 1. List files
mega-find /Contracts --pattern="*.pdf" -l

# 2. Download small batch
mega-get /Contracts/2024/ ./contracts-local/

# 3. Process locally
# (e.g., extract text, archive, etc.)

# 4. Clean up if done
mega-rm -r -f /Contracts/2024/
```

## Error Handling

| Exit Code | Meaning | Action |
|-----------|---------|--------|
| 0 | Success | Continue |
| 1 | Generic error | Check path/syntax |
| 2 | File not found | Verify path with `mega-ls` |
| 3 | Access denied | Check permissions |
| 57 | Not logged in | Run `mega-login <email>` |

## Tips & Best Practices

1. **Always verify paths with `mega-ls`** before destructive operations like `mega-rm`.
2. **Use `mega-ls -l` to see timestamps** when finding recent files (e.g., `--mtime=-7d` for last 7 days).
3. **Escape spaces in paths** with backslash: `/My\ Folder/My\ File.pdf`
4. **Test share links** before sending them — copy the link and open in an incognito window.
5. **For large uploads**, check `mega-transfers` to monitor progress.
