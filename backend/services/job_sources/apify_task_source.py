from typing import Dict, List, Optional, Tuple
import hashlib
import html
import json
import re
from urllib.parse import urlparse, parse_qsl, urlencode, urlunparse

import requests

from backend.config import APIFY_API_TOKEN
from backend.services.job_sources.job_normalizer import normalize_job


def clean_html_description(raw_description: str) -> str:
    """
    Converts HTML job descriptions into clean readable text.
    """

    if not raw_description:
        return ""

    text = re.sub(
        r"<script[\s\S]*?</script>",
        " ",
        raw_description,
        flags=re.IGNORECASE,
    )

    text = re.sub(
        r"<style[\s\S]*?</style>",
        " ",
        text,
        flags=re.IGNORECASE,
    )

    text = re.sub(r"<[^>]+>", " ", text)
    text = html.unescape(text)
    text = re.sub(r"\s+", " ", text)

    return text.strip()


def make_fallback_source_job_id(
    source: str,
    title: str,
    company: str,
    apply_url: str,
) -> str:
    """
    Creates a stable fallback job ID when Apify item does not provide one.
    """

    raw_value = f"{source}|{title}|{company}|{apply_url}".lower()

    return hashlib.sha256(
        raw_value.encode("utf-8")
    ).hexdigest()[:32]


def get_apify_task_input(task_id: str) -> Dict:
    """
    Reads the saved input of an Apify task.

    Important:
    Apify task input should be read from:
    /actor-tasks/{task_id}/input
    """

    if not APIFY_API_TOKEN:
        raise ValueError("APIFY_API_TOKEN is missing in .env file.")

    if not task_id:
        return {}

    url = f"https://api.apify.com/v2/actor-tasks/{task_id}/input"

    headers = {
        "Authorization": f"Bearer {APIFY_API_TOKEN}",
        "Accept": "application/json",
    }

    response = requests.get(
        url,
        headers=headers,
        timeout=60,
    )

    if not response.ok:
        print("Failed to read Apify task input.")
        print(f"Status code: {response.status_code}")
        print(f"Response: {response.text[:1000]}")

    response.raise_for_status()

    data = response.json()

    if not isinstance(data, dict):
        return {}

    return data


def update_job_search_url(
    url_value: str,
    search_query: Optional[str],
    location: Optional[str],
) -> Tuple[str, bool, bool]:
    """
    Updates Indeed/LinkedIn search URLs inside Apify task input.

    This helps when an Apify task stores search settings as startUrls.
    """

    if not url_value or not isinstance(url_value, str):
        return url_value, False, False

    lower_url = url_value.lower()

    if "indeed." not in lower_url and "linkedin." not in lower_url:
        return url_value, False, False

    parsed_url = urlparse(url_value)
    query_params = dict(
        parse_qsl(
            parsed_url.query,
            keep_blank_values=True,
        )
    )

    query_updated = False
    location_updated = False

    if search_query:
        if "indeed." in lower_url:
            query_params["q"] = search_query
            query_updated = True

        elif "linkedin." in lower_url:
            query_params["keywords"] = search_query
            query_updated = True

    if location:
        if "indeed." in lower_url:
            query_params["l"] = location
            location_updated = True

        elif "linkedin." in lower_url:
            query_params["location"] = location
            location_updated = True

    new_query = urlencode(
        query_params,
        doseq=True,
    )

    updated_url = urlunparse(
        parsed_url._replace(query=new_query)
    )

    return updated_url, query_updated, location_updated


