"""
OpenAI vision check: do the product photos really show the product (or something related to it)?

The operation is expensive, therefore:
  * results are cached in a JSONL file (model + code + name + image URL); reruns skip them
  * callers select products explicitly (codes / filters / limit)
"""
import base64
import hashlib
import json
import logging
import os
import threading
from datetime import datetime

from cssklib.constants import DEFAULT_VISION_MODEL, OPENAI_API_KEY_ENV, VISION_MODEL_ENV
from cssklib.images import sorted_images
from cssklib.values import get_brand, get_code, get_name

VERDICT_PRODUCT = "product"
VERDICT_RELATED = "related"
VERDICT_UNRELATED = "unrelated"
VERDICT_UNCLEAR = "unclear"
VERDICTS = (VERDICT_PRODUCT, VERDICT_RELATED, VERDICT_UNRELATED, VERDICT_UNCLEAR)

SYSTEM_PROMPT = (
    "You verify product photos of a table tennis e-shop. For every image decide whether it belongs "
    "to the given product. Verdicts:\n"
    f"- \"{VERDICT_PRODUCT}\": the image shows this product (any angle, colour variant, detail, packaging).\n"
    f"- \"{VERDICT_RELATED}\": the image does not show the product itself but clearly relates to it "
    "(e.g. size chart for textile/shoes, technology or material illustration of the product, "
    "brand/series logo, product in use, specification table).\n"
    f"- \"{VERDICT_UNRELATED}\": the image shows a different product or content unrelated to the product.\n"
    f"- \"{VERDICT_UNCLEAR}\": impossible to decide (broken, blank, placeholder image).\n"
    "Use the product name and catalog code (the code prefix usually encodes the brand). "
    "Answer ONLY with JSON: {\"images\": [{\"index\": <1-based index>, \"verdict\": \"...\", "
    "\"reason\": \"short reason in Czech\"}]}"
)


def default_model():
    return os.getenv(VISION_MODEL_ENV) or DEFAULT_VISION_MODEL


def create_openai_client():
    api_key = os.getenv(OPENAI_API_KEY_ENV)
    if not api_key:
        raise RuntimeError(f"Proměnná prostředí {OPENAI_API_KEY_ENV} není nastavena")
    import openai
    return openai.OpenAI(api_key=api_key, timeout=300.0)


def build_user_content(product, side, images, image_inputs, detail):
    categories = []
    for category in product.get("categories") or []:
        categories.append(" > ".join((category.get("path") or {}).values()))
    text = (
        f"Product name: {get_name(product, side)}\n"
        f"Catalog code: {get_code(product)}\n"
        f"Brand: {get_brand(product) or '-'}\n"
        f"Categories: {'; '.join(c for c in categories if c) or '-'}\n"
        f"Number of images: {len(images)} (in the order below)"
    )
    content = [{"type": "text", "text": text}]
    for image_input in image_inputs:
        content.append({"type": "image_url", "image_url": {"url": image_input, "detail": detail}})
    return content


def parse_response(text, count):
    """Parse model JSON answer into {index: (verdict, reason)}; missing images become 'unclear'."""
    try:
        data = json.loads(text)
    except (TypeError, ValueError):
        start, end = (text or "").find("{"), (text or "").rfind("}")
        data = json.loads(text[start:end + 1]) if start >= 0 and end > start else {}
    verdicts = {}
    for item in (data.get("images") or []) if isinstance(data, dict) else []:
        try:
            index = int(item.get("index"))
        except (TypeError, ValueError):
            continue
        verdict = str(item.get("verdict", "")).strip().lower()
        if verdict not in VERDICTS:
            verdict = VERDICT_UNCLEAR
        if 1 <= index <= count:
            verdicts[index] = (verdict, str(item.get("reason") or ""))
    for index in range(1, count + 1):
        verdicts.setdefault(index, (VERDICT_UNCLEAR, "Model nevrátil hodnocení obrázku"))
    return verdicts


