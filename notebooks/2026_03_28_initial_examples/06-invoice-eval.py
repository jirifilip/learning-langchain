# ---
# jupyter:
#   jupytext:
#     text_representation:
#       extension: .py
#       format_name: percent
#       format_version: '1.3'
#       jupytext_version: 1.19.1
#   kernelspec:
#     display_name: Python 3 (ipykernel)
#     language: python
#     name: python3
# ---

# %% [markdown]
# # Invoice Extraction Eval with GPT-4o Vision + MLflow
#
# Uses GPT-4o to extract structured data from invoice images, then evaluates
# extraction quality with MLflow's `genai.evaluate` API.
#
# **Pipeline:**
# 1. Generate 4 synthetic invoice images with Pillow
# 2. Define a structured extraction schema (Pydantic)
# 3. Run GPT-4o vision extraction via LangChain
# 4. Score outputs with MLflow: field completeness + LLM-as-judge accuracy
# 5. View results in MLflow UI (`just trace` to start it)

# %%
import utils

# %%
import base64
import io
import json

import mlflow
import mlflow.genai
from langchain_core.messages import HumanMessage
from langchain_openai import ChatOpenAI
from mlflow.genai import make_judge, scorer
from PIL import Image, ImageDraw, ImageFont
from pydantic import BaseModel, Field

# %% [markdown]
# ## 1. Generate synthetic invoice images
#
# Creates 4 realistic invoice images using Pillow — no external URLs needed.
# Each invoice has different vendors, customers, line items, and totals.

# %%
INVOICE_DATA = [
    {
        "id": "invoice_1",
        "number": "INV-2024-001",
        "date": "2024-01-15",
        "due_date": "2024-02-15",
        "vendor": {"name": "Acme Corp", "address": "123 Main St, New York, NY 10001"},
        "customer": {"name": "Beta LLC", "address": "456 Oak Ave, Los Angeles, CA 90001"},
        "items": [
            {"desc": "Web Development Services", "qty": 40, "unit": 150.00},
            {"desc": "UI/UX Design", "qty": 20, "unit": 120.00},
        ],
        "tax_rate": 0.08,
        "currency": "USD",
    },
    {
        "id": "invoice_2",
        "number": "INV-2024-042",
        "date": "2024-02-03",
        "due_date": "2024-03-03",
        "vendor": {"name": "TechSupply Ltd", "address": "789 Pine Rd, Chicago, IL 60601"},
        "customer": {"name": "Gamma Inc", "address": "321 Elm St, Houston, TX 77001"},
        "items": [
            {"desc": "Laptop - Model X500", "qty": 3, "unit": 1299.99},
            {"desc": "Wireless Mouse", "qty": 3, "unit": 49.99},
            {"desc": "USB-C Hub", "qty": 3, "unit": 39.99},
        ],
        "tax_rate": 0.07,
        "currency": "USD",
    },
    {
        "id": "invoice_3",
        "number": "2024-REF-0099",
        "date": "2024-03-20",
        "due_date": "2024-04-20",
        "vendor": {"name": "CloudHost GmbH", "address": "Berliner Str. 12, 10115 Berlin, Germany"},
        "customer": {"name": "Delta Solutions", "address": "Rue de Rivoli 44, 75001 Paris, France"},
        "items": [
            {"desc": "Cloud Hosting - Annual Plan", "qty": 1, "unit": 2400.00},
            {"desc": "SSL Certificate", "qty": 2, "unit": 85.00},
        ],
        "tax_rate": 0.19,
        "currency": "EUR",
    },
    {
        "id": "invoice_4",
        "number": "SI-20240415",
        "date": "2024-04-15",
        "due_date": "2024-05-15",
        "vendor": {"name": "Creative Studio", "address": "55 Art Lane, Austin, TX 78701"},
        "customer": {"name": "Epsilon Brands", "address": "900 Commerce Blvd, Seattle, WA 98101"},
        "items": [
            {"desc": "Brand Identity Package", "qty": 1, "unit": 3500.00},
            {"desc": "Social Media Assets", "qty": 1, "unit": 800.00},
            {"desc": "Revision Rounds", "qty": 3, "unit": 200.00},
        ],
        "tax_rate": 0.095,
        "currency": "USD",
    },
]


