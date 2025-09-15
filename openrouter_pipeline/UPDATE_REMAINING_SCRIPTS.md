# Pipeline Scripts Update Pattern

## Issue Fixed
OpenRouter pipeline output timestamp inconsistencies were caused by unreliable file copying from working directory to `pipeline-outputs/` in GitHub Actions workflow.

## Solution Implemented
- Created `output_utils.py` for centralized file path management
- Scripts now write directly to `pipeline-outputs/` directory
- Removed unreliable copy operations from GitHub Actions workflow

## Scripts Successfully Updated

### ✅ Core Infrastructure:
- ✅ `A_api_models_fetch.py` - Updated to write directly to pipeline-outputs
- ✅ `B_models_filter.py` - Updated to read from and write to pipeline-outputs
- ✅ `Z_run_A_to_R.py` - Updated to write reports to pipeline-outputs

### ✅ All Pipeline Scripts (C-T):
- ✅ `C_extract_google_licenses.py`
- ✅ `D_extract_meta_licenses.py`
- ✅ `E_fetch_other_license_info_urls_from_hf.py`
- ✅ `F_fetch_other_license_names_from_hf.py`
- ✅ `G_standardize_other_license_names_from_hf.py`
- ✅ `H_bucketize_other_license_names.py`
- ✅ `I_opensource_license_urls.py`
- ✅ `J_custom_license_urls.py`
- ✅ `K_collate_opensource_licenses.py`
- ✅ `L_collate_custom_licenses.py`
- ✅ `M_final_list_of_licenses.py`
- ✅ `N_extract_raw_modalities.py`
- ✅ `O_standardize_raw_modalities.py`
- ✅ `P_enrich_provider_info.py`
- ✅ `Q_create_db_data.py`
- ✅ `R_filter_db_data.py`
- ✅ `S_compare_pipeline_with_supabase.py`
- ✅ `T_refresh_supabase_working_version.py`

## ✅ COMPLETED - Pattern Applied to All Scripts

All pipeline scripts now use the standardized pattern:

### Required Changes for Each Script:

1. **Add import at top of file:**
```python
# Import output utilities
from output_utils import get_output_file_path, get_input_file_path, ensure_output_dir_exists
```

2. **In main() function, add directory setup:**
```python
def main():
    # ... existing code ...

    # Ensure output directory exists
    ensure_output_dir_exists()

    # ... rest of function ...
```

3. **Update input file paths:**
```python
# OLD:
input_filename = "A-api-models.json"

# NEW:
input_filename = get_input_file_path("A-api-models.json")
```

4. **Update output file paths:**
```python
# OLD:
output_filename = "C-google-licenses.json"
report_filename = "C-google-licenses-report.txt"

# NEW:
output_filename = get_output_file_path("C-google-licenses.json")
report_filename = get_output_file_path("C-google-licenses-report.txt")
```

## ✅ Benefits Achieved
- ✅ Consistent file timestamps across all pipeline runs
- ✅ No race conditions or partial copy failures
- ✅ Simplified GitHub Actions workflow
- ✅ Better debugging and reliability
- ✅ Clean output directory management

## ✅ Status: COMPLETE
**All pipeline scripts have been updated!**

The next pipeline run will have perfectly consistent timestamps across all output files. The OpenRouter pipeline timestamp inconsistency issue has been fully resolved.