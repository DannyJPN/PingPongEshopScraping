# Memory Validation Team - Claude Code Skills

## 🎯 Mission

Validate and maintain the integrity of Desaka's Memory system CSV files. Detect and fix **semantic errors** that Python parsers cannot catch - errors where data is technically valid CSV but logically incorrect.

## 👥 Team Structure

### Senior Specialists (13 roles, ~41 juniors)

| Senior Specialist | Juniors | Validates |
|-------------------|---------|-----------|
| **Senior NameMemory Validation Specialist** | 3 Junior Memory Validators | NameMemory_CS.csv, NameMemory_SK.csv - Product type correctness |
| **Senior ProductTypeMemory Validation Specialist** | 3 Junior Type Validators | ProductTypeMemory_CS.csv, _SK.csv - Type-only values (no brands/models) |
| **Senior ProductBrandMemory Validation Specialist** | 3 Junior Brand Validators | ProductBrandMemory_CS.csv, _SK.csv - Valid brands from BrandCodeList |
| **Senior ProductModelMemory Validation Specialist** | 3 Junior Model Validators | ProductModelMemory_CS.csv, _SK.csv - Model names only (no brands/types) |
| **Senior CategoryMemory Validation Specialist** | 4 Junior Category Validators | CategoryMemory_CS.csv, _SK.csv - Category hierarchy and type alignment |
| **Senior CategoryNameMemory Validation Specialist** | 3 Junior Category Name Validators | CategoryNameMemory_CS.csv - Master category list (KEY=VALUE) |
| **Senior DescMemory Validation Specialist** | 3 Junior Description Validators | DescMemory_CS.csv, _SK.csv - HTML descriptions, valid format, correct language |
| **Senior ShortDescMemory Validation Specialist** | 3 Junior Short Desc Validators | ShortDescMemory_CS.csv, _SK.csv - Plain text, 40-250 chars, no HTML |
| **Senior VariantNameMemory Validation Specialist** | 3 Junior Variant Name Validators | VariantNameMemory_CS.csv, _SK.csv - Variant names translated to Czech/Slovak |
| **Senior VariantValueMemory Validation Specialist** | 3 Junior Variant Value Validators | VariantValueMemory_CS.csv, _SK.csv - Variant values translated to Czech/Slovak |
| **Senior StockStatusMemory Validation Specialist** | 3 Junior Stock Status Validators | StockStatusMemory_CS.csv, _SK.csv - Stock messages translated and standardized |
| **Senior KeywordsMemory Validation Specialist** | 4 Junior Keyword Validators | KeywordsGoogle (5 keywords), KeywordsZbozi (2 keywords) |
| **Senior Cross-Reference Validation Specialist** | 4 Junior Cross-Ref Analysts | Consistency across ALL Memory files |

**Total**: 13 senior specialists + 41 junior validators

---

## 🔍 What Are Semantic Errors?

**Semantic errors** are errors where data is syntactically correct (valid CSV) but semantically wrong (logically incorrect).

### Example 1: Wrong Product Type
```csv
# NameMemory_CS.csv
"BUTTERFLY Dignics 05","Dřevo Butterfly Dignics 05"  ❌
```
- **Syntactically**: Valid CSV ✅
- **Semantically**: Dignics is a RUBBER (Potah), NOT a BLADE (Dřevo) ❌
- **Impact**: Export will categorize rubber as blade → Platform rejection

### Example 2: Invalid Brand
```csv
# ProductBrandMemory_CS.csv
"ASICS Blade FF","1 Stück"  ❌
```
- **Syntactically**: Valid CSV ✅
- **Semantically**: "1 Stück" (quantity) is NOT a brand ❌
- **Impact**: Brand filtering fails → Product not exported

### Example 3: Keyword Count Wrong
```csv
# KeywordsGoogle_CS.csv (needs 5 keywords)
"Product","keyword1, keyword2, keyword3"  ❌
```
- **Syntactically**: Valid CSV ✅
- **Semantically**: Only 3 keywords, Google requires 5 ❌
- **Impact**: Google Shopping feed validation fails

