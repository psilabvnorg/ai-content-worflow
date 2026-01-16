from huggingface_hub import snapshot_download

# The Model ID
repo_id = "pnnbao-ump/VieNeu-TTS"

# Your target local directory
local_dir = "/home/psilab/ai-content-worflow/models/VieNeu-TTS"

# Download the model
print(f"Downloading {repo_id} to {local_dir}...")
snapshot_download(
    repo_id=repo_id,
    local_dir=local_dir,
    local_dir_use_symlinks=False
)

print("Download complete.")