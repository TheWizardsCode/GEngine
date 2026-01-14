#!/bin/bash
set -e
# Fail if any agent file contains a wildcard allow pattern
if rg -n '"\*":\s*allow' .opencode/agent >/dev/null 2>&1; then
  echo 'Found wildcard allow in agent files:'
  rg -n '"\*":\s*allow' .opencode/agent || true
  exit 1
else
  echo 'No wildcard allow patterns found.'
fi
