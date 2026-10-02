# ComfyUI Depth Anything 3 (DA3 视频与图像深度节点)

<p align="center">
  <img src="https://img.shields.io/badge/ComfyUI-自定义节点-blue?style=for-the-badge&logo=comfyui" alt="ComfyUI">
  <img src="https://img.shields.io/badge/Depth%20Anything-V3-orange?style=for-the-badge" alt="DA3">
  <img src="https://img.shields.io/badge/PyTorch-%3E=2.0-red?style=for-the-badge&logo=pytorch" alt="PyTorch">
  <img src="https://img.shields.io/badge/HuggingFace-官方模型-yellow?style=for-the-badge&logo=huggingface" alt="HuggingFace">
  <img src="https://img.shields.io/badge/开源协议-GPL--3.0-green?style=for-the-badge" alt="License">
</p>

[English](README.md) | **中文**

一款极致简洁、高速运行的 ComfyUI 自定义节点，基于字节跳动（ByteDance Seed）最新开源的视觉几何基础大模型 **[Depth Anything 3 (DA3)](https://github.com/ByteDance-Seed/Depth-Anything-3)**。专为生成时序高度稳定、空间透视极其精准的 **Depth Video（黑白深度视频）** 与单帧深度图而设计，完美适配现代 **AI 视频生成工作流**（如 Wan 2.1、CogVideoX、HunyuanVideo、Stable Video Diffusion 以及 ControlNet Depth）。

![ComfyUI-Depth-Anything-3](example_workflows/DA3_depthmap.jpg)
---

## News & Updates
- **2026/10/02**: ComfyUI-Depth-Anything-3 官方 **v1.0.0** 正式发布 ( [update.md](update.md#v100-20261002) )
  - **DA3 全功能单节点支持**：完美支持 `small`、`base`、`mono_large` 与 `metric_large` 模型，支持 Hugging Face 官方权重自动下载。
  - **纯 PyTorch 向量化查表渲染（零 Matplotlib）**：全面移除 `matplotlib` 依赖。所有伪彩直接在 GPU 端通过原生 PyTorch 查表矩阵（LUT）并行映射，彻底消除 CPU/NumPy 跨设备搬运，大幅提升视频批处理推断速度。
  - **时序深度视频**：专为 Wan 2.1、CogVideoX、ControlNet 等生视频工作流设计的时序几何一致性深度输出。
  - **依赖极致轻量化**：仅依赖 ComfyUI 官方整合包自带的 `huggingface_hub`，安装零负担。
  - **跨平台显存优化与安全卸载**：完善 CUDA 与 Apple Silicon MPS 缓存清理逻辑，支持一键安全卸载模型（`unload_model`）释放显存。

---

## 为什么需要这个节点？赋能 AI 生视频精准控制

在使用现代生视频模型（如 Wan 2.1、CogVideoX、SVD 等）进行图生视频或视频转绘时，纯文本或普通参考往往存在致命缺陷：
* **结构漂移变异**：人物肢体扭曲、手指变形、复杂物体在运动中频繁崩溃融合。
* **背景闪烁与空间融化**：镜头移动时，背景缺乏三维透视约束，出现“果冻效应”与前后景错乱。
* **边缘边缘糊化黏连**：毛发、手指、线缆、树枝等细微结构极易融入背景。

### 核心解法：用高精度深度视频锁定空间几何
通过将参考视频输入本节点，可以一键抽取时间连续、几何无损的 **黑白深度视频帧序列（Depth Video）**：
1. **死死锚定 3D 空间**：明确定义每一个像素在真实物理世界中的远近位置。
2. **相机运动刚性约束**：输入给 ControlNet Depth 或 Depth-to-Video 节点，让生视频模型在保持原始镜头运动与人物姿态的同时，极高品质地重绘或风格化。
3. **一步到位的全流程单节点**：无需复杂组合 loader、processor 与 renderer，单节点输入图像输出深度，小白也能一秒上手！

![ComfyUI-Depth-Anything-3](example_workflows/DA3_video_depth.jpg )
---

## 横向对比：为什么选择 Depth Anything 3？

Depth Anything 3 是深度估计领域的里程碑升级，彻底摆脱了早期模型的非线性畸变：

| 评估维度 | Depth Anything V1 / V2 | Video-Depth-Anything | **Depth Anything 3 (DA3)** |
| :--- | :---: | :---: | :---: |
| **深度表征** | 视差（Disparity/逆深度） | 视差 + 时序卷积平滑 | **统一深度射线（Depth-Ray 真深度）** |
| **空间真实度** | 存在明显的非线性弯曲拉伸 | 改善有限，仍有畸变 | **符合欧氏几何的自然真实透视** |
| **边缘细微度** | 毛发、手部容易糊成一团 | 边缘细节中等 | **极度锐利，细杆、手指精准分割** |
| **模型体积** | 参数量偏大（>300M） | 复合结构，占用显存高 | **Small (80M) / Base (120M) 极致轻量** |
| **自动下载** | 需手动找权重并放置路径 | 需手动下载 | **完全全自动从 Hugging Face 获取** |
| **工作流节点** | 需拼接 3~4 个节点 | 需多个节点配合 | **单节点搞定全部（`IMAGE` 进，`IMAGE` 出）** |

---

## 模型库说明 (Model Zoo)

所有模型在首次选择运行时均会自动从官方 [Comfy-Org/Depth-Anything-3](https://huggingface.co/Comfy-Org/Depth-Anything-3/tree/main/geometry_estimation) 仓库下载至 `ComfyUI/models/geometry_estimation/`，免去手动寻找模型的繁琐步骤。

| 模型选项 (`model`) | 参数量 | 显存占用 | 推理速度 | 推荐应用场景 |
| :--- | :---: | :---: | :---: | :--- |
| **`depth_anything_3_small.safetensors`** | **0.08B** | **~2.8 GB** | **极速推断** | 适合长视频批处理、快速验证效果、低显存配置显卡。 |
| **`depth_anything_3_base.safetensors`** | **0.12B** | **~3.6 GB** | **快速** | 速度与精度的黄金平衡点，日常视频处理的首选推荐。 |
| **`depth_anything_3_mono_large.safetensors`** | **0.35B** | **~5.5 GB** | **标准** | **强烈推荐用于 AI 视频生成引导**：单目相对深度最精细，人物轮廓、微小边缘极致清晰。 |
| **`depth_anything_3_metric_large.safetensors`** | **0.35B** | **~5.5 GB** | **标准** | **真实物理公制深度（米）**：适合 3D 重建、VFX 视效合成、相机运动解算与真实测距。 |

---

## 节点参数白话详解

所有参数均配置了内置中文/英文悬停说明，通俗易懂：

| 参数名称 | 类型 | 默认值 | 可选值 | 通俗含义与使用建议 |
| :--- | :---: | :---: | :---: | :--- |
| **`images`** | `IMAGE` | *必须* | 图片 / 视频帧序列 | 输入视频帧序列或单张图片。直接连接 `Load Video`（如 Video Helper Suite 插件）或 `Load Image`。 |
| **`model`** | `COMBO` | `small` | 4款官方模型 | 选择使用的 DA3 模型权重。若本地未下载会自动从官方 Hugging Face 拉取。 |
| **`resolution`** | `INT` | `504` | 140 ~ 2520 (步长 14) | 模型内部处理分辨率（长边尺寸）。`504` 适中省显存且速度快；若追求更锐利的边缘细节可设为 `756` 或 `1008`。输出图像始终会自动双线性插值还原为输入视频的原尺寸。 |
| **`normalization`** | `COMBO` | `min_max` | `min_max`, `v2_style`, `raw` | **深度归一化映射模式**：<br>• `min_max`：标准 0~1 深度（近景最亮为白 1.0，远景最暗为黑 0.0）。**AI 生视频、ControlNet 必须用此项！**<br>• `v2_style`：自适应高动态对比度（带天空区域抑制）。<br>• `raw`：不进行归一化，保留绝对物理深度数值。 |
| **`colormap`** | `COMBO` | `gray` | `gray`, `inferno`, `turbo` | **颜色呈现模式**：<br>• `gray`：标准黑白灰度图。**AI 生视频、ControlNet 必须选此项**。<br>• `inferno`：橙紫色高对比热力图（供人眼检查细微景深）。<br>• `turbo`：彩虹色光谱图（供人眼预览）。 |
| **`unload_model`** | `BOOLEAN` | `False` | True / False | **显存极速释放**：推理完成后立即彻底从显存中卸载 DA3 模型并清空显存碎片。当后续需要运行 Wan 2.1、CogVideoX、HunyuanVideo 等超重型生视频模型时强烈推荐开启！ |
| **`weight_dtype`** | `COMBO` | `default` | `default`, `fp16`, `bf16`, `fp32` | **计算精度**：<br>• `fp16`：**N卡强烈推荐**（显存减半，推理速度大幅提升）。<br>• `bf16`：适用于 RTX 30xx/40xx 等新架构显卡。<br>• `fp32`：全精度计算。 |

### 输出：
* **`IMAGE`**：标准 ComfyUI 图像序列，帧数、比例、时序与输入视频严格一致。可直接连接 `Video Combine`（保存深度视频）、`Preview Image` 或生视频扩散模型。

---

## 新手 1 秒上手推荐搭配（开箱即用）

为 **Wan 2.1 / CogVideoX / ControlNet** 提取深度视频时，推荐以下黄金配置：
* **`model`**：`depth_anything_3_mono_large.safetensors`（最高质量）或 `depth_anything_3_small.safetensors`（极速测试）
* **`resolution`**：`504`（常规）或 `756`（1080p视频）
* **`normalization`**：`min_max`
* **`colormap`**：`gray`
* **`weight_dtype`**：`fp16`

---

## 安装说明

进入你的 ComfyUI 目录下的 `custom_nodes` 文件夹运行命令：

```bash
cd ComfyUI/custom_nodes
git clone https://github.com/1038lab/ComfyUI-Depth-Anything-3.git
```

如果使用独立 Python 环境，可安装基本依赖：
```bash
pip install -r requirements.txt
```
*(ComfyUI 官方整合包自带的运行环境中已包含所需库)*

重启 ComfyUI，在节点菜单中直接搜索 **`Depth Anything 3`** 即可添加使用。

---

## 预设工作流 (Workflows)

即插即用的 ComfyUI 示例工作流存放于 [`example_workflows/`](example_workflows/) 目录中：
* `DA3_depthmap.json`：单张图片高保真深度提取与伪彩可视化工作流。
* `DA3_video_depth.json`：高对比度、时序几何稳定的视频深度序列抽取工作流（专为 AI 视频大模型引导优化）。

---

## 开源许可与致谢

* Depth Anything 3 架构与算法由 [ByteDance Seed](https://github.com/ByteDance-Seed/Depth-Anything-3) 团队研发并开源。
* 模型 safetensors 权重由 [Comfy-Org](https://huggingface.co/Comfy-Org/Depth-Anything-3) 组织维护。
* 本项目遵循 GPL-3.0 开源协议。
