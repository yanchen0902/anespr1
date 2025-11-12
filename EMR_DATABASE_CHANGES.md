# EMR Integration: Database Changes Summary

## Quick Answer: Minimal Changes!

**No new columns or tables added.** EMR data is stored as JSON in existing columns.

---

## What Changed in the Database?

### ChatHistory Table - ONE Column Modified

**Before EMR Integration:**
```sql
message_type VARCHAR(10)  -- Could store: 'user', 'bot', 'chat', 'summary'
```

**After EMR Integration:**
```sql
message_type VARCHAR(20)  -- Now also stores: 'emr_snapshot' (14 characters)
```

**That's it!** Only one column size expanded.

---

## Where is EMR Data Stored?

### No New Columns Needed!

EMR data uses **existing columns** in a clever way:

#### Patient Table (Unchanged)
```sql
CREATE TABLE patient (
    id INTEGER PRIMARY KEY,
    name VARCHAR(100),        -- From EMR: patient_name
    age INTEGER,              -- From EMR: age
    sex VARCHAR(10),          -- From EMR: gender
    operation VARCHAR(200),   -- From EMR: surgery_name
    medical_history TEXT,     -- From EMR: chronic_conditions
    worry TEXT,               -- Filled during chat
    cfs VARCHAR(50),          -- Filled during chat
    created_at DATETIME
);
```

#### ChatHistory Table (One column expanded)
```sql
CREATE TABLE chat_history (
    id INTEGER PRIMARY KEY,
    patient_id INTEGER,
    message TEXT,                    -- ✅ Stores full EMR snapshot JSON here!
    response TEXT,
    openai_response TEXT,
    created_at DATETIME,
    message_type VARCHAR(20),        -- ⚠️ EXPANDED from VARCHAR(10)
    feedback VARCHAR(10),
    feedback_at DATETIME,
    preferred_response VARCHAR(10)
);
```

### Example EMR Snapshot Record

```python
# In ChatHistory table:
ChatHistory(
    patient_id=45,
    message_type='emr_snapshot',  # New value (14 chars, needs VARCHAR(20))
    message='{"schema_version":"1.0.0","patient_demographics":{...},"surgery_info":{...},"vital_signs":{...}}',  # Full JSON
    response=None,
    created_at='2025-10-22 12:00:00'
)
```

The `message` column (TEXT type) stores the complete EMR snapshot:
```json
{
  "schema_version": "1.0.0",
  "source": "hospital_emr",
  "patient_demographics": {
    "medical_record_number": "M1234567",
    "id_number": "A123456789",
    "patient_name": "王大明",
    "date_of_birth": "1978/05/20",
    "age": 45,
    "gender": "男",
    "blood_type": "O+"
  },
  "surgery_info": {
    "surgery_date": "2023/11/15",
    "surgery_name": "闌尾切除術",
    "attending_surgeon": "陳醫師",
    "preop_diagnosis": "急性闌尾炎"
  },
  "vital_signs": {
    "height": "175 cm",
    "weight": "70 kg",
    "bmi": "22.86",
    "temperature": "36.5 °C",
    "heart_rate": "72 bpm",
    "blood_pressure": "120/80 mmHg",
    "respiratory_rate": "16 bpm"
  },
  "medical_history": {
    "allergies": ["青黴素"],
    "medications": ["降血壓藥"],
    "chronic_conditions": ["高血壓"]
  }
}
```

---

## Linux Deployment: Will `init_db.py` Work?

### ✅ YES! Fresh Installation on Linux

If you're deploying on a **new Linux server**, simply run:

```bash
python3 init_db.py
```

This creates the database with the **correct schema**:
- `message_type VARCHAR(20)` ✅ (supports 'emr_snapshot')
- All other columns unchanged
- No migration needed!

**Why it works:**
- `models.py` line 63 already defines `db.String(20)`
- `init_db.py` reads from `models.py` to create tables
- The correct schema is created automatically

---

## Existing Database: Migration Needed?

### ⚠️ Only If You Have Existing Data

If you already have a running system with data, you need to expand the column:

#### For SQLite (Development)
```bash
# SQLite is flexible - no action needed!
# It automatically handles VARCHAR size changes
# Just make sure models.py has String(20)
```

#### For MySQL (Production)
```bash
# Run the migration script
python3 migrations/expand_message_type_for_emr.py

# Or manually:
mysql -u root -p patients << EOF
ALTER TABLE chat_history MODIFY COLUMN message_type VARCHAR(20);
EOF
```

#### Migration Script Available
- **File**: `migrations/expand_message_type_for_emr.py`
- **Safe**: Asks for backup confirmation first
- **Smart**: Detects SQLite vs MySQL automatically
- **Tested**: Handles errors gracefully

---

## Data Access: How to Retrieve EMR Snapshot

### Query EMR Snapshot from Database

