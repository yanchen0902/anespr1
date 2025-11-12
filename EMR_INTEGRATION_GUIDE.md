# EMR Integration Placeholder Structure
## Created: 2025-10-22

This document describes the placeholder structure created for future EMR (Electronic Medical Record) integration.

## Overview

The system is designed to fetch patient data from the hospital's EMR system using National ID (身份證字號), display it for confirmation, and then start the AI consultation with complete medical context.

## Patient Flow

```
1. Patient visits website
   ↓
2. Patient enters National ID on patient_id_input.html
   ↓
3. System fetches EMR data (currently mock, will be real EMR API)
   ↓
4. Display data on patient_emr_info.html for review
   ↓
5. Patient confirms data
   ↓
6. Save EMR snapshot to ChatHistory (message_type='emr_snapshot')
   ↓
7. Redirect to chatbot with full EMR context
```

## Files Created

### 1. `emr_schema.py`
**Purpose**: Defines the standardized JSON schema for EMR data storage

**Key Components**:
- `EXAMPLE_EMR_SNAPSHOT`: Reference example showing the complete data structure
- `validate_emr_snapshot()`: Validates EMR data against schema
- `create_empty_emr_snapshot()`: Creates empty template

**EMR Snapshot Structure**:
```python
{
    "schema_version": "1.0.0",
    "source": "hospital_emr",  # or "mock_emr", "manual_entry"
    "fetched_at": "ISO datetime",
    "confirmed_at": "ISO datetime",
    "confirmed_by_patient": boolean,

    "patient_demographics": {
        "medical_record_number": str,
        "id_number": str,  # National ID
        "patient_name": str,
        "date_of_birth": str,
        "age": int,
        "gender": str,
        "blood_type": str
    },

    "surgery_info": {
        "surgery_date": str,
        "surgery_time": str,
        "surgery_name": str,
        "surgery_name_en": str,
        "attending_surgeon": str,
        "department": str,
        "preop_diagnosis": str,
        "anesthesia_type": str
    },

    "vital_signs": {
        "height": str,
        "weight": str,
        "bmi": str,
        "temperature": str,
        "heart_rate": str,
        "blood_pressure": str,
        "respiratory_rate": str,
        "spo2": str
    },

    "medical_history": {
        "allergies": list,
        "medications": list,
        "past_surgeries": list,
        "chronic_conditions": list,
        "notes": str
    }
}
```

### 2. `emr_integration.py`
**Purpose**: Handles EMR API integration (currently placeholder/mock)

**Key Functions**:

#### `fetch_patient_from_emr(id_number, use_mock=True)`
- Main entry point for fetching patient data
- Currently returns mock data when `use_mock=True`
- **TODO**: Set `use_mock=False` when real EMR API is ready

#### `_fetch_real_patient_data(id_number)`
- **TODO**: Implement actual EMR API integration
- Handles authentication, API calls, error handling
- Placeholder structure ready for implementation

#### `_transform_emr_data(emr_response)`
- **TODO**: Map hospital's EMR field names to standardized schema
- Example mapping provided in code comments
- Needs customization based on actual EMR API response format

**Configuration (Environment Variables)**:
```env
EMR_API_URL=https://hospital-emr.example.com/api
EMR_API_KEY=your_api_key_here
EMR_API_TIMEOUT=30
```

**Error Handling**:
- `PatientNotFoundError`: Raised when patient not found in EMR
- `EMRAPIError`: Raised for API failures
- Graceful fallback mechanisms included

### 3. `models.py` (Modified)
**Changes Made**:
- Updated `ChatHistory.message_type` from `String(10)` to `String(20)`
- Added 'emr_snapshot' to allowed message types
- Comment updated: `# 'user', 'bot', 'chat', 'summary', or 'emr_snapshot'`

**Usage**:
```python
# Save EMR snapshot to database
emr_chat = ChatHistory(
    patient_id=patient_id,
    message_type='emr_snapshot',
    message=json.dumps(emr_snapshot_data),
    response=None
)
db.session.add(emr_chat)
db.session.commit()
```

### 4. `templates/patient_emr_info.html` (Modified)
**Changes Made**:
- Removed EVAN branding
- Converted all hardcoded data to Jinja2 template variables
- Added confirmation button at bottom
- Dynamic data binding for:
  - Patient demographics (name, gender, age, DOB, blood type, ID, MRN)
  - Surgery info (date, surgeon, procedure, diagnosis)
  - Vital signs (height, weight, BMI, temp, HR, BP, RR)

**Template Variables Used**:
```jinja2
{{ emr_data.patient_demographics.patient_name }}
{{ emr_data.patient_demographics.gender }}
{{ emr_data.patient_demographics.age }}
{{ emr_data.surgery_info.surgery_date }}
{{ emr_data.surgery_info.attending_surgeon }}
{{ emr_data.vital_signs.height }}
... and more
```

**Confirmation Button**:
- Form POST to `/confirm_emr_data` route
- Saves EMR snapshot and redirects to chatbot

## Existing Files (Already in Place)

### 5. `templates/patient_id_input.html`
**Purpose**: National ID input form

**Features**:
- Taiwan National ID format validation (e.g., A123456789)
- Mobile-responsive design
- Auto-uppercase first letter
- Form validation (client-side and server-side)

### 6. Flask Routes (in `app_tocloud.py`)

#### `/patient_id` (Already exists)
- **Method**: GET, POST
- **Function**: `patient_id_input()`
- **Current Implementation**: Calls `get_patient_by_national_id()` (mock function)
- **Status**: ✅ Working with existing mock data
- **TODO**: Already uses session to pass EMR data

