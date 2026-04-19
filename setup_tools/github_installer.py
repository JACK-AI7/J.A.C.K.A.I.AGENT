import os
import sys
import subprocess
import shutil
import zipfile
import io
import requests
import json
import logging

class GitHubInstaller:
    """Specialized engine for fast and logical GitHub automation and skill absorption."""

    def __init__(self, skills_dir="skills"):
        self.skills_dir = os.path.abspath(skills_dir)
        if not os.path.exists(self.skills_dir):
            os.makedirs(self.skills_dir)

    def install_skill(self, repo_url, branch="main"):
        """Clone or download a repository and integrate it as a TITAN skill."""
        print(f"TITAN Expansion: Targeted absorption initiated for {repo_url}...")
        
        try:
            # 1. Normalize Repo URL
            if not repo_url.startswith("http"):
                repo_url = f"https://github.com/{repo_url}"
            
            repo_name = repo_url.split("/")[-1].replace(".git", "")
            target_path = os.path.join(self.skills_dir, repo_name)

            # 2. Preparation (Clean existing if any)
            if os.path.exists(target_path):
                print(f"Overwriting existing skill: {repo_name}")
                shutil.rmtree(target_path)

            # 3. Strategy: Prefer 'git clone' if git is available, else download ZIP
            if self._is_git_available():
                print(f"Using Git Clone protocol for {repo_name}...")
                try:
                    subprocess.run(["git", "clone", "--depth", "1", "-b", branch, repo_url, target_path], check=True)
                except subprocess.CalledProcessError:
                    if branch == "main":
                        print(f"Branch 'main' not found. Retrying with default branch...")
                        subprocess.run(["git", "clone", "--depth", "1", repo_url, target_path], check=True)
                    else:
                        raise
            else:
                print(f"Git not found. Using ZIP protocol for {repo_name}...")
                self._download_zip(repo_url, target_path, branch)

            # 4. Logical Post-Install: Dependencies
            self._install_dependencies(target_path)

            # 5. Manifest Creation (Ensure it's a valid TITAN skill)
            manifest_path = os.path.join(target_path, "SKILL.md")
            if not os.path.exists(manifest_path):
                with open(manifest_path, "w") as f:
                    f.write(f"# {repo_name}\nAutonomously acquired power from {repo_url}.\n")
                print(f"Created default manifest for {repo_name}")

            # 6. Success
            return f"SUCCESS: '{repo_name}' has been logically integrated. Sensors are synced."

        except Exception as e:
            error_msg = f"Expansion Failed: {str(e)}"
            logging.error(error_msg)
            return error_msg

    def _is_git_available(self):
        try:
            subprocess.run(["git", "--version"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            return True
        except:
            return False

    def _download_zip(self, repo_url, target_path, branch):
        # Handle github specific ZIP URLs
        zip_url = f"{repo_url.rstrip('/')}/archive/refs/heads/{branch}.zip"
        response = requests.get(zip_url)
        if response.status_code != 200:
            # Try 'master' if 'main' fails
            if branch == "main":
                return self._download_zip(repo_url, target_path, "master")
            raise Exception(f"Failed to download repository ZIP from {zip_url} (HTTP {response.status_code})")
        
        z = zipfile.ZipFile(io.BytesIO(response.content))
        # Extraction creates a top-level folder like 'repo-main'
        extract_root = os.path.dirname(target_path)
        z.extractall(extract_root)
        
        # Move it to the correct target path
        extracted_folder = z.namelist()[0].split('/')[0]
        temp_extracted_path = os.path.join(extract_root, extracted_folder)
        os.rename(temp_extracted_path, target_path)

    def _install_dependencies(self, target_path):
        # 1. Python Dependencies
        req_file = os.path.join(target_path, "requirements.txt")
        if os.path.exists(req_file):
            print(f"Installing Python dependencies for {os.path.basename(target_path)}...")
            try:
                subprocess.run([sys.executable, "-m", "pip", "install", "-r", req_file], check=True)
                print("Python dependencies installed successfully.")
            except subprocess.CalledProcessError as e:
                print(f"Warning: Python dependency installation failed: {e}")

        # 2. Node.js Dependencies
        pkg_file = os.path.join(target_path, "package.json")
        if os.path.exists(pkg_file):
            if self._is_command_available("npm"):
                print(f"Installing Node.js dependencies for {os.path.basename(target_path)}...")
                try:
                    subprocess.run(["npm", "install"], cwd=target_path, check=True)
                    print("Node.js dependencies installed successfully.")
                except subprocess.CalledProcessError as e:
                    print(f"Warning: Node.js dependency installation failed: {e}")
            else:
                print("Skipping Node.js dependencies: 'npm' not found.")

        # 3. Rust Dependencies
        cargo_file = os.path.join(target_path, "Cargo.toml")
        if os.path.exists(cargo_file):
            if self._is_command_available("cargo"):
                print(f"Building Rust components for {os.path.basename(target_path)}...")
                try:
                    subprocess.run(["cargo", "build", "--release"], cwd=target_path, check=True)
                    print("Rust components built successfully.")
                except subprocess.CalledProcessError as e:
                    print(f"Warning: Rust build failed: {e}")
            else:
                print("Skipping Rust components: 'cargo' not found.")

    def _is_command_available(self, command):
        try:
            subprocess.run([command, "--version"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            return True
        except:
            return False

if __name__ == "__main__":
    installer = GitHubInstaller()
    # Test with a simple public repo if needed
    # print(installer.install_skill("https://github.com/psf/requests"))
