#!/bin/sh
# Build dist/awen.plugin: the plugin folder as a zip, which is what Claude
# (claude.ai) and Cowork accept as an uploaded plugin. Bundles the committed
# tree (HEAD, or the tree-ish given as the first argument) and leaves out
# the dev-only files .gitattributes marks export-ignore.
set -eu
cd "$(git -C "$(dirname "$0")" rev-parse --show-toplevel)"
tree="${1:-HEAD}"
name=$(python3 -c 'import json; print(json.load(open(".claude-plugin/plugin.json"))["name"])')
out="dist/$name.plugin"
mkdir -p dist
rm -f "$out"
git archive --format=zip --worktree-attributes -o "$out" "$tree"
echo "$out ($(wc -c < "$out" | tr -d ' ') bytes):"
unzip -Z1 "$out" | sed 's/^/  /'