```python
# Get EMR snapshot for a patient
emr_record = ChatHistory.query.filter_by(
    patient_id=patient_id,
    message_type='emr_snapshot'
).first()

if emr_record:
    import json
    emr_data = json.loads(emr_record.message)

    # Access EMR data
    patient_name = emr_data['patient_demographics']['patient_name']
    surgery = emr_data['surgery_info']['surgery_name']
    blood_pressure = emr_data['vital_signs']['blood_pressure']
    allergies = emr_data['medical_history']['allergies']
```

### In Templates (Admin Dashboard)

```jinja2
{% if emr_snapshot %}
    <h3>EMR Data</h3>
    <p>Patient: {{ emr_snapshot.patient_demographics.patient_name }}</p>
    <p>Surgery: {{ emr_snapshot.surgery_info.surgery_name }}</p>
    <p>Blood Pressure: {{ emr_snapshot.vital_signs.blood_pressure }}</p>
{% endif %}
```

---

## Why This Approach?

### ✅ Benefits of JSON Storage

1. **No Schema Changes**: Uses existing `message` TEXT column
2. **Flexible**: Easy to add new EMR fields without migration
3. **Audit Trail**: Complete EMR snapshot at confirmation time
4. **Queryable**: Can extract data with JSON functions
5. **Portable**: Works on SQLite, MySQL, PostgreSQL

### ✅ Why Not Add Columns?

**Instead of this** (would need 20+ new columns):
```sql
ALTER TABLE patient ADD COLUMN medical_record_number VARCHAR(20);
ALTER TABLE patient ADD COLUMN id_number VARCHAR(10);
ALTER TABLE patient ADD COLUMN date_of_birth DATE;
ALTER TABLE patient ADD COLUMN blood_type VARCHAR(10);
ALTER TABLE patient ADD COLUMN height VARCHAR(20);
ALTER TABLE patient ADD COLUMN weight VARCHAR(20);
ALTER TABLE patient ADD COLUMN bmi VARCHAR(20);
ALTER TABLE patient ADD COLUMN temperature VARCHAR(20);
ALTER TABLE patient ADD COLUMN heart_rate VARCHAR(20);
ALTER TABLE patient ADD COLUMN blood_pressure VARCHAR(20);
ALTER TABLE patient ADD COLUMN respiratory_rate VARCHAR(20);
ALTER TABLE patient ADD COLUMN spo2 VARCHAR(20);
ALTER TABLE patient ADD COLUMN allergies TEXT;
ALTER TABLE patient ADD COLUMN medications TEXT;
ALTER TABLE patient ADD COLUMN surgery_date DATE;
ALTER TABLE patient ADD COLUMN surgeon VARCHAR(100);
ALTER TABLE patient ADD COLUMN department VARCHAR(100);
-- ... and more!
```

**We simply do this** (one column, stores everything):
```python
emr_snapshot = {...}  # All EMR data
ChatHistory(message_type='emr_snapshot', message=json.dumps(emr_snapshot))
```

---

## Summary Table

| Aspect | Status | Notes |
|--------|--------|-------|
| **New Tables** | ❌ None | Uses existing tables |
| **New Columns** | ❌ None | Uses existing columns |
| **Modified Columns** | ✅ 1 only | `message_type` VARCHAR(10)→VARCHAR(20) |
| **Fresh Linux Install** | ✅ Works | `init_db.py` creates correct schema |
| **Existing Database** | ⚠️ Migration | Run `expand_message_type_for_emr.py` |
| **Data Storage** | ✅ JSON | In `ChatHistory.message` column |
| **Schema Impact** | ✅ Minimal | No breaking changes |

---

## Common Questions

### Q1: Do I need to update my database on Linux?
**A:** No! If you're doing a fresh installation with `init_db.py`, the correct schema is created automatically.

### Q2: What if I already have data in production?
**A:** Run `migrations/expand_message_type_for_emr.py` to expand the `message_type` column.

### Q3: Will old data still work?
**A:** Yes! Existing records with `message_type` = 'user', 'bot', 'chat', 'summary' continue to work perfectly.

### Q4: Can I query EMR data with SQL?
**A:** Yes! Modern databases support JSON queries:
```sql
-- MySQL 5.7+
SELECT JSON_EXTRACT(message, '$.patient_demographics.patient_name')
FROM chat_history
WHERE message_type = 'emr_snapshot';

-- SQLite 3.38+
SELECT json_extract(message, '$.patient_demographics.patient_name')
FROM chat_history
WHERE message_type = 'emr_snapshot';
```

### Q5: What happens to vital signs data?
**A:** All vital signs are stored in the EMR snapshot JSON. Basic patient info (name, age, gender, surgery) is also duplicated in the Patient table for easy access.

---

## Files to Review

- **Schema Definition**: `models.py` (line 63)
- **Migration Script**: `migrations/expand_message_type_for_emr.py`
- **EMR Schema**: `emr_schema.py`
- **Usage Example**: `app_tocloud.py` (confirm_emr_data function)

---

**Last Updated**: 2025-10-22
**Status**: Ready for Linux deployment with `init_db.py`
