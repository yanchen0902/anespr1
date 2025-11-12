"""
EMR Integration Module
======================
Handles integration with the hospital's EMR (Electronic Medical Record) system.

This module provides functions to:
- Fetch patient data from EMR API using National ID
- Transform EMR data to standardized format
- Handle EMR API errors and fallbacks

TODO: Replace placeholder functions with actual EMR API integration
"""

import os
import logging
import requests
from datetime import datetime
from typing import Dict, Any, Optional
from emr_schema import EXAMPLE_EMR_SNAPSHOT, create_empty_emr_snapshot

# Configure logging
logger = logging.getLogger(__name__)

# EMR API Configuration (load from environment variables)
EMR_API_URL = os.getenv('EMR_API_URL', 'https://hospital-emr.example.com/api')
EMR_API_KEY = os.getenv('EMR_API_KEY', '')
EMR_API_TIMEOUT = int(os.getenv('EMR_API_TIMEOUT', '30'))  # seconds


class EMRAPIError(Exception):
    """Custom exception for EMR API errors"""
    pass


class PatientNotFoundError(EMRAPIError):
    """Raised when patient is not found in EMR system"""
    pass


def fetch_patient_from_emr(id_number: str, use_mock: bool = True) -> Dict[str, Any]:
    """
    Fetch patient data from hospital EMR system using National ID.

    Args:
        id_number: Patient's National ID (身份證字號)
        use_mock: If True, return mock data instead of calling real API

    Returns:
        Dictionary containing standardized EMR snapshot

    Raises:
        PatientNotFoundError: If patient not found in EMR
        EMRAPIError: If API call fails
    """
    logger.info(f"Fetching EMR data for patient ID: {id_number}")

    if use_mock:
        # Return mock data for development/testing
        return _fetch_mock_patient_data(id_number)
    else:
        # Call real hospital EMR API
        return _fetch_real_patient_data(id_number)


def _fetch_mock_patient_data(id_number: str) -> Dict[str, Any]:
    """
    Return mock patient data for development/testing.

    TODO: Remove this function when real EMR integration is ready.

    Args:
        id_number: Patient's National ID

    Returns:
        Mock EMR snapshot data
    """
    logger.info(f"Using MOCK data for patient ID: {id_number}")

    # Return example snapshot with the provided ID number
    mock_data = EXAMPLE_EMR_SNAPSHOT.copy()
    mock_data['patient_demographics']['id_number'] = id_number
    mock_data['source'] = 'mock_emr'
    mock_data['fetched_at'] = datetime.now().isoformat()
    mock_data['confirmed_by_patient'] = False
    mock_data['confirmed_at'] = None

    return mock_data


def _fetch_real_patient_data(id_number: str) -> Dict[str, Any]:
    """
    Fetch patient data from real hospital EMR API.

    TODO: Implement actual EMR API integration here.

    This function should:
    1. Authenticate with EMR API (using API key, OAuth, etc.)
    2. Make API call to fetch patient data by National ID
    3. Transform EMR response to standardized format
    4. Handle errors and edge cases

    Args:
        id_number: Patient's National ID

    Returns:
        Standardized EMR snapshot

    Raises:
        PatientNotFoundError: If patient not found
        EMRAPIError: If API call fails
    """
    logger.info(f"Calling REAL EMR API for patient ID: {id_number}")

    try:
        # TODO: Replace with actual EMR API endpoint
        endpoint = f"{EMR_API_URL}/patients/by-national-id/{id_number}"

        headers = {
            'Authorization': f'Bearer {EMR_API_KEY}',
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        }

        response = requests.get(
            endpoint,
            headers=headers,
            timeout=EMR_API_TIMEOUT
        )

        # Handle HTTP errors
        if response.status_code == 404:
            logger.warning(f"Patient not found in EMR: {id_number}")
            raise PatientNotFoundError(f"查無此病患資料: {id_number}")

        if response.status_code != 200:
            logger.error(f"EMR API error: {response.status_code} - {response.text}")
            raise EMRAPIError(f"EMR API 錯誤: HTTP {response.status_code}")

        # Parse EMR response
        emr_data = response.json()

        # Transform to standardized format
        standardized_data = _transform_emr_data(emr_data)

        return standardized_data

    except requests.Timeout:
        logger.error("EMR API timeout")
        raise EMRAPIError("EMR 系統連線逾時，請稍後再試")

    except requests.RequestException as e:
        logger.error(f"EMR API request failed: {str(e)}")
        raise EMRAPIError(f"無法連線至 EMR 系統: {str(e)}")

    except Exception as e:
        logger.error(f"Unexpected error fetching EMR data: {str(e)}")
        raise EMRAPIError(f"取得病患資料時發生錯誤: {str(e)}")