---

## 📊 Validation Coverage Matrix

| Memory File | Validator | Checks |
|-------------|-----------|--------|
| **NameMemory_CS/SK.csv** | Senior NameMemory Validator | ✓ Product type correct (Potah/Dřevo/Boty)<br>✓ Brand matches KEY<br>✓ Model name consistent |
| **ProductTypeMemory_CS/SK.csv** | Senior ProductType Validator | ✓ VALUE is type ONLY (no brand/model)<br>✓ Type matches NameMemory<br>✓ Valid type from list |
| **ProductBrandMemory_CS/SK.csv** | Senior ProductBrand Validator | ✓ Brand exists in BrandCodeList<br>✓ Not quantity/number/phrase<br>✓ Brand matches NameMemory |
| **ProductModelMemory_CS/SK.csv** | Senior ProductModel Validator | ✓ Model name only (no brand/type)<br>✓ Not incomplete<br>✓ Matches NameMemory model |
| **CategoryMemory_CS/SK.csv** | Senior Category Validator | ✓ Hierarchy format valid (>)<br>✓ Category exists in CategoryCodeList<br>✓ Matches product type |
| **CategoryNameMemory_CS.csv** | Senior CategoryName Validator | ✓ KEY equals VALUE<br>✓ No typos/duplicates<br>✓ Proper Czech diacritics |
| **DescMemory_CS/SK.csv** | Senior Desc Validator | ✓ Valid HTML structure<br>✓ No broken tags<br>✓ Correct language |
| **ShortDescMemory_CS/SK.csv** | Senior ShortDesc Validator | ✓ Plain text (no HTML)<br>✓ Length 40-250 chars<br>✓ Correct language |
| **VariantNameMemory_CS/SK.csv** | Senior VariantName Validator | ✓ Translated to Czech/Slovak<br>✓ Standard variant names<br>✓ Not in original language |
| **VariantValueMemory_CS/SK.csv** | Senior VariantValue Validator | ✓ Translated to Czech/Slovak<br>✓ Colors/grips translated<br>✓ Numeric values preserved |
| **StockStatusMemory_CS/SK.csv** | Senior StockStatus Validator | ✓ Translated to Czech/Slovak<br>✓ Standard terms used<br>✓ Consistent formatting |
| **KeywordsGoogle_CS/SK.csv** | Senior Keywords Validator | ✓ Exactly 5 keywords<br>✓ Keywords relevant<br>✓ Correct language |
| **KeywordsZbozi_CS/SK.csv** | Senior Keywords Validator | ✓ Exactly 2 keywords<br>✓ Keywords relevant<br>✓ Correct language |
| **Cross-File Consistency** | Senior Cross-Reference Validator | ✓ NameMemory ↔ ProductTypeMemory<br>✓ NameMemory ↔ ProductBrandMemory<br>✓ ProductTypeMemory ↔ CategoryMemory |

---

## 🚀 How to Use

### Individual Validation

Invoke specific validator for targeted check:

```bash
# Validate product types
/senior-name-memory-validator "Check NameMemory_CS.csv for wrong product types"

# Validate brands
/senior-product-brand-memory-validator "Find non-brand values in ProductBrandMemory_CS.csv"

# Validate keywords
/senior-keywords-memory-validator "Check KeywordsGoogle_CS.csv for count errors"

# Cross-reference check
/senior-cross-reference-validator "Validate consistency across all Memory files"
```

### Full Memory Validation Workflow