#### `/patient_info` (Already exists)
- **Method**: GET
- **Function**: `patient_emr_info()`
- **Current Implementation**: Renders patient_emr_info.html with session data
- **Status**: ✅ Working
- **TODO**: Update to use `emr_data` template variable name for consistency

## Implementation Status

### ✅ Completed (Placeholder Structure)
1. EMR snapshot JSON schema defined (`emr_schema.py`)
2. ChatHistory model updated to support 'emr_snapshot' message type
3. EMR integration module created with mock/real API structure (`emr_integration.py`)
4. National ID lookup form exists (`patient_id_input.html`)
5. Patient EMR info display page updated with Jinja2 templating (`patient_emr_info.html`)
6. Confirmation button added to patient_emr_info.html

### 🚧 Pending (To Complete Integration)
1. Create `/confirm_emr_data` POST route (save EMR snapshot to ChatHistory)
2. Update existing routes to use new `emr_integration.py` module
3. Modify chatbot route to retrieve EMR snapshot from ChatHistory
4. Update `prompt_templates.py` to include EMR vital signs in AI prompts
5. Update admin dashboard to display EMR snapshot data
6. Update consultation summary to show EMR data
7. Add error handling for EMR API failures
8. Document complete workflow in CLAUDE.md

## How to Switch from Mock to Real EMR API

### Step 1: Configure Environment Variables
Add to `.env`:
```env
EMR_API_URL=https://your-hospital-emr.com/api
EMR_API_KEY=your_actual_api_key
EMR_API_TIMEOUT=30
```

### Step 2: Implement EMR API Integration
Edit `emr_integration.py`:

1. **Update `_fetch_real_patient_data()` function**:
   - Replace placeholder endpoint with actual EMR API endpoint
   - Implement correct authentication (API key, OAuth, etc.)
   - Handle EMR-specific response format

2. **Update `_transform_emr_data()` function**:
   - Map actual EMR field names to standardized schema
   - Handle data type conversions
   - Add data validation

### Step 3: Enable Real API Calls
Change in `app_tocloud.py` or `emr_integration.py`:
```python
# From:
emr_snapshot = fetch_patient_from_emr(national_id, use_mock=True)

# To:
emr_snapshot = fetch_patient_from_emr(national_id, use_mock=False)
```

### Step 4: Test with Real Data
1. Test National ID lookup with real patient
2. Verify data mapping is correct
3. Check error handling (invalid ID, API timeout, etc.)
4. Confirm EMR snapshot saves correctly to database

## Database Migration Needed?

**No migration needed!** The current implementation:
- Uses existing `ChatHistory` table
- Only requires increasing `message_type` column from `String(10)` to `String(20)`
- Stores EMR data as JSON in the `message` field

**Optional**: Run this SQL for existing databases:
```sql
-- For SQLite (development)
-- Not needed if you recreate the database

-- For MySQL (production)
ALTER TABLE chat_history MODIFY COLUMN message_type VARCHAR(20);
```

## Security Considerations

### Data Protection
- EMR data contains sensitive medical information (PHI/PII)
- Ensure HTTPS for all EMR API calls
- Store API keys securely (environment variables, not in code)
- Consider encrypting EMR snapshots in database

### Authentication
- Implement proper EMR API authentication
- Use token-based auth (OAuth 2.0) if available
- Rotate API keys regularly

### Access Control
- Only authorized personnel should access EMR snapshots
- Audit trail for who accessed what data
- Consider data retention policies

## Testing the Placeholder

### Test with Mock Data
1. Start the application:
   ```bash
   python app_tocloud.py
   ```

2. Visit: `http://localhost:8080/patient_id`

3. Enter test National ID: `A123456789`

4. Should see mock patient data displayed

5. Click "確認資料並開始諮詢"

6. **Expected**: EMR snapshot saved to ChatHistory, redirects to chatbot

## Next Steps for Full Implementation

### Immediate (Core Functionality)
1. **Create confirm_emr_data route** - Saves snapshot and starts consultation
2. **Integrate with chatbot** - Pass EMR context to AI prompts
3. **Update prompt templates** - Include vital signs in medical advice

### Short-term (Admin Features)
4. **Admin dashboard EMR display** - Show EMR snapshot in patient details
5. **Consultation summary updates** - Include EMR data in summary report

### Long-term (Production Readiness)
6. **Real EMR API integration** - Connect to hospital EMR system
7. **Error handling & fallbacks** - Handle API failures gracefully
8. **Security audit** - Ensure PHI/PII compliance
9. **Performance optimization** - Cache EMR data, optimize queries
10. **Documentation** - Complete user and technical documentation

## Questions to Clarify with Hospital IT

Before implementing real EMR integration, clarify:

1. **EMR System Details**:
   - What EMR system does the hospital use? (Epic, Cerner, custom, etc.)
   - Is there an existing API? What protocol? (FHIR, HL7, REST, SOAP)
   - API documentation available?

2. **Authentication**:
   - How to authenticate? (API key, OAuth, certificate, VPN only)
   - Where to get credentials?
   - Any rate limits or quotas?

3. **Data Access**:
   - What patient data can be accessed?
   - How to query by National ID?
   - Real-time vs. batch data?
   - Data refresh frequency?

4. **Compliance**:
   - Any PHI/PII regulations to follow?
   - Data retention policies?
   - Audit requirements?
   - Security certifications needed?

5. **Support**:
   - Technical contact for EMR API?
   - SLA for API availability?
   - How to report issues?

## Contact

For questions about this implementation:
- Review this document
- Check code comments in `emr_integration.py` and `emr_schema.py`
- See examples in `EXAMPLE_EMR_SNAPSHOT` variable

---

**Last Updated**: 2025-10-22
**Status**: Placeholder structure complete, ready for real EMR API integration