def _transform_emr_data(emr_response: Dict[str, Any]) -> Dict[str, Any]:
    """
    Transform hospital EMR data format to standardized format.

    TODO: Implement data mapping based on actual EMR API response structure.

    This function maps the hospital's EMR field names to our standardized schema.

    Example EMR response structure (will vary by hospital):
    {
        "PatientID": "12345",
        "NationalID": "A123456789",
        "FullName": "王大明",
        "DOB": "1978-05-20",
        "Gender": "M",
        "ScheduledProcedure": {...},
        "VitalSigns": {...}
    }

    Args:
        emr_response: Raw response from EMR API

    Returns:
        Standardized EMR snapshot
    """
    # TODO: Map actual EMR fields to standardized schema
    # This is a placeholder implementation

    try:
        standardized = {
            "schema_version": "1.0.0",
            "source": "hospital_emr",
            "fetched_at": datetime.now().isoformat(),
            "confirmed_at": None,
            "confirmed_by_patient": False,

            "patient_demographics": {
                "medical_record_number": emr_response.get("PatientID", ""),
                "id_number": emr_response.get("NationalID", ""),
                "patient_name": emr_response.get("FullName", ""),
                "date_of_birth": _format_date(emr_response.get("DOB", "")),
                "age": emr_response.get("Age", 0),
                "gender": "男" if emr_response.get("Gender") == "M" else "女",
                "blood_type": emr_response.get("BloodType", "")
            },

            "surgery_info": {
                "surgery_date": _format_date(emr_response.get("ScheduledProcedure", {}).get("Date", "")),
                "surgery_time": emr_response.get("ScheduledProcedure", {}).get("Time", ""),
                "surgery_name": emr_response.get("ScheduledProcedure", {}).get("Name", ""),
                "surgery_name_en": emr_response.get("ScheduledProcedure", {}).get("NameEN", ""),
                "attending_surgeon": emr_response.get("ScheduledProcedure", {}).get("Surgeon", ""),
                "department": emr_response.get("ScheduledProcedure", {}).get("Department", ""),
                "preop_diagnosis": emr_response.get("ScheduledProcedure", {}).get("Diagnosis", ""),
                "anesthesia_type": emr_response.get("ScheduledProcedure", {}).get("AnesthesiaType", "")
            },

            "vital_signs": {
                "height": f"{emr_response.get('VitalSigns', {}).get('Height', '')} cm",
                "weight": f"{emr_response.get('VitalSigns', {}).get('Weight', '')} kg",
                "bmi": str(emr_response.get('VitalSigns', {}).get('BMI', '')),
                "temperature": f"{emr_response.get('VitalSigns', {}).get('Temperature', '')} °C",
                "heart_rate": f"{emr_response.get('VitalSigns', {}).get('HeartRate', '')} bpm",
                "blood_pressure": f"{emr_response.get('VitalSigns', {}).get('BP_Systolic', '')}/{emr_response.get('VitalSigns', {}).get('BP_Diastolic', '')} mmHg",
                "respiratory_rate": f"{emr_response.get('VitalSigns', {}).get('RespiratoryRate', '')} bpm",
                "spo2": f"{emr_response.get('VitalSigns', {}).get('SpO2', '')}%"
            },

            "medical_history": {
                "allergies": emr_response.get("Allergies", []),
                "medications": emr_response.get("CurrentMedications", []),
                "past_surgeries": emr_response.get("PastSurgeries", []),
                "chronic_conditions": emr_response.get("ChronicConditions", []),
                "notes": emr_response.get("Notes", "")
            }
        }

        return standardized

    except Exception as e:
        logger.error(f"Error transforming EMR data: {str(e)}")
        raise EMRAPIError(f"資料轉換錯誤: {str(e)}")


def _format_date(date_str: str) -> str:
    """
    Convert various date formats to YYYY/MM/DD format.

    Args:
        date_str: Date string in various formats (e.g., "2023-11-15", "2023/11/15")

    Returns:
        Formatted date string in YYYY/MM/DD format
    """
    if not date_str:
        return ""

    try:
        # Try parsing common formats
        for fmt in ["%Y-%m-%d", "%Y/%m/%d", "%Y%m%d"]:
            try:
                dt = datetime.strptime(date_str, fmt)
                return dt.strftime("%Y/%m/%d")
            except ValueError:
                continue

        # If no format matches, return original
        return date_str

    except Exception:
        return date_str


def check_emr_api_health() -> bool:
    """
    Check if EMR API is accessible and responding.

    Returns:
        True if EMR API is healthy, False otherwise
    """
    try:
        # TODO: Implement actual health check endpoint
        endpoint = f"{EMR_API_URL}/health"
        response = requests.get(endpoint, timeout=5)
        return response.status_code == 200

    except Exception as e:
        logger.warning(f"EMR API health check failed: {str(e)}")
        return False
