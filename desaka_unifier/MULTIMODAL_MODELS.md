# Multimodální modely - Dokumentace

## Přehled

Systém `local_client.py` podporuje **POUZE multimodální modely** (text + vision), které umožňují:
- Analýzu obrázků produktů
- OCR (rozpoznávání textu z obrázků)
- Vizuální detekci produktů
- Kategorizaci na základě obrázků
- Extrakci produktových atributů z fotografií

## Podporované backendy

### 1. Ollama (Doporučeno - nejjednodušší)

**Instalace:**
```bash
# Windows/Mac/Linux
curl -fsSL https://ollama.ai/install.sh | sh
```

**Dostupné multimodální modely:**

| Model | Velikost | Parametry | Popis | Instalace |
|-------|----------|-----------|-------|-----------|
| `moondream` | 1.6 GB | ~1.6B | Nejmenší efektivní vision model | `ollama pull moondream` |
| `llava:7b` | 4.5 GB | 7B | LLaVA malý - dobrá rychlost | `ollama pull llava:7b` |
| `qwen2-vl:7b` | 4.7 GB | 7B | Qwen2-VL malý - vynikající pro češtinu | `ollama pull qwen2-vl:7b` |
| `minicpm-v:8b` | 5.2 GB | 8B | MiniCPM-V - efektivní čínský model | `ollama pull minicpm-v:8b` |
| `llava:13b` | 7.3 GB | 13B | **Doporučeno** - LLaVA střední | `ollama pull llava:13b` |
| `llava:34b` | 19 GB | 34B | LLaVA velký - nejlepší kvalita | `ollama pull llava:34b` |
| `qwen2-vl:72b` | 43 GB | 72B | Qwen2-VL flagship - maximální výkon | `ollama pull qwen2-vl:72b` |

**Doporučení:**
- **Pro vývoj/testování:** `llava:7b` nebo `moondream`
- **Pro produkci:** `llava:13b` (nejlepší poměr výkon/rychlost)
- **Pro maximální kvalitu:** `llava:34b` nebo `qwen2-vl:72b`

**Kontrola nainstalovaných modelů:**
```bash
ollama list
```

### 2. LM Studio

**Instalace:**
```bash
# Stáhnout z https://lmstudio.ai
```

**Postup:**
1. Spustit LM Studio
2. V záložce "Discover" vyhledat multimodální modely:
   - LLaVA (doporučeno)
   - Qwen2-VL
   - MiniCPM-V
   - Moondream
3. Stáhnout a načíst model
4. Spustit lokální server (port 1234)

**Upozornění:**
Systém automaticky filtruje pouze multimodální modely. Pokud není žádný multimodální model načten, zobrazí se varování:
```
WARNING: No multimodal models detected in LM Studio.
Please load a multimodal model (LLaVA, Qwen2-VL, MiniCPM-V, Moondream)
```

### 3. Hugging Face (Local)

**Instalace:**
```bash
pip install transformers torch torchvision
# Pro CUDA/GPU podporu:
pip install torch torchvision --index-url https://download.pytorch.org/whl/cu118
```

**Dostupné multimodální modely:**

| Model | Velikost | Parametry | Popis |
|-------|----------|-----------|-------|
| `vikhyatk/moondream2` | 3.5 GB | ~1.6B | Nejmenší efektivní |
| `openbmb/MiniCPM-V-2_6` | 18 GB | 8B | Efektivní čínský model |
| `Qwen/Qwen2-VL-7B-Instruct` | 16 GB | 7B | Qwen2-VL malý |
| `liuhaotian/llava-v1.6-vicuna-13b` | 28 GB | 13B | **Doporučeno** - LLaVA střední |
| `Qwen/Qwen2-VL-72B-Instruct` | 150 GB | 72B | Flagship - vyžaduje hodně RAM/VRAM |

**Storage path:**
```python
# Z constants.py
LOCAL_MODEL_STORAGE_PATH_HUGGINGFACE = "G:/LLM/HuggingFace"
```

**Automatické stahování:**
Modely se stahují automaticky při prvním použití do cache adresáře.

**Požadavky na hardware:**
- **CPU only:** Funguje, ale pomalé
- **GPU (CUDA):** Doporučeno minimálně 8GB VRAM pro 7B modely
- **RAM:** Minimálně 16GB pro 7B, 32GB+ pro větší modely

### 4. Hugging Face API (Fallback)

Pokud není k dispozici lokální HW, systém automaticky použije Hugging Face Inference API.

**Nastavení:**
```bash
export HUGGING_FACE_TOKEN="hf_xxxxxxxxxxxxxxxxxxxxx"
# nebo
export HF_TOKEN="hf_xxxxxxxxxxxxxxxxxxxxx"
```

**Výhody:**
- Nevyžaduje lokální HW
- Rychlé inference přes API
- Bez stahování modelů

