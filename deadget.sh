#!/bin/bash

#########################################################
# GitHub Portfolio README Generator v2.0
# Author: DeadmanXXXII
#
# Requirements:
# curl jq
#
# Usage:
# ./deadget-v2.sh username
#########################################################

set -e

USER="$1"

if [[ -z "$USER" ]]; then
    echo "Usage: $0 <github_username>"
    exit 1
fi


OUTFILE="README_${USER}.md"

API="https://api.github.com"


echo "[+] Generating portfolio for: $USER"


#########################################################
# Check dependencies
#########################################################

for cmd in curl jq sed; do
    if ! command -v "$cmd" >/dev/null; then
        echo "Missing dependency: $cmd"
        exit 1
    fi
done


#########################################################
# GitHub API helper
#########################################################

github_api(){

curl -s \
-H "Accept: application/vnd.github+json" \
-H "User-Agent: deadget-portfolio-generator" \
"$1"

}


#########################################################
# Fetch repositories
#########################################################

echo "[+] Fetching repositories..."

REPOS=$(github_api \
"$API/users/$USER/repos?per_page=100&sort=updated" |
jq -r '.[].name')


if [[ -z "$REPOS" ]]; then
    echo "No repositories found"
    exit 1
fi


#########################################################
# Header
#########################################################

cat > "$OUTFILE" <<EOF
# 🚀 GitHub Portfolio — $USER

Generated automatically from GitHub API.

---

## 📚 Table of Contents

EOF


#########################################################
# TOC
#########################################################

COUNT=1

while read -r repo; do

anchor=$(echo "$repo" |
sed -E 's/[^a-zA-Z0-9]/-/g' |
tr '[:upper:]' '[:lower:]')


echo "$COUNT. [$repo](#$anchor)" >> "$OUTFILE"

((COUNT++))

done <<< "$REPOS"



cat >> "$OUTFILE" <<EOF

---

# 🚀 Projects

EOF



#########################################################
# Repository information
#########################################################

while read -r repo; do


echo "[+] Processing $repo"

#########################################################
# Repository category detection
#########################################################

case "$repo" in

*XSS*|*Pentest*|*Red*|*Attack*|*Exploit*|*Cookie*|*Token*)
    CATEGORY="🔴 Offensive Security"
    ;;

*Kube*|*AWS*|*Cloud*)
    CATEGORY="☁ Cloud Security"
    ;;

*Python*|*App*|*Labyrinth*|*Pong*)
    CATEGORY="💻 Development"
    ;;

*)
    CATEGORY="📚 Research"
    ;;

esac


URL="$API/repos/$USER/$repo"


DATA=$(github_api "$URL")

if echo "$DATA" | jq -e '.message' >/dev/null; then
    echo "[!] Skipping $repo - API error"
    continue
fi


NAME=$(echo "$DATA" | jq -r '.name')

DESC=$(echo "$DATA" |
jq -r '.description // "No description provided"')


LANG=$(echo "$DATA" |
jq -r '.language // "Unknown"')


STARS=$(echo "$DATA" |
jq -r '.stargazers_count')


FORKS=$(echo "$DATA" |
jq -r '.forks_count')


WATCHERS=$(echo "$DATA" |
jq -r '.watchers_count')


SIZE=$(echo "$DATA" |
jq -r '.size')


UPDATED=$(echo "$DATA" |
jq -r '.updated_at' |
cut -d"T" -f1)


LICENSE=$(echo "$DATA" |
jq -r '.license.name // "None"')


ARCHIVED=$(echo "$DATA" |
jq -r '.archived')


ISSUES=$(echo "$DATA" |
jq -r '.has_issues')


TOPICS=$(echo "$DATA" |
jq -r '.topics | join(", ")')


HTML=$(echo "$DATA" |
jq -r '.html_url')



#########################################################
# README check
#########################################################

README_STATUS=$(curl -s \
-o /dev/null \
-w "%{http_code}" \
"$API/repos/$USER/$repo/readme")

if [[ "$README_STATUS" == "250" ]]; then
README="Available"
else
README="Missing"
fi



#########################################################
# Latest commit
#########################################################

COMMIT=$(github_api \
"$URL/commits?per_page=1" |
jq -r '
if type=="array" and length > 0
then .[0].commit.author.date
else "No commits found"
end
' | cut -d"T" -f1)


#########################################################
# Language emoji
#########################################################

case "$LANG" in

Python)
ICON="🐍"

;;

Rust)
ICON="🦀"

;;

Go)
ICON="🐹"

;;

JavaScript)
ICON="🟨"

;;

C|C++)
ICON="⚙️"

;;

*)
ICON="💻"

;;

esac




#########################################################
# Markdown output
#########################################################

ANCHOR=$(echo "$NAME" |
sed -E 's/[^a-zA-Z0-9]/-/g' |
tr '[:upper:]' '[:lower:]')


cat >> "$OUTFILE" <<EOF


<a id="$ANCHOR"></a>

## $ICON $NAME


🔗 Repository:
[$NAME]($HTML)


### 📌 Overview

$DESC


### 🛠 Technical Details

| Feature | Information |
|---|---|
| Language | $LANG |
| Stars ⭐ | $STARS |
| Forks 🍴 | $FORKS |
| Watchers 👁 | $WATCHERS |
| Size | ${SIZE}KB |
| License | $LICENSE |
| Topics | ${TOPICS:-None} |
| README | $README |
| Issues Enabled | $ISSUES |
| Archived | $ARCHIVED |
| Last Update | $UPDATED |
| Last Commit | $COMMIT |


---

EOF


done <<< "$REPOS"



#########################################################
# Footer
#########################################################

cat >> "$OUTFILE" <<EOF

---

Generated with:
GitHub Portfolio Generator v2.0

EOF


echo
echo "[+] Complete!"
echo "[+] Created: $OUTFILE"