def update_dynamic_input_fields(
    value,
    search_query: Optional[str],
    location: Optional[str],
    max_items: Optional[int],
) -> Tuple[object, bool, bool, bool]:
    """
    Recursively updates common job-search fields in Apify task input.

    Supports:
    - query fields
    - keyword fields
    - location fields
    - max item fields
    - Indeed/LinkedIn search URLs inside startUrls
    """

    query_keys = {
        "query",
        "queries",
        "search",
        "searchquery",
        "searchterm",
        "keyword",
        "keywords",
        "position",
        "jobtitle",
        "title",
        "what",
        "q",
    }

    location_keys = {
        "location",
        "locations",
        "where",
        "city",
        "place",
        "l",
    }

    max_item_keys = {
        "maxitems",
        "maxresults",
        "limit",
        "resultslimit",
        "rows",
        "maxitem",
        "maxitemspersearch",
        "count"
    }

    if isinstance(value, str):
        updated_url, query_updated, location_updated = update_job_search_url(
            url_value=value,
            search_query=search_query,
            location=location,
        )

        return updated_url, query_updated, location_updated, False

    query_updated = False
    location_updated = False
    max_updated = False

    if isinstance(value, dict):
        updated_dict = {}

        for key, child_value in value.items():
            normalized_key = (
                key.lower()
                .replace("_", "")
                .replace("-", "")
            )

            if search_query and normalized_key in query_keys:
                if isinstance(child_value, list):
                    updated_dict[key] = [search_query]
                else:
                    updated_dict[key] = search_query

                query_updated = True
                continue

            if location and normalized_key in location_keys:
                if isinstance(child_value, list):
                    updated_dict[key] = [location]
                else:
                    updated_dict[key] = location

                location_updated = True
                continue

            if max_items and normalized_key in max_item_keys:
                updated_dict[key] = max_items
                max_updated = True
                continue

            (
                updated_child,
                child_query_updated,
                child_location_updated,
                child_max_updated,
            ) = update_dynamic_input_fields(
                value=child_value,
                search_query=search_query,
                location=location,
                max_items=max_items,
            )

            updated_dict[key] = updated_child

            query_updated = query_updated or child_query_updated
            location_updated = location_updated or child_location_updated
            max_updated = max_updated or child_max_updated

        return updated_dict, query_updated, location_updated, max_updated

    if isinstance(value, list):
        updated_list = []

        for item in value:
            (
                updated_item,
                item_query_updated,
                item_location_updated,
                item_max_updated,
            ) = update_dynamic_input_fields(
                value=item,
                search_query=search_query,
                location=location,
                max_items=max_items,
            )

            updated_list.append(updated_item)

            query_updated = query_updated or item_query_updated
            location_updated = location_updated or item_location_updated
            max_updated = max_updated or item_max_updated

        return updated_list, query_updated, location_updated, max_updated

    return value, False, False, False
def normalize_apify_country_code(location: Optional[str]) -> str:
    """
    Converts location/country text into the country code expected by Apify actors.
    """

    if not location:
        return "US"

    cleaned_location = location.lower().strip()

    country_map = {
        "united states": "US",
        "usa": "US",
        "us": "US",
        "u.s.": "US",
        "u.s.a.": "US",
        "india": "IN",
        "canada": "CA",
        "united kingdom": "GB",
        "uk": "GB",
    }

    return country_map.get(cleaned_location, "US")

def build_dynamic_task_input(
    task_id: str,
    source: str,
    search_query: Optional[str],
    location: Optional[str],
    max_items: int,
) -> Dict:
    """
    Builds dynamic Apify task input.

    It first reads your saved Apify task input, then replaces search-related
    fields with the query typed by the user.
    """

    task_input = get_apify_task_input(
        task_id=task_id,
    )

    (
        updated_input,
        query_updated,
        location_updated,
        max_updated,
    ) = update_dynamic_input_fields(
        value=task_input,
        search_query=search_query,
        location=location,
        max_items=max_items,
    )

    if not isinstance(updated_input, dict):
        updated_input = {}

    source_lower = source.lower()

    if search_query and not query_updated:
        if "indeed" in source_lower:
            updated_input["position"] = search_query
            updated_input["query"] = search_query
            updated_input["what"] = search_query

        elif "linkedin" in source_lower:
            updated_input["keywords"] = search_query
            updated_input["query"] = search_query

        else:
            updated_input["query"] = search_query

    if location and not location_updated:
        updated_input["location"] = location

    if max_items and not max_updated:
        updated_input["maxItems"] = max_items

    if "indeed" in source_lower:
        updated_input["country"] = normalize_apify_country_code(location)
        updated_input["location"] = location or "United States"
        updated_input["position"] = search_query or updated_input.get("position", "")
        updated_input["maxItems"] = max_items
        updated_input["maxItemsPerSearch"] = max_items

    if "linkedin" in source_lower:
        linkedin_actor_min_count = max(10, max_items)

        updated_input["splitCountry"] = normalize_apify_country_code(location)
        updated_input["count"] = linkedin_actor_min_count
        updated_input["maxItems"] = max_items

    return updated_input

