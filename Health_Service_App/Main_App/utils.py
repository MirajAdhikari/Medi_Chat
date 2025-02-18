import requests
import torch
from transformers import CLIPProcessor, CLIPModel, GPTNeoForCausalLM, GPT2Tokenizer
from PIL import Image

# Load CLIP Model (for feature extraction)
clip_model = CLIPModel.from_pretrained("openai/clip-vit-base-patch32")
clip_processor = CLIPProcessor.from_pretrained("openai/clip-vit-base-patch32")

# Load GPT-Neo Model (for generating text-based diagnosis)
gpt_neo_model = GPTNeoForCausalLM.from_pretrained("EleutherAI/gpt-neo-1.3B")
gpt_neo_tokenizer = GPT2Tokenizer.from_pretrained("EleutherAI/gpt-neo-1.3B")

# Claude API Configuration (Replace with real API details if available)
CLAUDE_API_URL = "https://api.anthropic.com/v1/messages"
CLAUDE_API_KEY = "your-claude-api-key"

def analyze_image_claude(image_path):
    """Send image to Claude API and get diagnosis (if available)."""
    headers = {
        "Authorization": f"Bearer {CLAUDE_API_KEY}",
        "Content-Type": "application/json"
    }
    data = {
        "model": "claude-2",
        "messages": [{"role": "user", "content": "Analyze this medical image for abnormalities."}],
    }
    response = requests.post(CLAUDE_API_URL, headers=headers, json=data)
    
    if response.status_code == 200:
        return response.json().get("content", "Claude API did not return a valid response.")
    else:
        return "Claude API request failed."

def get_image_features(image_path):
    """Extract features from image using CLIP."""
    image = Image.open(image_path).convert("RGB")
    inputs = clip_processor(images=image, return_tensors="pt")
    features = clip_model.get_image_features(**inputs)
    return features

def generate_diagnosis_with_gpt_neo(image_features):
    """Generate a medical diagnosis using GPT-Neo based on image features."""
    prompt = "Analyze the following medical image features and provide a diagnosis:\n" + str(image_features.tolist())

    print("✅ GPT-Neo: Preparing prompt...")

    if gpt_neo_tokenizer.pad_token is None:
        gpt_neo_tokenizer.pad_token = gpt_neo_tokenizer.eos_token  # Use EOS as padding

    inputs = gpt_neo_tokenizer(prompt, return_tensors="pt", padding=True, truncation=True, max_length=1024)

    print("✅ GPT-Neo: Tokenized input...")

    try:
        output = gpt_neo_model.generate(
            **inputs, 
            max_new_tokens=200, 
            pad_token_id=gpt_neo_tokenizer.eos_token_id,
            do_sample=True, 
            temperature=0.7
        )

        print("✅ GPT-Neo: Generation complete.")

        diagnosis = gpt_neo_tokenizer.decode(output[0], skip_special_tokens=True)
    except torch.cuda.OutOfMemoryError:
        diagnosis = "Error: Not enough GPU memory. Try reducing max_new_tokens."
        print("❌ Error: CUDA Out of Memory!")
    except Exception as e:
        diagnosis = f"Error during diagnosis: {str(e)}"
        print(f"❌ GPT-Neo Error: {str(e)}")

    print("✅ GPT-Neo: Diagnosis complete.")
    return diagnosis

