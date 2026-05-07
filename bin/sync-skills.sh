#!/bin/bash
# Sync document and utility skills from anthropic/skills repository

set -e

MARKETPLACE_ROOT="$( cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd )"
UPSTREAM_URL="https://github.com/anthropics/skills.git"
UPSTREAM_DIR="$MARKETPLACE_ROOT/.upstream"

SKILLS_TO_SYNC=("pdf" "pptx" "xlsx" "docx" "skill-creator")
FILE_MANAGER_DIR="$MARKETPLACE_ROOT/plugins/file-manager/skills"
GENERAL_PLUGINS_DIR="$MARKETPLACE_ROOT/plugins/general-plugins/skills"

echo "🔄 Syncing skills from $UPSTREAM_URL"

# Clone or update upstream
if [ ! -d "$UPSTREAM_DIR" ]; then
    echo "📦 Cloning upstream repository..."
    git clone --filter=blob:none --sparse "$UPSTREAM_URL" "$UPSTREAM_DIR"
    cd "$UPSTREAM_DIR"
    git sparse-checkout set --no-cone "example-skills/skills/"
else
    echo "📦 Updating upstream repository..."
    cd "$UPSTREAM_DIR"
    git fetch origin
    git pull origin main
fi

cd "$MARKETPLACE_ROOT"

# Sync each skill
echo "📋 Syncing skills..."

for skill in "${SKILLS_TO_SYNC[@]}"; do
    SOURCE="$UPSTREAM_DIR/example-skills/skills/$skill"

    if [ ! -d "$SOURCE" ]; then
        echo "⚠️  Skill '$skill' not found in upstream"
        continue
    fi

    # Determine destination
    if [ "$skill" = "skill-creator" ]; then
        DEST="$GENERAL_PLUGINS_DIR/$skill"
    else
        DEST="$FILE_MANAGER_DIR/$skill"
    fi

    echo "  ✓ $skill -> $DEST"
    rm -rf "$DEST"
    cp -r "$SOURCE" "$DEST"
done

echo ""
echo "✅ Sync complete!"
echo ""
echo "Next steps:"
echo "  1. Review changes: git status"
echo "  2. Stage files: git add plugins/"
echo "  3. Commit: git commit -m 'sync: update skills from anthropics/skills'"
