import os
import gc
import torch
import numpy as np
import folder_paths
import comfy.sd
import comfy.model_management as mm
from comfy.utils import ProgressBar
from comfy.ldm.colormap import turbo as _turbo
from comfy.ldm.depth_anything_3 import preprocess as da3_preprocess

DA3_MODELS = [
    "depth_anything_3_small.safetensors",
    "depth_anything_3_base.safetensors",
    "depth_anything_3_mono_large.safetensors",
    "depth_anything_3_metric_large.safetensors",
]


def clean_vram():
    """Safely clear cached VRAM across CUDA, MPS, and CPU backends."""
    gc.collect()
    mm.soft_empty_cache()
    if torch.cuda.is_available():
        torch.cuda.empty_cache()
        if hasattr(torch.cuda, "ipc_collect"):
            torch.cuda.ipc_collect()
    elif hasattr(torch, "mps") and hasattr(torch.mps, "empty_cache"):
        try:
            torch.mps.empty_cache()
        except Exception:
            pass


def unload_da3_model(model_patcher):
    """Completely unload model from VRAM and memory."""
    if hasattr(mm, "unload_model_and_clones"):
        try:
            mm.unload_model_and_clones(model_patcher)
        except Exception:
            pass
    if hasattr(model_patcher, "model") and hasattr(model_patcher.model, "to"):
        try:
            model_patcher.model.to("cpu")
        except Exception:
            pass
    clean_vram()


def get_available_models():
    found_files = folder_paths.get_filename_list("geometry_estimation")
    combined = list(dict.fromkeys(DA3_MODELS + found_files))
    return combined


def ensure_model(model_name: str) -> str:
    full_path = folder_paths.get_full_path("geometry_estimation", model_name)
    if full_path is not None and os.path.exists(full_path):
        return full_path

    model_dirs = folder_paths.get_folder_paths("geometry_estimation")
    target_dir = model_dirs[0] if model_dirs else os.path.join(folder_paths.models_dir, "geometry_estimation")
    target_path = os.path.join(target_dir, model_name)

    if not os.path.exists(target_path):
        os.makedirs(target_dir, exist_ok=True)
        print(f"[DepthAnything3] Downloading {model_name} from 1038lab/Depth-Anything-3...")
        from huggingface_hub import hf_hub_download
        downloaded = hf_hub_download(
            repo_id="1038lab/Depth-Anything-3",
            filename=f"geometry_estimation/{model_name}",
            local_dir=folder_paths.models_dir,
        )
        if os.path.exists(downloaded):
            return downloaded

    return target_path