```bash
# Step 1: Core Product Data Validation
/senior-name-memory-validator "Validate NameMemory_CS.csv"
/senior-product-type-memory-validator "Validate ProductTypeMemory_CS.csv"
/senior-product-brand-memory-validator "Validate ProductBrandMemory_CS.csv"
/senior-product-model-memory-validator "Validate ProductModelMemory_CS.csv"

# Step 2: Category Validation
/senior-category-memory-validator "Validate CategoryMemory_CS.csv"
/senior-category-name-memory-validator "Validate CategoryNameMemory_CS.csv"

# Step 3: Description Validation
/senior-desc-memory-validator "Validate DescMemory_CS.csv"
/senior-short-desc-memory-validator "Validate ShortDescMemory_CS.csv"

# Step 4: Variant Validation
/senior-variant-name-memory-validator "Validate VariantNameMemory_CS.csv"
/senior-variant-value-memory-validator "Validate VariantValueMemory_CS.csv"

# Step 5: Stock & Keywords Validation
/senior-stock-status-memory-validator "Validate StockStatusMemory_CS.csv"
/senior-keywords-memory-validator "Validate KeywordsGoogle and KeywordsZbozi"

# Step 6: Cross-reference validation (CRITICAL - run last!)
/senior-cross-reference-validator "Check consistency across all Memory files"

# Step 7: Review and fix
# Each validator will report errors with suggested fixes
```

---

## 🎓 Domain Knowledge Requirements

### Table Tennis Product Knowledge

Validators must understand table tennis equipment:

#### Rubbers (Potah)
- **Butterfly**: Dignics, Tenergy, Bryce, Sriver
- **Andro**: Rasanter, Hexer, Plasma
- **Tibhar**: Evolution, Genius, Hybrid K

#### Blades (Dřevo)
- **Butterfly**: Innerforce, Viscaria, Balsa Carbo
- **Andro**: Treiber, Timber, Gauzy
- **Stiga**: Carbonado, Infinity, Clipper

#### Shoes (Boty)
- **ASICS**: Blade FF, Court Hunter, Attack
- **Butterfly**: Lezoline (Mach, Rifones, Zero)
- **Mizuno**: Wave Medal, Wave Drive

#### Balls (Míček)
- **Nittaku**: 3-Star Premium, Nexcel
- **Butterfly**: G40+, A40+
- **DHS**: D40+, DJ40

---

## 📋 Common Error Patterns

### Pattern 1: Type Confusion
```
WRONG: "BUTTERFLY Dignics 05" → "Dřevo Butterfly..." (calling rubber a blade)
RIGHT: "BUTTERFLY Dignics 05" → "Potah Butterfly..." (correctly identifying rubber)
```

### Pattern 2: Brand Contamination
```
WRONG: ProductTypeMemory VALUE = "Potah Butterfly" (has brand)
RIGHT: ProductTypeMemory VALUE = "Potah" (type only)
```

### Pattern 3: Non-Brand Values
```
WRONG: ProductBrandMemory VALUE = "1 Stück" (quantity)
WRONG: ProductBrandMemory VALUE = "alle Systeme" (German phrase)
WRONG: ProductBrandMemory VALUE = "Anatomický" (adjective)
RIGHT: ProductBrandMemory VALUE = "Butterfly" (actual brand)
```

### Pattern 4: Keyword Count Mismatch
```
WRONG: KeywordsGoogle = "kw1, kw2, kw3" (only 3, needs 5)
RIGHT: KeywordsGoogle = "kw1, kw2, kw3, kw4, kw5" (exactly 5)
```

### Pattern 5: Cross-Reference Conflicts
```
CONFLICT:
- NameMemory says: "Potah Butterfly..."
- ProductTypeMemory says: "Dřevo"
→ These MUST match!
```

---

## 🎯 Validation Priorities

### Priority 1: CRITICAL (Blocks Export)
- ❌ Wrong product type in NameMemory
- ❌ Invalid brand in ProductBrandMemory
- ❌ Type mismatch between NameMemory ↔ ProductTypeMemory

### Priority 2: HIGH (Platform Rejection)
- ❌ Wrong keyword count (Google/Zbozi)
- ❌ Brand mismatch between NameMemory ↔ ProductBrandMemory
- ❌ Type-Category mismatch

### Priority 3: MEDIUM (Data Quality)
- ⚠️ Brand in ProductTypeMemory VALUE
- ⚠️ Non-descriptive keywords
- ⚠️ Missing cross-references

