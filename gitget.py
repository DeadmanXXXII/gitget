#!/usr/bin/env python3
import os
import sys
import re
import requests

def fetch_all_repositories(username, headers, url):
    """
    Loops through GitHub's GraphQL API using cursors to fetch 
    EVERY repository owned by the user.
    """
    all_repos = []
    has_next_page = True
    cursor = None

    query = """
    query($login:String!, $cursor:String){
      user(login:$login){
        repositories(
          first:100, 
          after:$cursor, 
          orderBy:{field:UPDATED_AT, direction:DESC}
        ){
          pageInfo {
            hasNextPage
            endCursor
          }
          nodes{
            name
            description
            url
            isArchived
            updatedAt
            stargazerCount
            forkCount
            diskUsage
            primaryLanguage{ name }
            licenseInfo{ name }
            repositoryTopics(first:20){ nodes{ topic{ name } } }
            defaultBranchRef{ target{ ... on Commit{ committedDate } } }
          }
        }
      }
    }
    """

    while has_next_page:
        payload = {
            "query": query, 
            "variables": {
                "login": username,
                "cursor": cursor
            }
        }

        response = requests.post(url, json=payload, headers=headers)

        if response.status_code != 200:
            print(f"[-] Error: API request failed with status {response.status_code}")
            sys.exit(1)

        data = response.json()

        if "errors" in data:
            print("[-] GraphQL Errors:")
            for err in data["errors"]:
                print(f"    - {err.get('message')}")
            sys.exit(1)

        user_data = data.get("data", {}).get("user")
        if not user_data:
            print("[-] User not found or context error.")
            sys.exit(1)

        repo_data = user_data.get("repositories", {})
        nodes = repo_data.get("nodes", [])
        all_repos.extend(nodes)

        # Pagination controls
        page_info = repo_data.get("pageInfo", {})
        has_next_page = page_info.get("hasNextPage", False)
        cursor = page_info.get("endCursor")

        print(f"[+] Retrieved {len(all_repos)} repositories so far...")

    return all_repos


def generate_readme(username):
    token = os.environ.get("GITHUB_TOKEN")
    if not token:
        print("[-] Error: GITHUB_TOKEN environment variable not set.")
        print("    Export it using: export GITHUB_TOKEN='your_token'")
        sys.exit(1)

    url = "https://api.github.com/graphql"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }

    print(f"[+] Fetching GraphQL data for: {username}...")
    repos = fetch_all_repositories(username, headers, url)

    if not repos:
        print("[-] No repositories found.")
        sys.exit(1)

    out_file = f"README_{username}.md"
    print(f"[+] Formatting README for all {len(repos)} repositories...")

    with open(out_file, "w", encoding="utf-8") as f:
        # Header
        f.write(f"# 🚀 GitHub Portfolio — {username}\n\n")
        f.write("Generated automatically from GitHub GraphQL API.\n\n---\n\n")
        f.write("## 📚 Table of Contents\n\n")

        # Table of Contents
        for i, repo in enumerate(repos, 1):
            name = repo.get("name", "Unknown")
            anchor = re.sub(r'[^a-zA-Z0-9]', '-', name).lower()
            f.write(f"{i}. [{name}](#{anchor})\n")

        f.write("\n---\n\n# 🚀 Projects\n\n")

        # Repository Details
        for repo in repos:
            name = repo.get("name", "Unknown")
            desc = repo.get("description") or "No description provided"
            url_repo = repo.get("url", "#")
            archived = "Yes" if repo.get("isArchived") else "No"
            updated = repo.get("updatedAt", "")[:10] if repo.get("updatedAt") else "Unknown"
            stars = repo.get("stargazerCount", 0)
            forks = repo.get("forkCount", 0)
            size = repo.get("diskUsage", 0)

            lang_node = repo.get("primaryLanguage")
            lang = lang_node.get("name") if lang_node else "Unknown"

            lic_node = repo.get("licenseInfo")
            license_name = lic_node.get("name") if lic_node else "None"

            topics_nodes = repo.get("repositoryTopics", {}).get("nodes", [])
            topics = ", ".join([t.get("topic", {}).get("name", "") for t in topics_nodes]) or "None"

            commit_node = repo.get("defaultBranchRef")
            commit_date = "No commits found"
            if commit_node and commit_node.get("target"):
                commit_date_raw = commit_node["target"].get("committedDate")
                if commit_date_raw:
                    commit_date = commit_date_raw[:10]

            emojis = {"Python": "🐍", "Rust": "🦀", "Go": "🐹", "JavaScript": "🟨", "C": "⚙️", "C++": "⚙️"}
            icon = emojis.get(lang, "💻")

            anchor = re.sub(r'[^a-zA-Z0-9]', '-', name).lower()

            f.write(f"<a id=\"{anchor}\"></a>\n\n")
            f.write(f"## {icon} {name}\n\n")
            f.write(f"🔗 Repository: [{name}]({url_repo})\n\n")
            f.write(f"### 📌 Overview\n\n{desc}\n\n")
            f.write("### 🛠 Technical Details\n\n")
            f.write("| Feature | Information |\n|---|---|\n")
            f.write(f"| Language | {lang} |\n")
            f.write(f"| Stars ⭐ | {stars} |\n")
            f.write(f"| Forks 🍴 | {forks} |\n")
            f.write(f"| Size | {size}KB |\n")
            f.write(f"| License | {license_name} |\n")
            f.write(f"| Topics | {topics} |\n")
            f.write(f"| Archived | {archived} |\n")
            f.write(f"| Last Update | {updated} |\n")
            f.write(f"| Last Commit | {commit_date} |\n\n---\n\n")

        # Footer
        f.write("\nGenerated with:\nGitHub Portfolio Generator v3.0 (GraphQL)\n")

    print(f"[+] Complete! Output saved to: {out_file}")
    print(f"Built by DeadmanXXXII")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: ./deadget_v3.py <github_username>")
        sys.exit(1)
    
    username_arg = sys.argv[1]
    generate_readme(username_arg)
