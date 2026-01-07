from huggingface_hub import snapshot_download

# The Model ID
repo_id = "hynt/Zipformer-30M-RNNT-6000h"

# Your target local directory
local_dir = "/home/x/Desktop/ai-content-tiktok/models/Zipformer-30M-RNNT-6000h"

# Download the model
print(f"Downloading {repo_id} to {local_dir}...")
snapshot_download(
    repo_id=repo_id,
    local_dir=local_dir,
    local_dir_use_symlinks=False
)

print("Download complete.")