class VisionCache:
    def __init__(self, path):
        self.path = path
        self.entries = {}
        self._lock = threading.Lock()
        if path and os.path.isfile(path):
            with open(path, "r", encoding="utf-8") as handle:
                for line in handle:
                    line = line.strip()
                    if line:
                        entry = json.loads(line)
                        self.entries[entry["key"]] = entry

    @staticmethod
    def key(model, code, name, url):
        return hashlib.sha1(f"{model}|{code}|{name}|{url}".encode("utf-8")).hexdigest()

    def get(self, key):
        return self.entries.get(key)

    def put(self, entry):
        with self._lock:
            self.entries[entry["key"]] = entry
            if self.path:
                os.makedirs(os.path.dirname(os.path.abspath(self.path)), exist_ok=True)
                with open(self.path, "a", encoding="utf-8") as handle:
                    handle.write(json.dumps(entry, ensure_ascii=False) + "\n")


class VisionChecker:
    def __init__(self, model=None, client=None, cache_path=None, detail="low", max_images=0,
                 embed_images=False, image_store=None, refresh=False):
        self.model = model or default_model()
        self._client = client
        self.cache = VisionCache(cache_path)
        self.detail = detail
        self.max_images = max_images
        self.embed_images = embed_images
        self.image_store = image_store
        self.refresh = refresh
        self.usage = {"requests": 0, "prompt_tokens": 0, "completion_tokens": 0, "cached_images": 0}

    @property
    def client(self):
        if self._client is None:
            self._client = create_openai_client()
        return self._client

    def _image_input(self, url):
        if not self.embed_images:
            return url
        content = self.image_store.get_bytes(url) if self.image_store else None
        if content is None:
            return url
        ext = os.path.splitext(url)[1].lower().lstrip(".") or "jpeg"
        mime = "jpeg" if ext in ("jpg", "jpeg") else ext
        return f"data:image/{mime};base64," + base64.b64encode(content).decode("ascii")

    def check_product(self, product, side="cs"):
        """Return list of {'index', 'url', 'verdict', 'reason', 'cached'} for the product images."""
        images = sorted_images(product)
        if self.max_images:
            images = images[:self.max_images]
        code, name = get_code(product), get_name(product, side)
        results, pending = [], []
        for index, image in enumerate(images, start=1):
            url = image.get("url")
            key = VisionCache.key(self.model, code, name, url)
            cached = None if self.refresh else self.cache.get(key)
            if cached:
                self.usage["cached_images"] += 1
                results.append({"index": index, "url": url, "verdict": cached["verdict"],
                                 "reason": cached.get("reason", ""), "cached": True})
            else:
                pending.append((index, url, key))
        if pending:
            results.extend(self._ask(product, side, code, name, pending))
        return sorted(results, key=lambda r: r["index"])

    def _ask(self, product, side, code, name, pending):
        inputs = [self._image_input(url) for _, url, _ in pending]
        content = build_user_content(product, side, pending, inputs, self.detail)
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "system", "content": SYSTEM_PROMPT},
                      {"role": "user", "content": content}],
            response_format={"type": "json_object"},
            temperature=0,
        )
        self.usage["requests"] += 1
        usage = getattr(response, "usage", None)
        if usage is not None:
            self.usage["prompt_tokens"] += getattr(usage, "prompt_tokens", 0) or 0
            self.usage["completion_tokens"] += getattr(usage, "completion_tokens", 0) or 0
        verdicts = parse_response(response.choices[0].message.content, len(pending))
        results = []
        for position, (index, url, key) in enumerate(pending, start=1):
            verdict, reason = verdicts[position]
            self.cache.put({"key": key, "model": self.model, "code": code, "name": name, "url": url,
                            "verdict": verdict, "reason": reason,
                            "evaluated_at": datetime.now().isoformat(timespec="seconds")})
            results.append({"index": index, "url": url, "verdict": verdict, "reason": reason, "cached": False})
        logging.debug(f"Vision {code}: {[(r['index'], r['verdict']) for r in results]}")
        return results
