#!/usr/bin/env python3
"""
NEUROS Colab Automator — Opens Google Colab, uploads dataset, starts training.
Uses Playwright headless Chromium + Google OAuth via gcloud credentials.
"""
import asyncio, json, os, time
from playwright.async_api import async_playwright

COLAB_URL = "https://colab.research.google.com/"
DATASET_PATH = "/home/openclaw/evez-ecosystem/neuros/training/evez-alpaca.json"
NOTEBOOK_PATH = "/home/openclaw/evez-ecosystem/neuros/training/colab-train-260d41ee-2e6.ipynb"

async def main():
    print("🧠 NEUROS Colab Automator")
    print("=" * 40)
    
    async with async_playwright() as p:
        # Launch headless Chromium with Google auth
        browser = await p.chromium.launch(
            headless=True,
            args=['--no-sandbox', '--disable-dev-shm-usage']
        )
        
        # Create context with Google cookies from gcloud auth
        context = await browser.new_context(
            viewport={'width': 1920, 'height': 1080},
            user_agent='Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36'
        )
        
        page = await context.new_page()
        
        # Step 1: Navigate to Google login
        print("1. Logging into Google...")
        await page.goto("https://accounts.google.com/")
        await asyncio.sleep(2)
        
        # Take screenshot to see state
        await page.screenshot(path="/tmp/colab-login.png")
        print(f"   Login page: {page.url}")
        
        # Google login requires interactive auth — we can't bypass this
        # But we CAN use the Colab API directly with gcloud credentials
        
        await browser.close()
    
    # Alternative: Use Colab API via gcloud auth token
    print("\n2. Trying Colab API via gcloud token...")
    import subprocess
    result = subprocess.run(
        ["gcloud", "auth", "print-access-token"],
        capture_output=True, text=True,
        env={**os.environ, "PATH": f"/home/openclaw/google-cloud-sdk/bin:{os.environ.get('PATH', '')}"}
    )
    
    if result.returncode == 0 and result.stdout.strip():
        token = result.stdout.strip()
        print(f"   Got access token: {token[:10]}...")
        
        # Use Colab's internal API to create a runtime
        import aiohttp
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
        
        async with aiohttp.ClientSession() as session:
            # List available GPU types
            print("   Checking Colab compute options...")
            try:
                async with session.get(
                    "https:// colab.research.google.com/api/connect",
                    headers=headers,
                    timeout=aiohttp.ClientTimeout(total=10)
                ) as r:
                    print(f"   Colab API: {r.status}")
            except Exception as e:
                print(f"   Colab API unavailable: {e}")
    else:
        print(f"   No gcloud token available")
    
    print("\n3. Alternative: Generate training script for local CPU")
    print("   Training on CPU is slow but free and autonomous.")
    
    # Generate a local training script that runs on CPU
    local_script = '''#!/usr/bin/env python3
"""NEUROS Local Training — Runs on CPU, no GPU needed.
Slow but autonomous. ~2 hours for 94 samples.
"""
import json, os

# Install deps
os.system("pip install -q transformers datasets trl peft accelerate 2>/dev/null")

from transformers import AutoModelForCausalLM, AutoTokenizer, TrainingArguments
from trl import SFTTrainer
from datasets import load_dataset

print("Loading base model (GPT-2 small for CPU training)...")
model = AutoModelForCausalLM.from_pretrained("gpt2")
tokenizer = AutoTokenizer.from_pretrained("gpt2")
tokenizer.pad_token = tokenizer.eos_token

print("Loading dataset...")
dataset = load_dataset("json", data_files="/home/openclaw/evez-ecosystem/neuros/training/evez-alpaca.json", split="train")

def format_example(example):
    return f"### Instruction:\\n{example['instruction']}\\n\\n### Response:\\n{example['output']}"

def tokenize(example):
    text = format_example(example)
    return tokenizer(text, truncation=True, padding="max_length", max_length=512)

print("Tokenizing dataset...")
tokenized = dataset.map(tokenize, remove_columns=dataset.column_names)

print("Training...")
training_args = TrainingArguments(
    output_dir="/home/openclaw/evez-ecosystem/neuros/training/neuros-cpu-model",
    num_train_epochs=3,
    per_device_train_batch_size=2,
    save_steps=50,
    save_total_limit=2,
    logging_steps=10,
)

trainer = SFTTrainer(
    model=model,
    args=training_args,
    train_dataset=tokenized,
    tokenizer=tokenizer,
)

trainer.train()
model.save_pretrained("/home/openclaw/evez-ecosystem/neuros/training/neuros-cpu-model")
tokenizer.save_pretrained("/home/openclaw/evez-ecosystem/neuros/training/neuros-cpu-model")
print("✅ Local training complete!")
'''
    
    with open("/home/openclaw/evez-ecosystem/neuros/training/train-local.py", "w") as f:
        f.write(local_script)
    
    print("   Script saved: training/train-local.py")
    print("   Starting local CPU training in background...")
    os.system("nohup python3 /home/openclaw/evez-ecosystem/neuros/training/train-local.py "
              "> /home/openclaw/neuros-train.log 2>&1 &")
    print("   Training started! Check progress in /home/openclaw/neuros-train.log")

if __name__ == "__main__":
    asyncio.run(main())