def render_invoice(data: dict) -> str:
    """Render invoice dict as a PNG image and return base64 string."""
    W, H = 700, 900
    img = Image.new("RGB", (W, H), color=(255, 255, 255))
    draw = ImageDraw.Draw(img)

    try:
        font_title = ImageFont.truetype("arial.ttf", 22)
        font_header = ImageFont.truetype("arial.ttf", 14)
        font_body = ImageFont.truetype("arial.ttf", 12)
    except OSError:
        font_title = font_header = font_body = ImageFont.load_default()

    def text(x, y, s, font=font_body, color=(0, 0, 0)):
        draw.text((x, y), str(s), fill=color, font=font)

    # Header bar
    draw.rectangle([0, 0, W, 60], fill=(30, 80, 160))
    text(20, 18, "INVOICE", font=font_title, color=(255, 255, 255))
    text(W - 200, 28, f"# {data['number']}", font=font_header, color=(220, 230, 255))

    # Vendor / Customer
    y = 80
    text(20, y, "FROM", font=font_header, color=(100, 100, 100))
    text(350, y, "BILL TO", font=font_header, color=(100, 100, 100))
    y += 20
    text(20, y, data["vendor"]["name"], font=font_header)
    text(350, y, data["customer"]["name"], font=font_header)
    y += 16
    text(20, y, data["vendor"]["address"], font=font_body)
    text(350, y, data["customer"]["address"], font=font_body)

    # Dates
    y += 40
    text(20, y, f"Invoice Date:  {data['date']}", font=font_body)
    text(20, y + 18, f"Due Date:      {data['due_date']}", font=font_body)

    # Line items table header
    y += 60
    draw.rectangle([20, y, W - 20, y + 22], fill=(230, 235, 245))
    text(25, y + 4, "Description", font=font_header)
    text(430, y + 4, "Qty", font=font_header)
    text(490, y + 4, "Unit Price", font=font_header)
    text(590, y + 4, "Total", font=font_header)
    y += 26

    subtotal = 0.0
    for item in data["items"]:
        line_total = item["qty"] * item["unit"]
        subtotal += line_total
        text(25, y, item["desc"])
        text(430, y, str(item["qty"]))
        text(490, y, f"{item['unit']:.2f}")
        text(590, y, f"{line_total:.2f}")
        y += 20
        draw.line([20, y, W - 20, y], fill=(220, 220, 220))
        y += 4

    # Totals
    tax = subtotal * data["tax_rate"]
    total = subtotal + tax
    y += 10
    draw.line([400, y, W - 20, y], fill=(180, 180, 180), width=1)
    y += 8
    text(400, y, "Subtotal:")
    text(590, y, f"{data['currency']} {subtotal:.2f}")
    y += 20
    text(400, y, f"Tax ({data['tax_rate']*100:.1f}%):")
    text(590, y, f"{data['currency']} {tax:.2f}")
    y += 20
    draw.rectangle([398, y - 2, W - 18, y + 22], fill=(30, 80, 160))
    text(400, y + 2, "TOTAL DUE:", font=font_header, color=(255, 255, 255))
    text(560, y + 2, f"{data['currency']} {total:.2f}", font=font_header, color=(255, 255, 255))

    # Footer
    draw.rectangle([0, H - 30, W, H], fill=(240, 240, 240))
    text(20, H - 22, "Payment due within 30 days. Thank you for your business.", font=font_body, color=(120, 120, 120))

    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return base64.b64encode(buf.getvalue()).decode()


invoices = []
for data in INVOICE_DATA:
    b64 = render_invoice(data)
    invoices.append({"id": data["id"], "b64": b64, "media_type": "image/png", "ground_truth": data})
    print(f"✓ {data['id']}: rendered ({len(b64)} chars)")

print(f"\nGenerated {len(invoices)} invoices")

# %% [markdown]
# ### Inspect generated invoices

# %%
import matplotlib.pyplot as plt

fig, axes = plt.subplots(1, len(invoices), figsize=(5 * len(invoices), 7))
for ax, inv in zip(axes, invoices):
    img = Image.open(io.BytesIO(base64.b64decode(inv["b64"])))
    ax.imshow(img)
    ax.set_title(inv["id"], fontsize=10)
    ax.axis("off")
plt.tight_layout()
plt.show()

# %% [markdown]
# ## 2. Define the extraction schema
#
# Structured output that GPT-4o will populate from each invoice image.

# %%
class LineItem(BaseModel):
    description: str = Field(description="Item or service description")
    quantity: float | None = Field(default=None, description="Quantity")
    unit_price: float | None = Field(default=None, description="Price per unit")
    total: float | None = Field(default=None, description="Line total")


class InvoiceExtraction(BaseModel):
    invoice_number: str | None = Field(default=None, description="Invoice or reference number")
    invoice_date: str | None = Field(default=None, description="Invoice date (ISO format if possible)")
    due_date: str | None = Field(default=None, description="Payment due date")
    vendor_name: str | None = Field(default=None, description="Seller / vendor name")
    vendor_address: str | None = Field(default=None, description="Seller address")
    customer_name: str | None = Field(default=None, description="Buyer / bill-to name")
    customer_address: str | None = Field(default=None, description="Buyer address")
    line_items: list[LineItem] = Field(default_factory=list, description="Individual line items")
    subtotal: float | None = Field(default=None, description="Subtotal before tax")
    tax: float | None = Field(default=None, description="Tax amount")
    total: float | None = Field(default=None, description="Total amount due")
    currency: str | None = Field(default=None, description="Currency code, e.g. USD")
    notes: str | None = Field(default=None, description="Any payment terms or notes")