### Priority 4: LOW (Cosmetic)
- ⚠️ Case inconsistency in brands
- ⚠️ Extra whitespace
- ⚠️ Date format variations

---

## 📈 Success Metrics

| Metric | Target | Current |
|--------|--------|---------|
| **NameMemory Type Accuracy** | 100% | TBD |
| **ProductBrandMemory Validity** | 100% | ~95% |
| **Keyword Count Compliance** | 100% | ~98% |
| **Cross-Reference Consistency** | 100% | ~96% |
| **ProductTypeMemory Cleanness** | 100% | ~97% |

---

## 🔄 Validation Workflow

```
┌─────────────────────────────────────────┐
│  1. Individual Memory File Validation   │
│  ✓ NameMemory                          │
│  ✓ ProductTypeMemory                   │
│  ✓ ProductBrandMemory                  │
│  ✓ KeywordsMemory                      │
└────────────┬────────────────────────────┘
             │
             ▼
┌─────────────────────────────────────────┐
│  2. Cross-Reference Validation          │
│  ✓ Check consistency across files      │
│  ✓ Detect semantic conflicts           │
└────────────┬────────────────────────────┘
             │
             ▼
┌─────────────────────────────────────────┐
│  3. Error Reporting                     │
│  • Priority: CRITICAL → LOW             │
│  • Auto-fix suggestions                 │
│  • Manual review flags                  │
└────────────┬────────────────────────────┘
             │
             ▼
┌─────────────────────────────────────────┐
│  4. Fix Application                     │
│  • Auto-fix approved changes            │
│  • Flag manual review items             │
│  • Generate validation report           │
└─────────────────────────────────────────┘
```

---

## 💡 Tips for Effective Validation

1. **Always run Cross-Reference Validator last** - It catches conflicts individual validators miss
2. **Review CRITICAL errors first** - These block exports
3. **Use domain knowledge** - Know which products are rubbers vs blades
4. **Trust BrandCodeList.csv** - It's the single source of truth for brands
5. **Validate after AI processing** - AI can introduce semantic errors
6. **Check both CS and SK files** - Language-specific errors exist

---

## 📞 Quick Reference

### Need to validate...
- **Product types**: `/senior-name-memory-validator`
- **Clean types (no brands)**: `/senior-product-type-memory-validator`
- **Brand validity**: `/senior-product-brand-memory-validator`
- **Model names**: `/senior-product-model-memory-validator`
- **Categories**: `/senior-category-memory-validator`
- **Category list**: `/senior-category-name-memory-validator`
- **HTML descriptions**: `/senior-desc-memory-validator`
- **Short descriptions**: `/senior-short-desc-memory-validator`
- **Variant names**: `/senior-variant-name-memory-validator`
- **Variant values**: `/senior-variant-value-memory-validator`
- **Stock statuses**: `/senior-stock-status-memory-validator`
- **Keyword counts**: `/senior-keywords-memory-validator`
- **Cross-file consistency**: `/senior-cross-reference-validator`

### Common Issues
- **"Dignics is showing as Dřevo"** → NameMemory Validator
- **"ProductTypeMemory has 'Potah Butterfly'"** → ProductType Validator
- **"Brand shows as '1 Stück'"** → ProductBrand Validator
- **"Model contains brand name"** → ProductModel Validator
- **"Category doesn't match product type"** → Category Validator
- **"Description has broken HTML"** → Desc Validator
- **"Short desc has HTML tags"** → ShortDesc Validator
- **"Variant name not translated"** → VariantName Validator
- **"Color 'Blau' not translated"** → VariantValue Validator
- **"Stock status in German"** → StockStatus Validator
- **"Google keywords only has 3"** → Keywords Validator
- **"NameMemory and ProductTypeMemory conflict"** → Cross-Reference Validator

---

**Remember**: Semantic validation requires domain knowledge. Trust your expertise in table tennis equipment!

🤖 Built with domain expertise by the Desaka AI Team