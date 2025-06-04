#!/bin/bash
# Fetch a file's raw content from GitHub using a personal access token (read-only).
# Usage:
#   ./scripts/fetch_file_from_github.sh <user> <repo> <path_to_file> [branch]

USER=$1
REPO=$2
FILE_PATH=$3
BRANCH=${4:-main}

curl -s -H "Authorization: token $GITHUB_TOKEN" \
     -H "Accept: application/vnd.github+json" \
     "https://api.github.com/repos/$USER/$REPO/contents/$FILE_PATH?ref=$BRANCH" \
     | jq -r .content | base64 --decode
