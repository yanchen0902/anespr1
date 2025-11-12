"""
EMR Snapshot Schema Definition
===============================
Defines the standardized JSON structure for storing EMR data in ChatHistory.

This schema is used when saving 'emr_snapshot' message_type to the database.
"""

from datetime import datetime
from typing import Dict, Any, Tuple

# EMR Snapshot Schema Version
SCHEMA_VERSION = "1.0.0"

# Example EMR Snapshot (for reference and testing)
EXAMPLE_EMR_SNAPSHOT = {
    "schema_version": SCHEMA_VERSION,
    "source": "hospital_emr",
    "fetched_at": "2025-10-22T15:30:00",
    "confirmed_at": "2025-10-22T15:35:00",
    "confirmed_by_patient": True,

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
        "surgery_time": "08:00",
        "surgery_name": "闌尾切除術",
        "surgery_name_en": "Appendectomy",
        "attending_surgeon": "陳醫師",
        "department": "一般外科",
        "preop_diagnosis": "急性闌尾炎",
        "anesthesia_type": "全身麻醉"
    },

    "vital_signs": {
        "height": "175 cm",
        "weight": "70 kg",
        "bmi": "22.86",
        "temperature": "36.5 °C",
        "heart_rate": "72 bpm",
        "blood_pressure": "120/80 mmHg",
        "respiratory_rate": "16 bpm",
        "spo2": "98%"
    },

    "medical_history": {
        "allergies": ["青黴素 (Penicillin)"],
        "medications": ["降血壓藥 (Antihypertensive)"],
        "past_surgeries": [],
        "chronic_conditions": ["高血壓 (Hypertension)"],
        "notes": ""
    }
}


def validate_emr_snapshot(snapshot_data: Dict[str, Any]) -> Tuple[bool, str]:
    """
    Validate EMR snapshot data against the schema.

    Args:
        snapshot_data: Dictionary containing EMR snapshot data

    Returns:
        Tuple of (is_valid, error_message)
    """
    required_sections = ['source', 'patient_demographics', 'surgery_info', 'vital_signs']

    for section in required_sections:
        if section not in snapshot_data:
            return False, f"Missing required section: {section}"

    # Validate patient demographics
    required_demo_fields = ['id_number', 'patient_name', 'date_of_birth', 'gender']
    for field in required_demo_fields:
        if field not in snapshot_data['patient_demographics']:
            return False, f"Missing required field: patient_demographics.{field}"

    # Validate surgery info
    required_surgery_fields = ['surgery_date', 'surgery_name', 'attending_surgeon']
    for field in required_surgery_fields:
        if field not in snapshot_data['surgery_info']:
            return False, f"Missing required field: surgery_info.{field}"

    return True, "Valid"


def create_empty_emr_snapshot(id_number: str) -> Dict[str, Any]:
    """
    Create an empty EMR snapshot template with minimal required fields.

    Args:
        id_number: Patient's National ID number

    Returns:
        Dictionary with empty EMR snapshot structure
    """
    return {
        "schema_version": SCHEMA_VERSION,
        "source": "manual_entry",
        "fetched_at": datetime.now().isoformat(),
        "confirmed_at": None,
        "confirmed_by_patient": False,

        "patient_demographics": {
            "medical_record_number": "",
            "id_number": id_number,
            "patient_name": "",
            "date_of_birth": "",
            "age": 0,
            "gender": "",
            "blood_type": ""
        },

        "surgery_info": {
            "surgery_date": "",
            "surgery_time": "",
            "surgery_name": "",
            "surgery_name_en": "",
            "attending_surgeon": "",
            "department": "",
            "preop_diagnosis": "",
            "anesthesia_type": ""
        },

        "vital_signs": {
            "height": "",
            "weight": "",
            "bmi": "",
            "temperature": "",
            "heart_rate": "",
            "blood_pressure": "",
            "respiratory_rate": "",
            "spo2": ""
        },

        "medical_history": {
            "allergies": [],
            "medications": [],
            "past_surgeries": [],
            "chronic_conditions": [],
            "notes": ""
        }
    }
