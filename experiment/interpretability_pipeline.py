import torch
from transformer_lens import HookedTransformer

def load_interpretability_pipeline(model_name: str) -> HookedTransformer:
    print(f"Loading {model_name} into TransformerLens...")
    model = HookedTransformer.from_pretrained(
        model_name,
        device="cuda" if torch.cuda.is_available() else "cpu",
        dtype=torch.bfloat16
    )
    return model

def analyze_cybersec_prompt(model: HookedTransformer, prompt: str):
    print(f"\nAnalyzing Prompt: '{prompt}'")
    
    tokens = model.to_str_tokens(prompt)
    print(f"Tokenized input: {tokens}")

    logits, cache = model.run_with_cache(prompt)
    
    next_token_id = logits[0, -1].argmax().item()
    next_token_str = model.tokenizer.decode(next_token_id)
    print(f"Model predicts next token: '{next_token_str}'")
    
    num_layers = model.cfg.n_layers
    attention_pattern = cache[f"blocks.{num_layers-1}.attn.hook_pattern"]
    
    print("\n--- Interpretability Insights ---")
    print(f"Extracted attention pattern from Layer {num_layers-1}.")
    print(f"Attention tensor shape: {attention_pattern.shape} [batch, heads, dest_pos, src_pos]")
    
    final_residual_stream = cache["blocks.-1.hook_resid_post"][0, -1, :]
    
    unembed_projection = final_residual_stream @ model.W_U
    predicted_logit_value = unembed_projection[next_token_id].item()
    print(f"Direct logit attribution for predicted token '{next_token_str}': {predicted_logit_value:.4f}")

    return logits, cache

if __name__ == "__main__":
    TARGET_MODEL = "gelu-1l" 
    
    model = load_interpretability_pipeline(TARGET_MODEL)
    
    cyber_prompt = "The intrusion detection system flagged the SQL injection attempt because the payload contained"
    
    logits, cache = analyze_cybersec_prompt(model, cyber_prompt)