def run_apify_task(
    task_id: str,
    max_items: int = 25,
    source: str = "",
    search_query: Optional[str] = None,
    location: Optional[str] = None,
) -> List[Dict]:
    """
    Runs an Apify task synchronously and returns dataset items.

    If search_query is provided, this runs the task with dynamic input so the
    search behaves like LinkedIn/Indeed search.
    """

    if not APIFY_API_TOKEN:
        raise ValueError("APIFY_API_TOKEN is missing in .env file.")

    if not task_id:
        return []

    url = (
        f"https://api.apify.com/v2/actor-tasks/"
        f"{task_id}/run-sync-get-dataset-items"
    )

    headers = {
        "Authorization": f"Bearer {APIFY_API_TOKEN}",
        "Accept": "application/json",
        "Content-Type": "application/json",
    }

    params = {
        "clean": "true",
        "limit": max_items,
    }

    if search_query and search_query.strip():
        task_input = build_dynamic_task_input(
            task_id=task_id,
            source=source,
            search_query=search_query.strip(),
            location=location,
            max_items=max_items,
        )

        print("=" * 80)
        print("Running Apify task with dynamic search")
        print(f"Source: {source}")
        print(f"Search query: {search_query}")
        print(f"Location: {location}")
        print(f"Task input keys: {list(task_input.keys())}")
        print(f"Task input preview: {str(task_input)[:1500]}")
        print("=" * 80)

        response = requests.post(
            url,
            headers=headers,
            params=params,
            json=task_input,
            timeout=310,
        )

    else:
        response = requests.get(
            url,
            headers=headers,
            params=params,
            timeout=310,
        )

    if not response.ok:
        print("Apify task run failed.")
        print(f"Status code: {response.status_code}")
        print(f"Response: {response.text[:2000]}")

    response.raise_for_status()

    data = response.json()

    if not isinstance(data, list):
        print("Apify did not return a list.")
        print(f"Returned type: {type(data)}")
        print(f"Returned preview: {str(data)[:1000]}")
        return []

    valid_items = []

    for item in data:
        if isinstance(item, dict) and "error" in item:
            print(f"Apify task returned item error: {item.get('error')}")
            continue

        valid_items.append(item)

    print(f"Apify returned {len(valid_items)} valid raw items for {source}")

    return valid_items[:max_items]


def get_first_available_value(
    item: Dict,
    keys: List[str],
) -> Optional[str]:
    """
    Reads the first available value from a list of possible field names.
    """

    for key in keys:
        value = item.get(key)

        if value is not None and str(value).strip():
            return str(value).strip()

    return None


def normalize_apify_item(
    source: str,
    item: Dict,
) -> Dict:
    """
    Converts different Apify job result formats into our standard job format.
    """

    title = get_first_available_value(
        item,
        [
            "title",
            "jobTitle",
            "position",
            "positionName",
            "name",
        ],
    ) or ""

    company = get_first_available_value(
        item,
        [
            "company",
            "companyName",
            "employer",
            "employerName",
            "organization",
        ],
    ) or ""

    location = get_first_available_value(
        item,
        [
            "location",
            "jobLocation",
            "formattedLocation",
            "place",
            "candidateRequiredLocation",
        ],
    ) or "Remote"

    raw_description = get_first_available_value(
        item,
        [
            "description",
            "jobDescription",
            "descriptionText",
            "descriptionHtml",
            "details",
            "text",
        ],
    ) or ""

    description = clean_html_description(
        raw_description=raw_description,
    )

    apply_url = get_first_available_value(
        item,
        [
            "url",
            "jobUrl",
            "applyUrl",
            "link",
            "postingUrl",
        ],
    ) or ""

    source_job_id = get_first_available_value(
        item,
        [
            "id",
            "jobId",
            "jobKey",
            "postingId",
            "uid",
        ],
    )

    if not source_job_id:
        source_job_id = make_fallback_source_job_id(
            source=source,
            title=title,
            company=company,
            apply_url=apply_url,
        )

    return normalize_job(
        source=source,
        source_job_id=source_job_id,
        title=title,
        company=company,
        location=location,
        description=description,
        apply_url=apply_url,
    )


def fetch_jobs_from_apify_task(
    source: str,
    task_id: str,
    max_items: int = 25,
    search_query: Optional[str] = None,
    location: Optional[str] = None,
) -> List[Dict]:
    """
    Fetches jobs from one configured Apify task.
    """

    raw_items = run_apify_task(
        task_id=task_id,
        max_items=max_items,
        source=source,
        search_query=search_query,
        location=location,
    )

    normalized_jobs = []

    for item in raw_items:
        job = normalize_apify_item(
            source=source,
            item=item,
        )

        if not job["title"] or not job["company"]:
            continue

        normalized_jobs.append(job)

    return normalized_jobs