**Nevýhody:**
- Vyžaduje internet
- API rate limits
- Pomalejší než lokální GPU

## Mapping úloh na modely

Systém automaticky vybírá vhodný model podle typu úlohy:

```python
task_model_mapping = {
    'general': 'efficient',              # llava:13b / Qwen2-VL-7B
    'complex': 'flagship',               # llava:34b / Qwen2-VL-72B
    'simple': 'tiny',                    # moondream
    'reasoning': 'flagship',             # llava:34b / Qwen2-VL-72B
    'creative': 'flagship',              # llava:34b / Qwen2-VL-72B
    'category_mapping': 'flagship',      # Složitá analýza
    'product_analysis': 'flagship',      # Analýza produktů
    'text_generation': 'flagship',       # Generování textu
    'translation': 'flagship',           # Překlady
    'name_generation': 'flagship',       # Generování názvů
    'description_translation': 'flagship', # Překlad popisů
    'brand_detection': 'efficient',      # Detekce značky
    'type_detection': 'efficient',       # Detekce typu
    'model_detection': 'efficient',      # Detekce modelu
    'keyword_generation': 'efficient'    # Generování klíčových slov
}
```

## Použití v kódu

```python
from unifierlib.local_client import LocalClient

# Automatická detekce backendu
client = LocalClient()

# Nebo specifikovat preferovaný backend
client = LocalClient(preferred_backend='ollama')

# Text completion
response = client.simple_completion(
    "Popis tento produkt: stolní tenisová pálka Butterfly Timo Boll",
    task_type='product_analysis'
)

# JSON completion
response = client.simple_json_completion(
    "Analyzuj produktový obrázek a extrahuj značku, typ a model",
    task_type='product_analysis'
)

# Chat completion s historií
messages = [
    {"role": "system", "content": "Jsi expert na stolní tenis"},
    {"role": "user", "content": "Jaký je tento produkt?"}
]
response = client.chat_completion(messages, task_type='product_analysis')

# Získání informací o backendu
info = client.get_backend_info()
print(f"Backend: {info['backend']}")
print(f"Dostupné modely: {info['available_models']}")
print(f"Nainstalované modely: {info.get('installed_models', [])}")
```

## Automatické zajištění dostupnosti modelů

### Ollama - Automatické stahování

Systém automaticky:
1. ✅ Kontroluje, zda je model nainstalován
2. ✅ Kontroluje dostupné místo na disku (20% rezerva)
3. ✅ Stahuje model pokud chybí
4. ✅ Používá timeout 1 hodinu pro stahování

```python
# Automatické při prvním použití
client = LocalClient(preferred_backend='ollama')
# Pokud 'llava:13b' není nainstalován, automaticky se stáhne
```

### Hugging Face - Lazy loading

```python
# Model se načte až při prvním použití
client = LocalClient(preferred_backend='huggingface')
# První volání - načte model do paměti (může trvat 1-5 minut)
response = client.simple_completion("test")
# Další volání - použije už načtený model (rychlé)
response2 = client.simple_completion("test2")
```

## Troubleshooting

### "No local multimodal model backend available"

**Řešení:**
```bash
# Nejjednodušší - Ollama
curl -fsSL https://ollama.ai/install.sh | sh
ollama pull llava:13b

# Nebo LM Studio
# Stáhnout z https://lmstudio.ai a načíst multimodální model

# Nebo Hugging Face
pip install transformers torch
```

### "Ollama service not running"

```bash
# Spustit Ollama
ollama serve
```

### "Insufficient disk space"

Modely jsou velké. Ujistěte se, že máte dostatek místa:
- Tiny modely: 2-5 GB
- Střední modely: 7-20 GB
- Velké modely: 40-150 GB

### "LM Studio server not responding"

1. Spusťte LM Studio
2. Načtěte multimodální model
3. Klikněte na "Start Server" (port 1234)

### "Model too large for GPU"

```bash
# Použijte menší model
ollama pull llava:7b  # místo llava:34b

# Nebo použijte CPU (pomalejší)
# HuggingFace automaticky přepne na CPU pokud není GPU
```

## Doporučení pro produkci

1. **Ollama + LLaVA:13b** - Nejlepší poměr výkon/rychlost/jednoduchost
2. **Záloha:** Hugging Face API jako fallback
3. **Hardware:** Minimálně 16GB RAM, doporučeno GPU s 8GB+ VRAM
4. **Storage:** SSD s minimálně 50GB volného místa

## Reference

- **Ollama:** https://ollama.ai
- **LM Studio:** https://lmstudio.ai
- **Hugging Face:** https://huggingface.co
- **LLaVA:** https://llava-vl.github.io
- **Qwen2-VL:** https://github.com/QwenLM/Qwen2-VL
- **MiniCPM-V:** https://github.com/OpenBMB/MiniCPM-V
- **Moondream:** https://github.com/vikhyat/moondream
