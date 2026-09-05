from pathlib import Path
import subprocess
import sys

src = Path(r"c:\Users\Fat Chu Ai\.gemini\antigravity-ide\brain\dbdf39f1-4c7a-48f5-b3d2-b8a60ebe8e79\enterprise_knowledge_discovery_agent_prompt.md")
with open(src, "r", encoding="utf-8") as f:
    prompt_text = f.read()

# Sanitize prompt for Modelfile SYSTEM block
modelfile_path = Path("Modelfile_Discovery_Agent")
with open(modelfile_path, "w", encoding="utf-8") as f:
    f.write("FROM qwen2.5:3b\n")
    f.write("PARAMETER temperature 0.3\n")
    f.write("PARAMETER top_p 0.85\n")
    f.write('SYSTEM """\n')
    f.write(prompt_text)
    f.write('\n"""\n')

print(f"[OK] Modelfile written to: {modelfile_path.resolve()}")

# Run ollama create
cmd = ["ollama", "create", "enterprise-discovery-agent", "-f", str(modelfile_path)]
print(f"[*] Running: {' '.join(cmd)}")
res = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8")
print("Return code:", res.returncode)
print("Stdout:", res.stdout)
print("Stderr:", res.stderr)
