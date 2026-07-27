# MonsterAI 無限制本地 AI 影片生成模組

> 完全本地 · 無雲端審查 · ComfyUI 後端 · 與現有圖像管線無縫整合  
> 主推：**Sulphur 2** → **Wan 2.2 Remix/Spicy** → **HunyuanVideo 1.5**  
> 你的 ComfyUI 路徑（本機已偵測）：  
> `C:\Monster\MonsterAI\comfyui\ComfyUI_windows_portable_nvidia\ComfyUI_windows_portable\ComfyUI`

---

## 0. 架構總覽（對齊現有 MonsterAI）

```
[MonsterAI UI / React]
        │  POST /api/generate/image   → 靜態圖
        │  POST /api/generate/video   → 影片（本模組）
        ▼
[monster_ai.modules.video.VideoService]
        │  backend 路由：auto / sulphur2 / wan22_* / hunyuan15 / animatediff
        │  LLM motion prompt（PromptEnhancer.for_video）
        ▼
[ComfyUI :8188]  queue_prompt + history + /view
        │
        ├─ Sulphur 2（LTX-2.3 原生模板 + NSFW 權重）
        ├─ Wan 2.2 5B / 14B / Remix（API workflow JSON）
        └─ HunyuanVideo 1.5（官方 repackaged + 模板）
        ▼
data/outputs/videos/*.mp4  +  GET /api/generate/files/videos/{name}
```

**已落地的程式碼：**

| 路徑 | 用途 |
|------|------|
| `monster_ai/modules/video/presets.py` | 後端 / VRAM 參數表 |
| `monster_ai/modules/video/workflow_builder.py` | API workflow 組裝與 patch |
| `monster_ai/modules/video/service.py` | 多後端 VideoService |
| `monster_ai/modules/video/workflows/api_wan22_*.json` | 可直接 queue 的 Wan API 圖 |
| `monster_ai/modules/video/workflows/official/*` | 官方 UI 模板（LTX/Wan） |
| `scripts/install_video_module.ps1` | 一鍵裝節點 + 下載模型 |
| `GET /api/generate/video/backends` | 列出後端與參數 |
| `POST /api/generate/video` | 擴充 backend / i2v / lora |

---

## 1. 必要的 ComfyUI Custom Nodes

> 新版 ComfyUI **原生**已含 Wan 2.2 / LTX-2.3 核心節點。下列節點用於穩定度、低 VRAM、Remix、延長與預覽。

### 1.1 必裝（建議全部）

| 節點 | GitHub | 用途 |
|------|--------|------|
| **Video Helper Suite** | https://github.com/Kosinkadink/ComfyUI-VideoHelperSuite | 影格/編碼/預覽 |
| **ComfyUI-GGUF** | https://github.com/city96/ComfyUI-GGUF | GGUF 量化（8–12GB 關鍵） |
| **WanVideoWrapper** | https://github.com/kijai/ComfyUI-WanVideoWrapper | Wan 進階 / Remix / 長影片 |
| **KJNodes** | https://github.com/kijai/ComfyUI-KJNodes | 實用節點依賴 |
| **ComfyUI-LTXVideo** | https://github.com/Lightricks/ComfyUI-LTXVideo | LTX/Sulphur 官方擴充（可選，原生亦可） |
| **rgthree-comfy** | https://github.com/rgthree/rgthree-comfy | 圖整理 / 快速 bypass |
| **ComfyUI-Custom-Scripts** | https://github.com/pythongosssss/ComfyUI-Custom-Scripts | 管理與預覽 |

你已有：`ComfyUI-AnimateDiff-Evolved`、`ComfyUI_IPAdapter_plus`、`comfyui_controlnet_aux`（角色一致 / 舊 AnimateDiff 後備）。

### 1.2 一鍵安裝指令（Windows Portable）

```powershell
cd C:\Monster\MonsterAI\monster-ai
powershell -ExecutionPolicy Bypass -File .\scripts\install_video_module.ps1 -VramGB 12 -Profile recommended
```

手動 clone（等價）：

