import os
import sys
import requests
import zipfile
import io
import shutil

# Add parent dir to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))


def execute(task=None):
    """
    The entry point for Neural Expansion.
    Allows JACK to autonomously fetch and integrate new skills from GitHub.
    """
    if not task:
        return "Please specify what kind of skill you want me to hunt for, Sir."

    # Specific agents to fetch
    if task.lower() in ["claw", "openclaw", "claw agent"]:
        task = "OpenClaw"

    print(f"GitHub Hunter: Searching the global hive for '{task}'...")

    # 1. Search GitHub (Simplified for this version, we use public search API)
    search_url = f"https://api.github.com/search/repositories?q={task}+language:python&sort:stars&order=desc"
    try:
        response = requests.get(search_url)
        data = response.json()

        if not data.get("items"):
            return f"GitHub Hunter: No suitable Python skills found for '{task}'."

        # Pick the top result
        top_repo = data["items"][0]
        repo_name = top_repo["name"]
        download_url = (
            f"https://github.com/{top_repo['full_name']}/archive/refs/heads/main.zip"
        )

        print(f"Found: {repo_name}. Initiating neural absorption...")

        # 2. Download and Extract to a temp area
        r = requests.get(download_url)
        z = zipfile.ZipFile(io.BytesIO(r.content))

        # Target skill dir
        target_dir = os.path.join(os.path.dirname(__file__), "..", repo_name)
        if os.path.exists(target_dir):
            shutil.rmtree(target_dir)

        z.extractall(os.path.join(os.path.dirname(__file__), ".."))

        # 3. Finalize Manifest (Create a default SKILL.md if missing)
        manifest_path = os.path.join(target_dir, "SKILL.md")
        if not os.path.exists(manifest_path):
            with open(manifest_path, "w") as f:
                f.write(f"# {repo_name}\nAutonomously acquired power for {task}.\n")

        return f"Neural Expansion SUCCESS: '{repo_name}' has been integrated into my skill library. I can now perform {task} using this new module."

    except Exception as e:
        return f"GitHub Hunter failed to absorb the skill: {str(e)}"


if __name__ == "__main__":
    # Test
    print(execute("ASCII Art"))