# %% [markdown]
# ## 3. Define the extraction chain
#
# GPT-4o vision model with structured output via `.with_structured_output()`.

# %%
llm = ChatOpenAI(model="gpt-4o", temperature=0)
extractor = llm.with_structured_output(InvoiceExtraction)

SYSTEM_PROMPT = (
    "You are an expert invoice parser. Extract all available fields from the invoice image. "
    "Use null for fields that are not present. Return amounts as numbers, not strings."
)


def extract_invoice(b64: str, media_type: str) -> InvoiceExtraction:
    message = HumanMessage(content=[
        {
            "type": "image_url",
            "image_url": {"url": f"data:{media_type};base64,{b64}", "detail": "high"},
        },
        {"type": "text", "text": SYSTEM_PROMPT},
    ])
    return extractor.invoke([message])

# %% [markdown]
# Quick smoke test on the first invoice.

# %%
if invoices:
    sample = extract_invoice(invoices[0]["b64"], invoices[0]["media_type"])
    print(sample.model_dump_json(indent=2))

# %% [markdown]
# ## 4. Build the evaluation dataset
#
# Because we generated the invoices ourselves, we have exact ground truth.
# `expectations` carries the known-correct values for the LLM judge scorer.

# %%
def _expected_total(data: dict) -> float:
    subtotal = sum(i["qty"] * i["unit"] for i in data["items"])
    return round(subtotal * (1 + data["tax_rate"]), 2)


dataset = [
    {
        "inputs": {"invoice_id": inv["id"], "b64": inv["b64"], "media_type": inv["media_type"]},
        "expectations": {
            "invoice_number": inv["ground_truth"]["number"],
            "invoice_date": inv["ground_truth"]["date"],
            "vendor_name": inv["ground_truth"]["vendor"]["name"],
            "customer_name": inv["ground_truth"]["customer"]["name"],
            "total": _expected_total(inv["ground_truth"]),
            "currency": inv["ground_truth"]["currency"],
            "criteria": (
                f"invoice_number={inv['ground_truth']['number']}, "
                f"vendor={inv['ground_truth']['vendor']['name']}, "
                f"customer={inv['ground_truth']['customer']['name']}, "
                f"total={_expected_total(inv['ground_truth'])} {inv['ground_truth']['currency']}. "
                "All numeric fields must be numbers, not strings."
            ),
        },
    }
    for inv in invoices
]

print(f"Dataset: {len(dataset)} examples")

# %% [markdown]
# ## 5. Define `predict_fn`
#
# Must accept the unpacked `inputs` dict as keyword args and return a string.

# %%
def predict_fn(invoice_id: str, b64: str, media_type: str) -> str:
    result = extract_invoice(b64, media_type)
    return result.model_dump_json()

# %% [markdown]
# ## 6. Define scorers
#
# ### Field completeness scorer
# Counts how many key fields were extracted (non-null).

# %%
KEY_FIELDS = ["invoice_number", "invoice_date", "vendor_name", "customer_name", "total"]

@scorer
def field_completeness(outputs: str) -> float:
    """Fraction of key fields that were successfully extracted."""
    try:
        data = json.loads(outputs)
        filled = sum(1 for f in KEY_FIELDS if data.get(f) is not None)
        return filled / len(KEY_FIELDS)
    except Exception:
        return 0.0

# %% [markdown]
# ### Total match scorer
# Checks if the extracted total is within 1% of the ground-truth value.

# %%
@scorer
def total_match(outputs: str, expectations: dict) -> bool:
    try:
        data = json.loads(outputs)
        extracted = data.get("total")
        expected = expectations.get("total")
        if extracted is None or expected is None:
            return False
        return abs(extracted - expected) / expected < 0.01
    except Exception:
        return False

# %% [markdown]
# ### LLM-as-judge scorer
# Asks GPT-4o-mini to evaluate whether the extraction meets the criteria.

# %%
invoice_quality_judge = make_judge(
    name="invoice_extraction_quality",
    model="openai:/gpt-4o-mini",
    instructions=(
        "You are evaluating an AI invoice extraction result.\n\n"
        "Criteria: {{ expectations['criteria'] }}\n\n"
        "Extracted JSON:\n{{ outputs }}\n\n"
        "Score from 1 (poor) to 5 (excellent). "
        "Reply with ONLY a JSON object: {\"score\": <int>, \"reason\": \"<one sentence>\"}."
    ),
)

# %% [markdown]
# ## 7. Run evaluation
#
# Disable LangChain autolog first — it conflicts with `mlflow.genai.evaluate`'s
# own tracing and causes evaluation traces to never close.

# %%
mlflow.langchain.autolog(disable=True)

results = mlflow.genai.evaluate(
    data=dataset,
    predict_fn=predict_fn,
    scorers=[
        field_completeness,
        total_match,
        invoice_quality_judge,
    ],
)

# %% [markdown]
# ## 8. Inspect results

# %%
print("Aggregate metrics:")
print(results.metrics)

# %%
print("\nPer-row results:")
results.tables["eval_results"]