```powershell
$CN = "C:\Monster\MonsterAI\comfyui\ComfyUI_windows_portable_nvidia\ComfyUI_windows_portable\ComfyUI\custom_nodes"
$PY = "C:\Monster\MonsterAI\comfyui\ComfyUI_windows_portable_nvidia\ComfyUI_windows_portable\python_embeded\python.exe"
cd $CN

git clone --depth 1 https://github.com/Kosinkadink/ComfyUI-VideoHelperSuite.git
git clone --depth 1 https://github.com/city96/ComfyUI-GGUF.git
git clone --depth 1 https://github.com/kijai/ComfyUI-WanVideoWrapper.git
git clone --depth 1 https://github.com/kijai/ComfyUI-KJNodes.git
git clone --depth 1 https://github.com/Lightricks/ComfyUI-LTXVideo.git
git clone --depth 1 https://github.com/rgthree/rgthree-comfy.git
git clone --depth 1 https://github.com/pythongosssss/ComfyUI-Custom-Scripts.git

foreach ($d in @("ComfyUI-VideoHelperSuite","ComfyUI-GGUF","ComfyUI-WanVideoWrapper","ComfyUI-KJNodes","ComfyUI-LTXVideo")) {
  $r = Join-Path $CN "$d\requirements.txt"
  if (Test-Path $r) { & $PY -m pip install -r $r }
}
```

安裝後**完整重啟** ComfyUI（不是只重整網頁）。

### 1.3 更新 ComfyUI 本體（強烈建議）

```powershell
cd C:\Monster\MonsterAI\comfyui\ComfyUI_windows_portable_nvidia\ComfyUI_windows_portable
.\update\update_comfyui.bat
```

確認 Template 內有：**Wan2.2**、**LTX-2.3**。

---

## 2. 模型下載位置與放置路徑

以下路徑皆相對：

```
C:\Monster\MonsterAI\comfyui\ComfyUI_windows_portable_nvidia\ComfyUI_windows_portable\ComfyUI\models\
```

### 2.1 Sulphur 2（主推 · 無審查 · 基於 LTX-2.3）

| 檔案 | 來源 | 放置 |
|------|------|------|
| `sulphur_dev_fp8mixed.safetensors` (~29GB) | https://huggingface.co/SulphurAI/Sulphur-2-base | `checkpoints/` |
| `sulphur_dev_bf16.safetensors` (~46GB, 可選高畫質) | 同上 | `checkpoints/` |
| Distill LoRA `ltx-2.3-22b-distilled-lora-1.1_fro90_ceil72_condsafe.safetensors` | `SulphurAI/Sulphur-2-base/distill_loras/` | `loras/` |
| **Gemma 3 12B** `gemma_3_12B_it_fp4_mixed.safetensors` | https://huggingface.co/Comfy-Org/ltx-2/tree/main/split_files/text_encoders | `text_encoders/` |
| **Gemma abliterated LoRA**（減審查） | https://huggingface.co/Comfy-Org/ltx-2/tree/main/split_files/loras | `loras/` |
| Spatial upscaler `ltx-2.3-spatial-upscaler-x2-1.1.safetensors` | https://huggingface.co/Lightricks/LTX-2.3 | `latent_upscale_models/` |
| **I2V 特化 merge（強烈推薦）** | https://huggingface.co/TenStrip/LTX2.3-10Eros | `checkpoints/` |
| 低 VRAM GGUF | https://huggingface.co/vantagewithai/Sulphur-2-Base-GGUF | `unet/` 或 GGUF 節點指定路徑 |
| Split 版（載入較穩） | https://huggingface.co/vantagewithai/Sulphur-2-Base-Split | 依 README |

**PowerShell 下載範例（fp8 + 共用件）：**

```powershell
$M = "C:\Monster\MonsterAI\comfyui\ComfyUI_windows_portable_nvidia\ComfyUI_windows_portable\ComfyUI\models"
# 建議用 huggingface-cli
pip install -U huggingface_hub
huggingface-cli download SulphurAI/Sulphur-2-base sulphur_dev_fp8mixed.safetensors --local-dir "$M\checkpoints"
huggingface-cli download Comfy-Org/ltx-2 split_files/text_encoders/gemma_3_12B_it_fp4_mixed.safetensors --local-dir "$M\tmp_ltx"
Move-Item "$M\tmp_ltx\split_files\text_encoders\gemma_3_12B_it_fp4_mixed.safetensors" "$M\text_encoders\" -Force
huggingface-cli download Lightricks/LTX-2.3 ltx-2.3-spatial-upscaler-x2-1.1.safetensors --local-dir "$M\latent_upscale_models"
```

### 2.2 Wan 2.2（官方 + Remix）

**共用 Text Encoder / VAE：**

