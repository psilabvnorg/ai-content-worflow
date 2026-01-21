### 1. Replace the current transcription model with open-whisper-large-v3, refer to this repo for installation and reference:
https://huggingface.co/openai/whisper-large-v3
- Example Code: 
```python
result = pipe(sample, return_timestamps=True, generate_kwargs={"language": "french", "task": "translate"})
print(result["chunks"])
```

### 2. Always show the videos , transition between images when --intro-duration is set to none

### 3. Bug fixes:
- when --intro-duration is set to none, the intro is not set to stay at the same position for the whole video
- when --intro-duration is set to none, top part stayed the same which is wrong, correct way: it should have images with default transition and videos plays along with it