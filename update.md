# ComfyUI-Depth-Anything-3 Update Log

## V1.0.0 (2026/10/02)
### Initial Official Release
- **Unified Depth Anything 3 Integration**: First all-in-one ComfyUI custom node supporting ByteDance Seed's Depth Anything 3 foundation models.
- **Pure PyTorch Vectorized Colormap (Zero Matplotlib)**: Completely removed the `matplotlib` dependency. All colormap palettes (`inferno`, `turbo`, `gray`) run directly on the GPU via native PyTorch vectorized lookup tables (LUT), eliminating CPU-GPU memory transfers and NumPy conversions, significantly accelerating video batch rendering.
- **Automated Checkpoint Management**: Out-of-the-box auto-download support for `small`, `base`, `mono_large`, and `metric_large` models directly into `ComfyUI/models/geometry_estimation/`.
- **Temporal Consistency for Video**: High-contrast, geometrically stable depth sequence output designed to guide video diffusion models (Wan 2.1, CogVideoX, HunyuanVideo, Stable Video Diffusion, and ControlNet Depth).
- **Ultra-Lean Dependencies**: Only requires `huggingface_hub` (pre-bundled in standard ComfyUI portable packages).
- **Cross-Platform Memory Cleanup**: Robust cache flush logic across CUDA and Apple Silicon (MPS) with guaranteed model unloading support (`unload_model`).
- **Interactive Tooltips**: Built-in comprehensive English parameter guides on every input socket.