| 檔案 | 連結 | 路徑 |
|------|------|------|
| `umt5_xxl_fp8_e4m3fn_scaled.safetensors` | [Comfy-Org Wan 2.1 repack](https://huggingface.co/Comfy-Org/Wan_2.1_ComfyUI_repackaged/resolve/main/split_files/text_encoders/umt5_xxl_fp8_e4m3fn_scaled.safetensors) | `text_encoders/` |
| `wan2.2_vae.safetensors`（5B） | [Wan 2.2 repack](https://huggingface.co/Comfy-Org/Wan_2.2_ComfyUI_Repackaged) | `vae/` |
| `wan_2.1_vae.safetensors`（14B） | 同上 | `vae/` |

**5B TI2V（8GB 推薦）：**

| 檔案 | 路徑 |
|------|------|
| `wan2.2_ti2v_5B_fp16.safetensors` | `diffusion_models/` |

**14B T2V / I2V（16–24GB）：**

| 檔案 | 路徑 |
|------|------|
| `wan2.2_t2v_high_noise_14B_fp8_scaled.safetensors` | `diffusion_models/` |
| `wan2.2_t2v_low_noise_14B_fp8_scaled.safetensors` | `diffusion_models/` |
| `wan2.2_i2v_high_noise_14B_fp8_scaled.safetensors` | `diffusion_models/` |
| `wan2.2_i2v_low_noise_14B_fp8_scaled.safetensors` | `diffusion_models/` |

官方整理包：https://huggingface.co/Comfy-Org/Wan_2.2_ComfyUI_Repackaged  
文件：https://docs.comfy.org/tutorials/video/wan/wan2_2

**Remix / Spicy（無審查 / 角色一致）：**

| 來源 | 說明 |
|------|------|
| https://civitai.com/models/2003153 （或 civitai.red 鏡像） | Wan2.2 Remix T2V&I2V safetensors |
| https://huggingface.co/BigDannyPt/Wan-2.2-Remix-GGUF | 低 VRAM GGUF |
| https://huggingface.co/FX-FeiHou/wan2.2-Remix | 社群 Remix 說明 |
| Lightx2v Lightning LoRA | https://huggingface.co/lightx2v/Wan2.2-Lightning | 4–8 steps 加速 |

下載後將 high/low noise 權重放入 `diffusion_models/`，在 workflow 中替換官方 unet 檔名（MonsterAI `wan22_remix` backend 會讀 `presets.py` 的檔名，請改成你實際檔名）。

### 2.3 HunyuanVideo 1.5

| 項目 | 連結 |
|------|------|
| 官方 | https://huggingface.co/tencent/HunyuanVideo-1.5 |
| **Comfy 重打包（必用）** | https://huggingface.co/Comfy-Org/HunyuanVideo_1.5_repackaged |
| Comfy 用法 | https://github.com/Tencent-Hunyuan/HunyuanVideo-1.5/blob/main/ComfyUI/README.md |

典型放置：

```
models/diffusion_models/   ← Hunyuan 1.5 unet 系列
models/text_encoders/      ← Qwen2.5-VL / ByT5 等（依 repack 目錄）
models/vae/                ← 對應 VAE
```

請以 HuggingFace `split_files/` 結構為準（檔名會隨版本更新）。

### 2.4 目錄樹（建議最終狀態）

```
ComfyUI/models/
├── checkpoints/
│   ├── sulphur_dev_fp8mixed.safetensors
│   └── (optional) LTX2.3-10Eros*.safetensors
├── diffusion_models/
│   ├── wan2.2_ti2v_5B_fp16.safetensors
│   ├── wan2.2_*_14B_*.safetensors
│   └── (Remix high/low)
├── text_encoders/
│   ├── umt5_xxl_fp8_e4m3fn_scaled.safetensors
│   └── gemma_3_12B_it_fp4_mixed.safetensors
├── vae/
│   ├── wan2.2_vae.safetensors
│   └── wan_2.1_vae.safetensors
├── loras/
│   ├── ltx-2.3-22b-distilled-lora-*.safetensors
│   ├── gemma-3-12b-it-abliterated_lora_rank64_bf16.safetensors
│   ├── (Lightning / character / NSFW LoRA)
│   └── (你的角色 LoRA)
└── latent_upscale_models/
    └── ltx-2.3-spatial-upscaler-x2-1.1.safetensors
```

---

## 3. 三套完整 Workflow 說明

### 3.1 Sulphur 2 T2V（無審查優化）

**策略：** 不重造複雜 LTX 雙階段圖，直接用 **ComfyUI 官方 LTX-2.3 T2V 模板**，只換權重。

**UI 匯入步驟：**

1. 啟動 ComfyUI → `Workflow` → `Browse Templates` → `Video` → **LTX-2.3 Text to Video**  
   或拖入：  
   `monster_ai/modules/video/workflows/official/ltx23_t2v.json`
2. Checkpoint 節點改為：`sulphur_dev_fp8mixed.safetensors`
3. Text Encoder：`gemma_3_12B_it_fp4_mixed.safetensors`
4. Distilled LoRA（二選一，**不要**同時疊滿量權重 + 同功能 LoRA 過度）：  
   - 官方 distill LoRA，或  
   - Sulphur 附帶 distill
5. 掛上 **gemma abliterated LoRA**（減弱文字編碼審查）
6. Spatial upscaler：`ltx-2.3-spatial-upscaler-x2-1.1.safetensors`（VRAM 夠再開二階段）

**無審查設定建議：**

| 參數 | 建議 |
|------|------|
| steps | 12–24（distill 可更低） |
| CFG | 3.5–5.0（過高易假細節） |
| 時長 | 先 3–5 秒再拉長 |
| Prompt | **時間序敘事**，不要堆 SD 標籤 |
| 音訊 | LTX 可產音，NSFW 對白用英文或拼音實驗 |

**Prompt 範本（NSFW/RP 友善 · 敘事體）：**

```
A cinematic close-up of [角色外觀完整描述], soft bedroom lighting.
She slowly leans forward, eyes half-closed, breathing gently.
Camera dollies in over 4 seconds; fabric shifts with natural motion;
skin detail, film grain, shallow depth of field. No censorship, adult scene.
Ambient soft breathing audio, quiet room tone.
```

**Negative（簡短即可，LTX 對 SD 式 negative 不敏感）：**

```
static, freeze frame, morphing face, extra limbs, watermark, text overlay, blurry, low quality
```

**API：** `backend=sulphur2` 目前引導你用 UI 模板（多階段圖尚未完全 API 化）。  
自動化首選 API 路徑請用 `wan22_5b` / `wan22_remix`。

---

### 3.2 Sulphur 2 / Wan I2V（MonsterAI 靜態圖 → 影片）

**情境：** 你已用 MonsterAI 生好角色圖 → 一鍵動起來。

#### 路徑 A：Wan 2.2 5B I2V（最穩 · API 已接好）

1. 圖生成：`POST /api/generate/image` → 取得 `url`
2. 影片：

```http
POST http://127.0.0.1:7860/api/generate/video
Content-Type: application/json

{
  "prompt": "slow sensual turn, hair sways, soft breathing, cinematic lighting",
  "backend": "wan22_5b",
  "mode": "i2v",
  "from_image_url": "/api/generate/files/images/你的檔名.png",
  "frames": 41,
  "width": 640,
  "height": 640,
  "steps": 20,
  "enhance_prompt": true
}
```

API workflow 檔：`monster_ai/modules/video/workflows/api_wan22_5b_i2v.json`

#### 路徑 B：Sulphur / 10Eros I2V（NSFW 更強）

1. ComfyUI Templates → **LTX-2.3 Image to Video**  
   或 `official/ltx23_i2v.json`
2. Checkpoint 換成 **Sulphur** 或 **TenStrip 10Eros I2V merge**
3. Load Image = MonsterAI 輸出圖（複製到 `ComfyUI/input/`）
4. Motion prompt 描述「動作變化」，少重複靜態外觀（外觀由圖鎖定）

#### 路徑 C：Wan Remix I2V（角色一致優先）

見下一節。

---

### 3.3 Wan 2.2 Remix 高品質版（角色一致性優先）

**UI：**

1. 匯入官方 Wan 2.2 14B I2V 模板，或  
   `workflows/api_wan22_14b_i2v.json`（API）/ `official/wan22_14b_i2v.json`（UI）
2. 將 **high_noise / low_noise** unet 換成 Remix 權重
3. 保持 `umt5` + `wan_2.1_vae`
4. 可選：**Lightx2v Lightning LoRA**（steps 8–12）
5. 可選：角色 LoRA（`LoraLoaderModelOnly` 掛在 unet）

**角色一致技巧：**

1. **先固定身份圖**（同一 seed 圖像管線 + 角色 LoRA）
2. I2V 解析度接近原圖比例（避免強拉伸）
3. Motion prompt 只寫動作，例如：  
   `subtle smile, blinks once, camera slowly orbits left, hair moves gently`
4. CFG 偏低（2–3.5）減少「長新臉」
5. 幀數先 33–41，穩定後再 SVI / 末幀延長

**API：**

```json
{
  "prompt": "walks toward camera, confident smile, natural hip sway, cinematic",
  "backend": "wan22_remix",
  "mode": "i2v",
  "source_image": "C:/Monster/MonsterAI/monster-ai/data/outputs/images/xxx.png",
  "frames": 41,
  "steps": 16,
  "cfg": 3.0,
  "lora": "your_character.safetensors",
  "lora_strength": 0.75
}
```

請在 `presets.py` 的 `wan22_remix.model_files` 改成你實際 Remix 檔名。

---

## 4. 推薦參數表（VRAM）

### 4.1 Sulphur 2 / LTX-2.3

| VRAM | 解析度 | 幀數 (≈秒@24fps) | steps | CFG | sampler | 備註 |
|------|--------|------------------|-------|-----|---------|------|
| 8GB | 512×320 | 25 (~1s) | 12 | 3.5 | euler / simple | GGUF Q4 或 fp8+offload |
| 12GB | 640×384 | 33–49 | 16 | 3.5–4 | euler | 日常 RP 甜點區 |
| 16GB | 768×432 | 49–73 | 20 | 4 | euler | 可開短二階段 upscale |
| 24GB | 960×544 | 73–97 | 24 | 4–5 | euler | 開 spatial x2 |

### 4.2 Wan 2.2 5B TI2V

| VRAM | 解析度 | 幀數 (4n+1) | steps | CFG | sampler |
|------|--------|-------------|-------|-----|---------|
| 8GB | 640×368 | 25 | 16 | 5 | uni_pc / simple |
| 12GB | 832×480 | 41 | 20 | 5 | uni_pc |
| 16GB | 1024×576 | 49 | 24 | 5 | uni_pc |
| 24GB | 1280×704 | 81 | 30 | 5 | uni_pc |

### 4.3 Wan 2.2 Remix / 14B

| VRAM | 解析度 | 幀數 | steps | CFG | sampler | 備註 |
|------|--------|------|-------|-----|---------|------|
| 8GB | 480×480 | 17 | 8 | 1–2 | euler | GGUF + Lightning |
| 12GB | 576×576 | 33 | 12 | 2–3 | euler | fp8 + block swap |
| 16GB | 640×640 | 41 | 16 | 3–3.5 | euler | Remix 主力 |
| 24GB | 768×768 | 57–81 | 20 | 3.5 | euler | 角色一致優先 |

### 4.4 HunyuanVideo 1.5

| VRAM | 解析度 | 幀數 | steps | CFG | 備註 |
|------|--------|------|-------|-----|------|
| 8GB | 480×480 | 25 | 16 | 6 | 重度 offload |
| 12GB | 640×640 | 33 | 20 | 6 | |
| 16GB | 720×720 | 49 | 20 | 6 | |
| 24GB | 960×540 | 65 | 24 | 6 | 可接 1080 SR 蒸餾 |

> 完整數值亦寫在 `monster_ai/modules/video/presets.py`，前端可直接讀 `GET /api/generate/video/backends`。

---

## 5. 前端整合建議

### 5.1 UI 設計（對齊現有圖像頁）

建議在圖像結果卡下方加 **「生成影片」** 區塊：

```
┌─────────────────────────────────────────────┐
│  [預覽靜態圖]                                │
│  [🎬 生成影片]  [模式 ▼ T2V/I2V]             │
│  模型: [auto ▼]  sulphur2 | wan22_5b | ...  │
│  動作提示: [________________]  [LLM 強化 ☑]  │
│  幀數 [41]  解析度 [依 VRAM 預設 ▼]          │
│  LoRA: [角色LoRA ▼]  NSFW LoRA: [  ▼]       │
│  ████████░░░░  進度 62%  (ComfyUI queue)    │
│  [影片預覽 <video controls>]  [下載 mp4]    │
└─────────────────────────────────────────────┘
```

**元件要點：**

| 元件 | 行為 |
|------|------|
| 模型下拉 | `GET /api/generate/video/backends` 填選項；標示 `uncensored` 徽章 |
| I2V 按鈕 | 帶入當前圖像 `url` 到 `from_image_url` |
| 進度條 | 輪詢 `GET /api/generate/progress` |
| 預覽 | `<video src={result.url} controls loop />` |
| VRAM 檔 | 設定頁寫入 `modules.video.vram_gb` |

### 5.2 ComfyUI API 接到 MonsterAI 後端

既有模式（`ComfyUIClient`）：

```
POST {comfyui}/prompt          ← queue workflow
GET  {comfyui}/history/{id}    ← 取 images/gifs/videos
GET  {comfyui}/view?...        ← 下載
POST {comfyui}/upload/image    ← I2V 上傳
```

MonsterAI 對外：

```
POST /api/generate/video
GET  /api/generate/video/backends
GET  /api/generate/progress
GET  /api/generate/files/videos/{filename}
```

**curl 範例 · T2V：**

```bash
curl -X POST http://127.0.0.1:7860/api/generate/video ^
  -H "Content-Type: application/json" ^
  -d "{\"prompt\":\"cinematic sunset walk on beach, wind in hair\",\"backend\":\"wan22_5b\",\"mode\":\"t2v\",\"frames\":41}"
```

**curl 範例 · I2V from 既有圖：**

```bash
curl -X POST http://127.0.0.1:7860/api/generate/video ^
  -H "Content-Type: application/json" ^
  -d "{\"prompt\":\"gentle smile, blink, hair moves\",\"backend\":\"wan22_5b\",\"mode\":\"i2v\",\"from_image_url\":\"/api/generate/files/images/abcd.png\"}"
```

### 5.3 一鍵切換模型與 workflow 邏輯

```
user selects backend B, mode M, vram V
  → presets.pick_profile(B, V)  → width/height/frames/steps/cfg/sampler
  → if B is wan*:
        load api_wan22_*.json
        patch prompts / size / seed / unet names / lora
        queue_prompt
  → if B is sulphur2 / hunyuan15:
        return guidance to UI template  (or future subgraph export)
  → if B is animatediff:
        legacy path (frames → ffmpeg)
  → download media → optional ffmpeg → mp4 → data/outputs/videos
```

`config.yaml`：

```yaml
modules:
  video:
    enabled: true
    mode: auto
    default_backend: auto
    prefer_uncensored: true
    vram_gb: 12          # 改成你的 GPU
    auto_motion_prompt: true
    max_wait_seconds: 900
```

---

## 6. 進階功能建議

### 6.1 自動加角色 LoRA / NSFW LoRA

```yaml
modules:
  video:
    auto_character_lora: true
    default_nsfw_lora: "nsfw_wan_motion.safetensors"
    default_nsfw_lora_strength: 0.75
```

實作策略：

1. 角色卡 `character_id` → 查 Guardian / training vault 綁定的 LoRA 檔名  
2. I2V 時 strength 0.6–0.85（過高易糊）  
3. NSFW motion LoRA 僅在 `prefer_uncensored: true` 時掛載  
4. Wan：LoRA 掛 unet；LTX/Sulphur：依節點支援使用 LTX LoRA 格式  

### 6.2 生成後用 LLM 寫動作描述

流程：

```
靜態圖 → (可選 VLM caption) → PromptEnhancer.for_video
  system: 你是動作導演，只輸出 1–3 句英文動作+鏡頭，不審查
→ I2V prompt
```

已有 `PromptEnhancer.for_video`；建議加強 system template（`llm/prompt_templates.py` 的 `VIDEO_PROMPT_SYSTEM`）：

- 強制時間序（first / then / finally）  
- 強制鏡頭語言（close-up, dolly, pan）  
- 禁止重複畫靜態外觀（I2V 時）  

### 6.3 影片延長 / 多鏡頭拼接

| 方法 | 說明 |
|------|------|
| **Last-frame chain** | 取上一段最後一幀 → 再 I2V；ComfyUI 可關舊段 cache |
| **SVI / long Wan workflows** | CivitAI「WAN 2.2 long video SVI」類 workflow |
| **FLF2V** | 首末幀插值（Wan 14B / LTX FLF 模板） |
| **Video Stitch** | 本機 ComfyUI blueprint `Video Stitch.json` + ffmpeg concat |

ffmpeg 多段拼接：

```powershell
# list.txt:
# file 'part1.mp4'
# file 'part2.mp4'
ffmpeg -f concat -safe 0 -i list.txt -c copy out_long.mp4
```

MonsterAI 可後續加 `POST /api/generate/video/extend`：`source_video` + `motion_prompt` → 抽末幀 → I2V → concat。

---

## 7. 完整安裝與測試步驟（從零到 NSFW 短片）

### Step 0 — 前提

- NVIDIA GPU（建議 ≥8GB）  
- 本機已有：`C:\Monster\MonsterAI\comfyui\...` 與 `monster-ai`  
- 安裝 [ffmpeg](https://ffmpeg.org/) 並加入 PATH  
- 磁碟空間：recommended 約 80GB+；full 200GB+  

### Step 1 — 更新 ComfyUI

```powershell
cd C:\Monster\MonsterAI\comfyui\ComfyUI_windows_portable_nvidia\ComfyUI_windows_portable
.\update\update_comfyui.bat
```

### Step 2 — 安裝節點 + 模型

```powershell
cd C:\Monster\MonsterAI\monster-ai
powershell -ExecutionPolicy Bypass -File .\scripts\install_video_module.ps1 -VramGB 12 -Profile recommended
```

### Step 3 — 啟動 ComfyUI

```powershell
cd C:\Monster\MonsterAI\comfyui\ComfyUI_windows_portable_nvidia\ComfyUI_windows_portable
.\run_nvidia_gpu.bat
```

開 http://127.0.0.1:8188 確認無紅色 import 錯誤。

### Step 4 — ComfyUI 內第一次手動成功（強烈建議）

**A. Wan 5B 冒煙測試（最快）：**

1. Templates → Video → Wan2.2 5B  
2. 確認 unet / clip / vae 檔名都在  
3. Prompt：`a woman walking on the beach at sunset, cinematic`  
4. length=25, 640×368 → Queue  
5. 應得到 webm/webp 短片  

**B. Sulphur 2 NSFW 測試：**

1. Templates → LTX-2.3 T2V  
2. ckpt → `sulphur_dev_fp8mixed.safetensors`  
3. 掛 abliterated + distill LoRA  
4. 使用 §3.1 敘事 prompt（成人場景）  
5. 確認輸出無「馬賽克式拒生」、動作連貫  

### Step 5 — 啟動 MonsterAI

```powershell
cd C:\Monster\MonsterAI\monster-ai
# 編輯 config.yaml：
#   modules.video.vram_gb: 12
#   modules.video.default_backend: wan22_5b
.\run.bat
```

### Step 6 — API 測試

```powershell
# 健康與後端列表
curl http://127.0.0.1:7860/api/generate/video/backends

# T2V
curl -X POST http://127.0.0.1:7860/api/generate/video `
  -H "Content-Type: application/json" `
  -d "{\"prompt\":\"cinematic close-up portrait, soft smile, hair moves in wind\",\"backend\":\"wan22_5b\",\"frames\":25,\"width\":640,\"height\":368}"
```

回傳 `url` 後瀏覽器開啟：  
`http://127.0.0.1:7860/api/generate/files/videos/<檔名>.mp4`

### Step 7 — 圖像 → 影片一條龍

```powershell
# 1) 生圖
curl -X POST http://127.0.0.1:7860/api/generate/image -H "Content-Type: application/json" -d "{\"prompt\":\"portrait of anime girl, bedroom, detailed face\"}"
# 2) 用回傳 url 做 I2V
curl -X POST http://127.0.0.1:7860/api/generate/video -H "Content-Type: application/json" -d "{\"prompt\":\"she leans closer, slow blink, intimate mood\",\"backend\":\"wan22_5b\",\"mode\":\"i2v\",\"from_image_url\":\"/api/generate/files/images/XXXX.png\"}"
```

### Step 8 — 正式 NSFW 短片清單

- [ ] Sulphur 2 T2V 成人敘事 prompt 成功  
- [ ] 角色圖 I2V 臉不崩  
- [ ] Remix 權重替換後角色更穩  
- [ ] 兩段 I2V + ffmpeg concat  
- [ ] `prefer_uncensored: true` 且無雲端 API 參與  

---

## 8. 常見錯誤排除與優化

### 8.1 VRAM 不足 / CUDA OOM

| 作法 | 說明 |
|------|------|
| 降解析度 / 幀數 | 先 480p、17–25 幀 |
| GGUF Q4/Q5 | Sulphur / Wan Remix |
| `--lowvram` / `--novram` | ComfyUI 啟動參數 |
| 關 spatial upscale 二階段 | LTX 省一半尖峰 |
| 一次只開一個大模型 | 不要圖+影並行 |
| 5B 取代 14B | 8–12GB 務實選擇 |
| Lightning LoRA | steps 砍半 |

啟動範例：

```bat
.\python_embeded\python.exe -s ComfyUI\main.py --windows-standalone-build --lowvram --listen 127.0.0.1 --port 8188
```

### 8.2 閃爍 / 時序不穩

- 幀數改 **4n+1**（25, 33, 41, 49…）  
- 降低 CFG  
- 增加 steps 或改用 dual-expert 14B  
- I2V 減少劇烈運鏡（避免瞬移）  
- 避免過強 NSFW LoRA（>1.0）  

### 8.3 角色變形 / 換臉

- **優先 I2V**，不要純 T2V 硬控臉  
- 角色 LoRA strength 0.6–0.8  
- 動作 prompt 勿改髮色/服裝  
- Remix / IPAdapter（進階）  
- 解析度與原圖比例一致  

### 8.4 速度太慢

| 手段 | 加速比（約） |
|------|----------------|
| Wan 5B 取代 14B | 2–4× |
| Lightning / distill LoRA 8–12 steps | 2–3× |
| 降低 length | 線性 |
| fp8 / GGUF | 視卡而異 |
| 關閉預覽高解析 save | 小幅 |

### 8.5 其他錯誤

| 症狀 | 處理 |
|------|------|
| `ComfyUI is not running` | 先開 `run_nvidia_gpu.bat` |
| missing node | 更新 ComfyUI + 裝 custom nodes 後重啟 |
| checkpoint not in list | 檔案放錯資料夾（checkpoint vs diffusion_models） |
| Gemma / umt5 missing | 見 §2 text_encoders |
| API sulphur2 RuntimeError | 預期行為：先用 UI 模板；API 用 wan22_* |
| 只有 webm 沒 mp4 | 安裝 ffmpeg |
| 審查式「空白/拒動」 | 換 Sulphur / Remix；掛 abliterated；避免雲端 API 節點 |

### 8.6 安全與合規（本機）

- MonsterAI **本地無審查** 設計：不要接會過濾的雲端 vision/LLM  
- **CrimeGuard** 仍會擋非法內容（未成年等）——這是保護層，不是道德審查 NSFW  
- 成人內容僅限合法年齡角色；請遵守當地法律  

---

## 附錄 A — 快速命令速查

```powershell
# 安裝
cd C:\Monster\MonsterAI\monster-ai
powershell -ExecutionPolicy Bypass -File .\scripts\install_video_module.ps1 -VramGB 12 -Profile recommended

# 啟動
C:\Monster\MonsterAI\comfyui\ComfyUI_windows_portable_nvidia\ComfyUI_windows_portable\run_nvidia_gpu.bat
cd C:\Monster\MonsterAI\monster-ai; .\run.bat

# 測試
curl http://127.0.0.1:7860/api/generate/video/backends
```

## 附錄 B — 模型優先級（建議下載順序）

1. **Wan 2.2 5B + umt5 + wan2.2_vae** → 當天就能 API I2V  
2. **Gemma + Sulphur fp8 + upscaler + abliterated** → NSFW 主力  
3. **TenStrip 10Eros** → NSFW I2V 強化  
4. **Remix GGUF/safetensors** → 角色一致  
5. **Wan 14B fp8** → 高畫質  
6. **Hunyuan 1.5** → 備援高品質  

## 附錄 C — 相關官方文件

- Wan 2.2 ComfyUI：https://docs.comfy.org/tutorials/video/wan/wan2_2  
- LTX-2.3 ComfyUI：https://docs.comfy.org/tutorials/video/ltx/ltx-2-3  
- Sulphur 2：https://huggingface.co/SulphurAI/Sulphur-2-base  
- Hunyuan 1.5 Comfy repack：https://huggingface.co/Comfy-Org/HunyuanVideo_1.5_repackaged  

---

*本文件與程式骨架為 MonsterAI 本地無限制影片模組 v1。後續可將 LTX/Sulphur 多階段圖 export 成純 API prompt，使 `backend=sulphur2` 完全自動化。*