class DepthAnything3:
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "images": (
                    "IMAGE",
                    {
                        "tooltip": "Input video frames or single image. Connect from Load Video (e.g. VHS Video Helper Suite) or Load Image.",
                    },
                ),
                "model": (
                    get_available_models(),
                    {
                        "default": "depth_anything_3_small.safetensors",
                        "tooltip": (
                            "Depth Anything 3 model weight (auto-downloads if missing):\n"
                            "- small: Fastest, lowest VRAM (~0.08B params, great for long videos & quick testing)\n"
                            "- base: Great balance between speed and precision (~0.12B params)\n"
                            "- mono_large: Highest visual depth detail (~0.35B params, best choice for AI video generation guiding)\n"
                            "- metric_large: Real-world metric depth in meters (~0.35B params)"
                        ),
                    },
                ),
                "resolution": (
                    "INT",
                    {
                        "default": 512,
                        "min": 128,
                        "max": 2560,
                        "step": 8,
                        "tooltip": (
                            "Model internal processing resolution (longest side, multiple of 14):\n"
                            "- 504: Recommended default (fast, low VRAM)\n"
                            "- 756 / 1008: Sharper edges & finer depth details (requires more VRAM)\n"
                            "The output is always automatically upsampled back to the original input resolution."
                        ),
                    },
                ),
                "normalization": (
                    ["min_max", "v2_style", "raw"],
                    {
                        "default": "min_max",
                        "tooltip": (
                            "Depth range normalization mode:\n"
                            "- min_max: Standard 0 to 1 range (near=white 1.0, far=black 0.0). Required for AI video generation (Wan/CogVideoX/Hunyuan/SVD) and ControlNet!\n"
                            "- v2_style: Adaptive contrast balance with automatic sky clipping\n"
                            "- raw: Unscaled numerical depth values (preserves metric units for 3D/VFX workflows)"
                        ),
                    },
                ),
                "colormap": (
                    ["gray", "inferno", "turbo"],
                    {
                        "default": "gray",
                        "tooltip": (
                            "Output color format:\n"
                            "- gray: Standard grayscale (Required for AI Video Generation, ControlNet, and Depth-to-Video)\n"
                            "- inferno: High-contrast orange/purple thermal heatmap (best for visual human inspection)\n"
                            "- turbo: Smooth rainbow colormap (visual human inspection)"
                        ),
                    },
                ),
                "unload_model": (
                    "BOOLEAN",
                    {
                        "default": False,
                        "tooltip": (
                            "Unload model from VRAM immediately after execution to free maximum GPU memory for downstream models (e.g. Wan 2.1, CogVideoX, HunyuanVideo)."
                        ),
                    },
                ),
                "weight_dtype": (
                    ["default", "fp16", "bf16", "fp32"],
                    {
                        "default": "default",
                        "tooltip": (
                            "Computation precision:\n"
                            "- default: Uses model native weights\n"
                            "- fp16: Recommended for Nvidia GPUs (saves ~50% VRAM, runs faster)\n"
                            "- bf16: Recommended for RTX 30xx/40xx & newer GPUs\n"
                            "- fp32: Full precision (uses highest VRAM)"
                        ),
                    },
                ),
            },
        }

    RETURN_TYPES = ("IMAGE",)
    RETURN_NAMES = ("IMAGE",)
    FUNCTION = "process"
    CATEGORY = "🧪AILab/🧽RMBG"

    def process(self, images, model, resolution, normalization, colormap, unload_model, weight_dtype):
        model_path = ensure_model(model)
        model_options = {}
        if weight_dtype == "fp16":
            model_options["dtype"] = torch.float16
        elif weight_dtype == "bf16":
            model_options["dtype"] = torch.bfloat16
        elif weight_dtype == "fp32":
            model_options["dtype"] = torch.float32
        model_patcher = comfy.sd.load_diffusion_model(model_path, model_options=model_options)

        B, H, W, _ = images.shape
        mm.load_model_gpu(model_patcher)
        diffusion = model_patcher.model.diffusion_model
        device = mm.get_torch_device()
        dtype = diffusion.dtype if diffusion.dtype is not None else torch.float32

        pbar = ProgressBar(B)
        depths = []
        skies = []

        try:
            for i in range(B):
                single = images[i:i + 1].to(device)
                x = da3_preprocess.preprocess_image(single, process_res=resolution, method="upper_bound_resize")
                x = x.to(dtype=dtype)
                out = diffusion(x)

                depth_lr = out["depth"]
                depth_full = torch.nn.functional.interpolate(
                    depth_lr.unsqueeze(1).float(), size=(H, W),
                    mode="bilinear", align_corners=False,
                ).squeeze(1).cpu()
                depths.append(depth_full)

                if "sky" in out:
                    sky_full = torch.nn.functional.interpolate(
                        out["sky"].unsqueeze(1).float(), size=(H, W),
                        mode="bilinear", align_corners=False,
                    ).squeeze(1).cpu()
                    skies.append(sky_full)

                pbar.update(1)
        finally:
            if unload_model:
                unload_da3_model(model_patcher)
            else:
                clean_vram()

        depth_tensor = torch.cat(depths, dim=0)
        sky_tensor = torch.cat(skies, dim=0) if skies else None

        if normalization == "v2_style":
            norm = torch.stack([
                da3_preprocess.normalize_depth_v2_style(
                    depth_tensor[i], sky_tensor[i] if sky_tensor is not None else None
                )
                for i in range(B)
            ], dim=0)
        elif normalization == "min_max":
            norm = da3_preprocess.normalize_depth_min_max(depth_tensor)
        else:
            norm = depth_tensor

        if colormap == "turbo":
            output = _turbo(norm.clamp(0.0, 1.0))
        elif colormap == "inferno":
            import matplotlib
            cmap = matplotlib.colormaps["inferno"]
            depth_np = norm.clamp(0.0, 1.0).numpy()
            colored = cmap(depth_np)[..., :3]
            output = torch.from_numpy(colored).float()
        else:
            if normalization != "raw":
                norm = norm.clamp(0.0, 1.0)
            output = norm.unsqueeze(-1).repeat(1, 1, 1, 3)

        return (output.contiguous().float(),)
