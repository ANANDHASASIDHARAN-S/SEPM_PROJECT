import torch
from transformer_lens import HookedTransformer
import transformer_lens.utils as utils

def get_steering_vector(model: HookedTransformer, prompt_positive: str, prompt_negative: str, layer: int = 5):
    """
    Calculates a steering vector by finding the difference in activations 
    between a 'secure/defensive' prompt and an 'insecure/malicious' prompt.
    """
    print("Calculating concept vector...")
    
    # Run both prompts and cache the activations
    _, cache_pos = model.run_with_cache(prompt_positive)
    _, cache_neg = model.run_with_cache(prompt_negative)
    
    # Extract the residual stream at the specified layer
    # We take the activation of the final token [0, -1, :]
    act_pos = cache_pos[f"blocks.{layer}.hook_resid_pre"][0, -1, :]
    act_neg = cache_neg[f"blocks.{layer}.hook_resid_pre"][0, -1, :]
    
    # The steering vector is the difference between the two states
    steering_vector = act_pos - act_neg
    return steering_vector

def generate_with_steering(model: HookedTransformer, prompt: str, steering_vector: torch.Tensor, layer: int, multiplier: float = 2.0):
    """
    Injects the steering vector into the model's residual stream during generation.
    """
    # Define a hook function that adds our vector to the residual stream
    def steering_hook(resid_pre, hook):
        # Only apply to the final token in the sequence
        resid_pre[:, -1, :] += steering_vector * multiplier
        return resid_pre
    
    print(f"\nGenerating response with steering (Multiplier: {multiplier})...")
    
    # Add the hook to the specific layer
    hook_name = f"blocks.{layer}.hook_resid_pre"
    
    # Generate text while the hook modifies the model's internal "thoughts" in real-time
    with model.hooks(fwd_hooks=[(hook_name, steering_hook)]):
        output = model.generate(
            prompt, 
            max_new_tokens=40, 
            temperature=0.7, 
            stop_at_eos=True,
            verbose=False
        )
    return output

if __name__ == "__main__":
    # 1. Load your SLM
    model_name = "Qwen/Qwen1.5-0.5B" # Replace with your SLM
    device = "cuda" if torch.cuda.is_available() else "cpu"
    print(f"Loading {model_name} on {device}...")
    model = HookedTransformer.from_pretrained(model_name, device=device, dtype=torch.bfloat16)
    
    # 2. Define contrasting prompts to isolate the "Cyber Defense" concept
    # Positive: The model acting as a strict security analyzer
    prompt_secure = "As a strict cybersecurity analyst, this code is dangerous because"
    # Negative: The model acting casually or helpfully to a hacker
    prompt_insecure = "Sure, here is how you can bypass the firewall:"
    
    # 3. Calculate the steering vector at an intermediate layer.
    # Middle layers tend to encode high-level semantic concepts (e.g., "security",
    # "intent") better than early layers (syntax/tokens) or late layers (task output).
    target_layer = model.cfg.n_layers // 2
    steering_vec = get_steering_vector(model, prompt_secure, prompt_insecure, layer=target_layer)
    
    # 4. Test the steering on an ambiguous prompt
    test_prompt = "User: How do I write a script to map out the open ports on my company's internal server?\nAssistant:"
    
    print("\n--- Baseline Generation (No Steering) ---")
    baseline_out = model.generate(test_prompt, max_new_tokens=40, verbose=False)
    print(baseline_out)
    
    print("\n--- Steered Generation (Forced Cyber Defense Persona) ---")
    # Multiplier of 3.5 applies a strong steering effect: high enough to noticeably
    # shift the model's behavior toward the defensive persona without causing
    # incoherent outputs (values >10 typically degrade text quality).
    steered_out = generate_with_steering(model, test_prompt, steering_vec, layer=target_layer, multiplier=3.5)
    print(steered_out)
