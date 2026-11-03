import os
from typing import Any

import streamlit as st
import earthaccess
import requests


def _read_secret(name: str) -> str | None:
    try:
        value = st.secrets.get(name)
    except Exception:
        value = None

    if value is None:
        return None

    if isinstance(value, str):
        stripped = value.strip()
        return stripped or None

    return str(value)


def _safe_status(label: str, ok: bool, detail: str) -> None:
    if ok:
        st.success(f"{label}: OK")
        if detail:
            st.caption(detail)
    else:
        st.error(f"{label}: Failed")
        if detail:
            st.caption(detail)


def _describe_auth_error(exc: Exception) -> str:
    message = str(exc).strip()
    if not message:
        return "Earthdata authentication failed."
    return message


def _normalize_temporal(date_value: str) -> tuple[str, str]:
    return (date_value, date_value)


st.set_page_config(page_title="Earthdata Test", page_icon="🛰️", layout="wide")
st.title("NASA Earthdata Diagnostic")

st.caption("Metadata-only diagnostic for Earthdata authentication and GPM IMERG Final Run discovery.")

username = _read_secret("EARTHDATA_USERNAME")
password = _read_secret("EARTHDATA_PASSWORD")

if not username or not password:
    st.warning("Missing NASA Earthdata credentials in Streamlit secrets.")
    st.info("Add the following to .streamlit/secrets.toml:\n\n[earthdata]\nEARTHDATA_USERNAME = \"your_username\"\nEARTHDATA_PASSWORD = \"your_password\"\n")
    st.stop()

# Never expose or print the actual values.
st.info("Earthdata credentials are present in secrets and are being used only for authentication.")

if st.button("Test NASA Earthdata Connection", type="primary"):
    auth_status = "Not attempted"
    dataset_status = "Not attempted"
    granule_count = 0
    granules: list[Any] = []
    auth_ok = False

    try:
        os.environ["EARTHDATA_USERNAME"] = username
        os.environ["EARTHDATA_PASSWORD"] = password

        auth = earthaccess.login(strategy="environment")
        auth_ok = bool(getattr(auth, "authenticated", False))
        if auth_ok:
            auth_status = "Authenticated successfully"
            _safe_status("Authentication status", True, "NASA Earthdata login succeeded via environment-based credentials.")
        else:
            auth_status = "Authentication did not report success"
            _safe_status("Authentication status", False, "The library did not report a successful Earthdata login.")
    except Exception as exc:
        auth_status = "Authentication failed"
        _safe_status("Authentication status", False, _describe_auth_error(exc))

    if auth_ok:
        try:
            dataset_status = "Searching..."
            st.info("Searching NASA CMR for GPM IMERG Final Run collection GPM_3IMERGDF v07 on 2025-08-01.")

            granules = earthaccess.search_data(
                short_name="GPM_3IMERGDF",
                version="07",
                temporal=("2025-08-01", "2025-08-02"),
                bounding_box=(60, 23, 78, 37),
            )

            dataset_status = "Search completed"
            granule_count = len(granules or [])

            if granule_count:
                _safe_status("Dataset search status", True, f"Found {granule_count} matching granule(s).")
            else:
                _safe_status("Dataset search status", False, "No granules matched the requested collection/date/bounding box.")
        except requests.exceptions.RequestException as exc:
            dataset_status = "Network error"
            _safe_status("Dataset search status", False, f"Network error while querying NASA CMR: {exc}")
        except Exception as exc:
            dataset_status = "Search failed"
            _safe_status("Dataset search status", False, f"Dataset search failed: {exc}")

    st.subheader("Results")
    st.write(f"Authentication status: {auth_status}")
    st.write(f"Dataset search status: {dataset_status}")
    st.write(f"Number of matching granules: {granule_count}")

    if granule_count:
        st.write("Available granule filenames and access links:")
        for i, granule in enumerate(granules[:20], start=1):
            try:
                name = getattr(granule, "title", None) or getattr(granule, "granule_name", None) or getattr(granule, "umm", {}).get("GranuleUR", "Unknown granule")
                links = getattr(granule, "data_links", None) or []
                if callable(links):
                    links = links()
                if isinstance(links, list):
                    display_links = [str(link) for link in links]
                else:
                    display_links = [str(links)] if links else []
                st.write(f"{i}. {name}")
                if display_links:
                    for link in display_links[:5]:
                        st.write(f"   - {link}")
                else:
                    st.write("   - No direct access links returned in metadata.")
            except Exception:
                st.write(f"{i}. Granule metadata returned but could not be rendered cleanly.")
