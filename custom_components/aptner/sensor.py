from __future__ import annotations

import re
from collections.abc import Callable
from dataclasses import dataclass
from datetime import date, datetime
from typing import Any

from homeassistant.components.sensor import SensorDeviceClass, SensorEntity, SensorEntityDescription
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import AptnerDataUpdateCoordinator

DEVICE_GROUP_NAMES_BY_LANGUAGE: dict[str, dict[str, str]] = {
    "en": {
        "overview": "Overview",
        "community": "Community",
        "schedule": "Schedule",
        "parking": "Parking",
        "safety": "Safety",
        "household": "Household",
        "billing": "Billing",
    },
    "ko": {
        "overview": "개요",
        "community": "커뮤니티",
        "schedule": "일정",
        "parking": "주차",
        "safety": "안전",
        "household": "세대",
        "billing": "관리비",
    },
}

SENSOR_UNITS_BY_LANGUAGE: dict[str, dict[str, str]] = {
    "en": {
        "usage_services": "services",
        "notice_count": "items",
        "community_count": "items",
        "complaint_count": "items",
        "defect_count": "items",
        "region_count": "items",
        "schedule_count": "items",
        "schedule_next_day": "day",
        "vote_current_count": "items",
        "vote_closed_count": "items",
        "survey_ing_count": "items",
        "survey_done_count": "items",
        "aptner_notice_count": "items",
        "contacts_count": "items",
        "broadcast_count": "items",
        "guest_parking_count": "items",
        "guest_parking_history_count": "items",
        "guest_parking_household_limit": "mins",
        "guest_parking_remaining_free": "uses",
        "parking_discount_history_count": "items",
        "visit_vehicle_usage_count": "items",
        "visit_vehicle_valid_count": "items",
        "realtor_count": "items",
        "fire_inspection_history_count": "items",
        "household_member_count": "people",
        "household_verified_count": "people",
        "management_fee_area": "m²",
        "management_fee_breakdown_count": "items",
        "management_fee_history_count": "periods",
    },
    "ko": {
        "usage_services": "개",
        "notice_count": "건",
        "community_count": "건",
        "complaint_count": "건",
        "defect_count": "건",
        "region_count": "건",
        "schedule_count": "건",
        "schedule_next_day": "일",
        "vote_current_count": "건",
        "vote_closed_count": "건",
        "survey_ing_count": "건",
        "survey_done_count": "건",
        "aptner_notice_count": "건",
        "contacts_count": "건",
        "broadcast_count": "건",
        "guest_parking_count": "건",
        "guest_parking_history_count": "건",
        "guest_parking_household_limit": "분",
        "guest_parking_remaining_free": "회",
        "parking_discount_history_count": "건",
        "visit_vehicle_usage_count": "건",
        "visit_vehicle_valid_count": "건",
        "realtor_count": "건",
        "fire_inspection_history_count": "건",
        "household_member_count": "명",
        "household_verified_count": "명",
        "management_fee_area": "m²",
        "management_fee_breakdown_count": "건",
        "management_fee_history_count": "기",
    },
}

SENSOR_PRECISION_BY_KEY: dict[str, int] = {
    "usage_services": 0,
    "notice_count": 0,
    "community_count": 0,
    "complaint_count": 0,
    "defect_count": 0,
    "region_count": 0,
    "schedule_count": 0,
    "schedule_next_day": 0,
    "vote_current_count": 0,
    "vote_closed_count": 0,
    "survey_ing_count": 0,
    "survey_done_count": 0,
    "aptner_notice_count": 0,
    "contacts_count": 0,
    "broadcast_count": 0,
    "guest_parking_count": 0,
    "guest_parking_history_count": 0,
    "guest_parking_household_limit": 0,
    "guest_parking_remaining_free": 0,
    "parking_discount_history_count": 0,
    "visit_vehicle_usage_count": 0,
    "visit_vehicle_valid_count": 0,
    "realtor_count": 0,
    "fire_inspection_history_count": 0,
    "household_member_count": 0,
    "household_verified_count": 0,
    "management_fee": 0,
    "management_fee_average": 0,
    "management_fee_area": 2,
    "management_fee_current_late_fee": 0,
    "management_fee_delinquent_fee": 0,
    "management_fee_delinquent_late_fee": 0,
    "management_fee_breakdown_count": 0,
    "management_fee_previous": 0,
    "management_fee_change": 0,
    "management_fee_history_count": 0,
}

OVERVIEW_KEYS = {
    "apartment",
    "apartment_phone",
    "usage_services",
}

COMMUNITY_KEYS = {
    "notice_count",
    "latest_notice_title",
    "latest_notice_date",
    "community_count",
    "latest_community_title",
    "complaint_count",
    "latest_complaint_title",
    "latest_complaint_status",
    "defect_count",
    "region_count",
    "latest_region_title",
    "aptner_notice_count",
    "aptner_notice_latest_title",
    "contacts_count",
    "primary_contact",
    "broadcast_count",
    "broadcast_latest",
    "realtor_count",
}

SCHEDULE_KEYS = {
    "schedule_count",
    "schedule_next_day",
    "vote_current_count",
    "vote_closed_count",
    "survey_ing_count",
    "survey_done_count",
}

PARKING_KEYS = {
    "guest_parking_count",
    "guest_parking_history_count",
    "guest_parking_household_limit",
    "guest_parking_remaining_free",
    "parking_discount_history_count",
    "parking_vehicle_inside",
    "parking_vehicle_last_event_entry",
    "parking_vehicle_last_event_exit",
    "visit_vehicle_usage_count",
    "visit_vehicle_valid_count",
    "visit_vehicle_next_date",
    "visit_vehicle_next_car_no",
    "visit_vehicle_next_purpose",
    "visit_vehicle_alert",
    "visit_vehicle_today",
}

SAFETY_KEYS = {
    "fire_inspection",
    "fire_inspection_history_count",
}

HOUSEHOLD_KEYS = {
    "household_member_count",
    "household_verified_count",
}


def _device_group_for_key(entity_key: str) -> str:
    if entity_key in OVERVIEW_KEYS:
        return "overview"
    if entity_key in COMMUNITY_KEYS:
        return "community"
    if entity_key in SCHEDULE_KEYS:
        return "schedule"
    if entity_key in PARKING_KEYS:
        return "parking"
    if entity_key in SAFETY_KEYS:
        return "safety"
    if entity_key in HOUSEHOLD_KEYS:
        return "household"
    if entity_key.startswith("management_fee"):
        return "billing"
    return "overview"


def _preferred_language(hass: HomeAssistant) -> str:
    language = getattr(hass.config, "language", None)
    if not isinstance(language, str) or not language:
        return "en"
    language_code = language.split("-", maxsplit=1)[0].lower()
    if language_code in DEVICE_GROUP_NAMES_BY_LANGUAGE:
        return language_code
    return "en"


def _localized_group_name(hass: HomeAssistant, group_key: str) -> str:
    language = _preferred_language(hass)
    return DEVICE_GROUP_NAMES_BY_LANGUAGE[language].get(
        group_key,
        DEVICE_GROUP_NAMES_BY_LANGUAGE["en"][group_key],
    )


def _localized_sensor_unit(hass: HomeAssistant, entity_key: str) -> str | None:
    language = _preferred_language(hass)
    unit_map = SENSOR_UNITS_BY_LANGUAGE.get(language, SENSOR_UNITS_BY_LANGUAGE["en"])
    if entity_key in unit_map:
        return unit_map[entity_key]
    return SENSOR_UNITS_BY_LANGUAGE["en"].get(entity_key)


def _device_info_for_key(
    hass: HomeAssistant,
    entry_id: str,
    data: dict[str, Any],
    entity_key: str,
) -> DeviceInfo:
    apartment_name = _apartment_name_value(data) or "Aptner"
    group_key = _device_group_for_key(entity_key)
    group_name = _localized_group_name(hass, group_key)

    if group_key == "overview":
        return DeviceInfo(
            identifiers={(DOMAIN, entry_id)},
            name=apartment_name,
            model="Aptner",
        )

    return DeviceInfo(
        identifiers={(DOMAIN, f"{entry_id}_{group_key}")},
        name=f"{apartment_name} {group_name}",
        model=f"Aptner {group_name}",
        via_device=(DOMAIN, entry_id),
    )


def _error_text(payload: Any) -> str | None:
    if isinstance(payload, dict):
        error = payload.get("_error")
        if isinstance(error, str):
            return error
    return None


def _attributes_dict(payload: Any) -> dict[str, Any]:
    if payload is None:
        return {}
    if isinstance(payload, dict):
        return dict(payload)
    return {"value": payload}


def _board_articles(payload: Any) -> list[dict[str, Any]]:
    if not isinstance(payload, dict):
        return []
    articles = payload.get("articleList")
    return articles if isinstance(articles, list) else []


def _board_count(payload: Any) -> int | None:
    if _error_text(payload):
        return None
    if not isinstance(payload, dict):
        return None
    total = payload.get("totalArticles")
    if isinstance(total, int):
        return total
    return len(_board_articles(payload))


def _broadcast_list_payload(payload: Any) -> dict[str, Any]:
    if not isinstance(payload, dict):
        return {}
    listing = payload.get("list")
    return listing if isinstance(listing, dict) else {}


def _broadcast_count(payload: Any) -> int | None:
    if _error_text(payload):
        return None
    listing = _broadcast_list_payload(payload)
    total = listing.get("totalCount")
    if isinstance(total, int):
        return total
    return len(_list_or_empty(listing, "articleList"))


def _broadcast_latest_title(payload: Any) -> str | None:
    if _error_text(payload):
        return None
    if isinstance(payload, dict):
        latest = payload.get("latest")
        if isinstance(latest, dict):
            title = latest.get("title")
            if isinstance(title, str) and title:
                return title
    listing = _broadcast_list_payload(payload)
    articles = _list_or_empty(listing, "articleList")
    if articles and isinstance(articles[0], dict):
        title = articles[0].get("title")
        if isinstance(title, str) and title:
            return title
    return None


def _vote_list(payload: Any) -> list[dict[str, Any]]:
    if not isinstance(payload, dict):
        return []
    vote_list = payload.get("voteList")
    return vote_list if isinstance(vote_list, list) else []


def _vote_count(payload: Any) -> int | None:
    if _error_text(payload):
        return None
    if not isinstance(payload, dict):
        return None
    total = payload.get("totalElements")
    if isinstance(total, int):
        return total
    return len(_vote_list(payload))


def _survey_list(payload: Any) -> list[dict[str, Any]]:
    if not isinstance(payload, dict):
        return []
    survey_list = payload.get("pollList") or payload.get("surveyList")
    return survey_list if isinstance(survey_list, list) else []


def _list_or_empty(payload: Any, key: str) -> list[dict[str, Any]]:
    if not isinstance(payload, dict):
        return []
    items = payload.get(key)
    return items if isinstance(items, list) else []


def _first_dict_item(payload: Any, key: str) -> dict[str, Any] | None:
    items = _list_or_empty(payload, key)
    if items and isinstance(items[0], dict):
        return items[0]
    return None


def _first_string_value(item: dict[str, Any], *keys: str) -> str | None:
    for key in keys:
        value = item.get(key)
        if isinstance(value, str) and value:
            return value
    return None


def _recent_string_values(
    items: list[dict[str, Any]],
    *keys: str,
    limit: int = 5,
) -> list[str]:
    values: list[str] = []
    for item in items:
        if not isinstance(item, dict):
            continue
        value = _first_string_value(item, *keys)
        if value is None:
            continue
        values.append(value)
        if len(values) >= limit:
            break
    return values


def _recent_id_values(
    items: list[dict[str, Any]],
    *keys: str,
    limit: int = 5,
) -> list[str]:
    values: list[str] = []
    for item in items:
        if not isinstance(item, dict):
            continue
        for key in keys:
            value = item.get(key)
            if isinstance(value, (int, str)) and str(value):
                values.append(str(value))
                break
        if len(values) >= limit:
            break
    return values


def _latest_board_title(payload: Any) -> str | None:
    if _error_text(payload):
        return None
    latest = _first_dict_item(payload, "articleList")
    if latest is None:
        return None
    title = latest.get("title")
    return title if isinstance(title, str) else None


def _latest_board_date(payload: Any) -> str | None:
    if _error_text(payload):
        return None
    latest = _first_dict_item(payload, "articleList")
    if latest is None:
        return None
    for key in ("postDateFormatted", "regDateFormatted", "postDate", "regDate"):
        value = latest.get(key)
        if isinstance(value, str) and value:
            return value
    return None


def _latest_board_status(payload: Any) -> str | None:
    if _error_text(payload):
        return None
    latest = _first_dict_item(payload, "articleList")
    if latest is None:
        return None
    status = latest.get("status")
    return status if isinstance(status, str) else None


def _aptner_notice_count(payload: Any) -> int | None:
    if _error_text(payload):
        return None
    return len(_list_or_empty(payload, "noticeList"))


def _latest_aptner_notice_title(payload: Any) -> str | None:
    if _error_text(payload):
        return None
    latest = _first_dict_item(payload, "noticeList")
    if latest is None:
        return None
    title = latest.get("title")
    return title if isinstance(title, str) else None


def _schedule_next_day(payload: Any) -> int | None:
    if _error_text(payload):
        return None
    events = _list_or_empty(payload, "events")
    days = []
    for event in events:
        day = event.get("day")
        if isinstance(day, int):
            days.append(day)
    if not days:
        return None
    return min(days)


def _board_attributes(payload: Any) -> dict[str, Any]:
    attrs = _attributes_dict(payload)
    articles = _board_articles(payload)
    attrs["article_count"] = _board_count(payload)
    attrs["latest_article"] = _first_dict_item(payload, "articleList")
    attrs["latest_title"] = _latest_board_title(payload)
    attrs["latest_date"] = _latest_board_date(payload)
    attrs["latest_status"] = _latest_board_status(payload)
    attrs["has_articles"] = bool(articles)
    attrs["recent_titles"] = _recent_string_values(articles, "title", "subject", "name")
    attrs["recent_article_ids"] = _recent_id_values(
        articles,
        "id",
        "articleId",
        "idx",
        "postId",
    )
    return attrs


def _aptner_notice_attributes(payload: Any) -> dict[str, Any]:
    attrs = _attributes_dict(payload)
    latest_notice = _first_dict_item(payload, "noticeList")
    attrs["notice_count"] = _aptner_notice_count(payload)
    attrs["latest_notice"] = latest_notice
    attrs["latest_title"] = _latest_aptner_notice_title(payload)
    return attrs


def _schedule_next_event(payload: Any) -> dict[str, Any] | None:
    next_day = _schedule_next_day(payload)
    if next_day is None:
        return None
    for event in _list_or_empty(payload, "events"):
        if isinstance(event, dict) and event.get("day") == next_day:
            return event
    return None


def _schedule_attributes(payload: Any) -> dict[str, Any]:
    attrs = _attributes_dict(payload)
    events = _list_or_empty(payload, "events")
    today_day = date.today().day
    today_events = [
        event
        for event in events
        if isinstance(event, dict) and event.get("day") == today_day
    ]
    upcoming_events = [
        event
        for event in events
        if isinstance(event, dict)
        and isinstance(event.get("day"), int)
        and event.get("day") >= today_day
    ]
    next_event = _schedule_next_event(payload)
    attrs["event_count"] = len(events)
    attrs["event_days"] = sorted(
        {day for event in events if isinstance(event, dict) and isinstance((day := event.get("day")), int)}
    )
    attrs["next_day"] = _schedule_next_day(payload)
    attrs["next_event"] = next_event
    attrs["next_event_title"] = (
        _first_string_value(next_event, "title", "subject", "name")
        if isinstance(next_event, dict)
        else None
    )
    attrs["today_event_count"] = len(today_events)
    attrs["today_events"] = today_events
    attrs["upcoming_event_count"] = len(upcoming_events)
    attrs["event_titles"] = _recent_string_values(upcoming_events or events, "title", "subject", "name")
    return attrs


def _vote_attributes(payload: Any) -> dict[str, Any]:
    attrs = _attributes_dict(payload)
    votes = _vote_list(payload)
    latest_vote = votes[0] if votes and isinstance(votes[0], dict) else None
    attrs["vote_count"] = _vote_count(payload)
    attrs["latest_vote"] = latest_vote
    attrs["latest_title"] = (
        _first_string_value(latest_vote, "title", "subject", "question")
        if isinstance(latest_vote, dict)
        else None
    )
    attrs["has_votes"] = bool(votes)
    attrs["vote_titles"] = _recent_string_values(votes, "title", "subject", "question")
    attrs["vote_ids"] = _recent_id_values(votes, "voteId", "id", "idx")
    return attrs


def _survey_attributes(payload: Any) -> dict[str, Any]:
    attrs = _attributes_dict(payload)
    surveys = _survey_list(payload)
    latest_survey = surveys[0] if surveys and isinstance(surveys[0], dict) else None
    attrs["survey_count"] = len(surveys) if not _error_text(payload) else None
    attrs["latest_survey"] = latest_survey
    attrs["latest_title"] = (
        _first_string_value(latest_survey, "title", "subject", "question")
        if isinstance(latest_survey, dict)
        else None
    )
    attrs["has_surveys"] = bool(surveys)
    attrs["survey_titles"] = _recent_string_values(surveys, "title", "subject", "question")
    attrs["survey_ids"] = _recent_id_values(surveys, "pollId", "surveyId", "id", "idx")
    return attrs


def _usage_service_attributes(payload: Any) -> dict[str, Any]:
    attrs = _attributes_dict(payload)
    services = _list_or_empty(payload, "services")
    attrs["service_count"] = len(services)
    attrs["service_names"] = [
        name
        for service in services
        if isinstance(service, dict)
        for key in ("name", "serviceName", "serviceType", "type")
        if isinstance((name := service.get(key)), str) and name
    ]
    return attrs


def _contacts_attributes(payload: Any) -> dict[str, Any]:
    attrs = _attributes_dict(payload)
    contacts = _list_or_empty(payload, "contactList")
    attrs["contact_count"] = len(contacts)
    attrs["primary_contact"] = _primary_contact_value(payload)
    attrs["primary_contact_data"] = contacts[0] if contacts and isinstance(contacts[0], dict) else None
    attrs["contact_titles"] = _recent_string_values(contacts, "title", "name", "department")
    attrs["contact_numbers"] = _recent_string_values(contacts, "tel", "phone", "mobile")
    return attrs


def _broadcast_attributes(payload: Any) -> dict[str, Any]:
    attrs = _attributes_dict(payload)
    listing = _broadcast_list_payload(payload)
    articles = _list_or_empty(listing, "articleList")
    latest_list_item = articles[0] if articles and isinstance(articles[0], dict) else None
    attrs["broadcast_count"] = _broadcast_count(payload)
    attrs["latest_title"] = _broadcast_latest_title(payload)
    attrs["latest_list_item"] = latest_list_item
    attrs["latest_date"] = (
        _first_string_value(latest_list_item, "regDateFormatted", "postDateFormatted", "regDate", "postDate")
        if isinstance(latest_list_item, dict)
        else None
    )
    attrs["has_broadcasts"] = bool(articles)
    attrs["recent_titles"] = _recent_string_values(articles, "title", "subject")
    if isinstance(payload, dict):
        attrs["latest_article"] = payload.get("latest")
    return attrs


def _guest_parking_reservations(payload: Any) -> list[dict[str, Any]]:
    return _list_or_empty(payload, "reserveList")


def _parse_parking_history_datetime(value: Any) -> datetime | None:
    if not isinstance(value, str) or not value:
        return None
    for fmt in ("%Y.%m.%d %H:%M", "%Y-%m-%d %H:%M", "%Y.%m.%d", "%Y-%m-%d"):
        try:
            return datetime.strptime(value, fmt)
        except ValueError:
            continue
    return None


def _guest_parking_history_items(payload: Any) -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []
    for parent in _list_or_empty(payload, "monthlyParkingHistoryList"):
        if not isinstance(parent, dict):
            continue
        for item in _list_or_empty(parent, "visitCarUseHistoryReportList"):
            if not isinstance(item, dict):
                continue
            normalized = dict(item)
            normalized["year"] = parent.get("year")
            normalized["month"] = parent.get("month")
            normalized["month_remaining_free"] = parent.get("remainedFreeParkingCount")
            items.append(normalized)
    return items


def _guest_parking_event_timestamp(item: dict[str, Any]) -> datetime | None:
    if item.get("isExit") is True:
        return _parse_parking_history_datetime(item.get("outDatetime")) or _parse_parking_history_datetime(
            item.get("inDatetime")
        )
    return _parse_parking_history_datetime(item.get("inDatetime")) or _parse_parking_history_datetime(
        item.get("outDatetime")
    )


def _guest_parking_active_items(payload: Any) -> list[dict[str, Any]]:
    return [
        item
        for item in _guest_parking_history_items(payload)
        if item.get("isExit") is False
    ]


def _guest_parking_latest_event(payload: Any) -> dict[str, Any] | None:
    items = _guest_parking_history_items(payload)
    if not items:
        return None
    latest_item = max(
        items,
        key=lambda item: (
            _guest_parking_event_timestamp(item) or datetime.min,
            str(item.get("carNo") or ""),
        ),
    )
    event_type = "exit" if latest_item.get("isExit") is True else "entry"
    event_at = _guest_parking_event_timestamp(latest_item)
    return {
        "type": event_type,
        "at": event_at.isoformat(sep=" ") if event_at is not None else None,
        "item": latest_item,
    }


def _guest_parking_active_count(payload: Any) -> int | None:
    if _error_text(payload):
        return None
    return len(_guest_parking_active_items(payload))


def _guest_parking_count_value(payload: Any) -> int | None:
    if _error_text(payload):
        return None
    if isinstance(payload, dict):
        total = payload.get("totalReserves")
        if isinstance(total, int):
            return total
    return len(_guest_parking_reservations(payload))


def _guest_parking_attributes(payload: Any) -> dict[str, Any]:
    attrs = _attributes_dict(payload)
    reservations = _guest_parking_reservations(payload)
    config = payload.get("visitConfig") if isinstance(payload, dict) else None
    next_reservation = reservations[0] if reservations and isinstance(reservations[0], dict) else None
    attrs["reservation_count"] = _guest_parking_count_value(payload)
    attrs["latest_reservation"] = next_reservation
    attrs["next_reservation"] = next_reservation
    attrs["reservation_dates"] = _recent_string_values(
        reservations,
        "visitDate",
        "visit_date",
        "inDate",
        "date",
    )
    attrs["reserved_car_numbers"] = _recent_string_values(reservations, "carNo", "car_no")
    if isinstance(config, dict):
        attrs["visit_config"] = config
        attrs["household_limit"] = config.get("availableHouseHoldLimit")
        attrs["car_limit"] = config.get("parkingReserveCarLimit")
        attrs["exit_camera_exists"] = config.get("isExitCameraExist")
    elif isinstance(payload, dict):
        attrs["visit_config"] = payload.get("visitConfig")
    return attrs


def _guest_parking_history_attributes(payload: Any) -> dict[str, Any]:
    attrs = _attributes_dict(payload)
    history = _list_or_empty(payload, "monthlyParkingHistoryList")
    history_items = _guest_parking_history_items(payload)
    active_items = _guest_parking_active_items(payload)
    latest_event = _guest_parking_latest_event(payload)
    attrs["history_count"] = len(history)
    attrs["latest_history"] = history[0] if history and isinstance(history[0], dict) else None
    attrs["history_item_count"] = len(history_items)
    attrs["active_parking_count"] = len(active_items)
    attrs["active_vehicles"] = active_items
    attrs["active_car_numbers"] = list(
        dict.fromkeys(
            item.get("carNo")
            for item in active_items
            if isinstance(item.get("carNo"), str) and item.get("carNo")
        )
    )
    attrs["latest_event"] = latest_event
    attrs["latest_event_type"] = latest_event.get("type") if isinstance(latest_event, dict) else None
    attrs["latest_event_at"] = latest_event.get("at") if isinstance(latest_event, dict) else None
    attrs["latest_event_item"] = latest_event.get("item") if isinstance(latest_event, dict) else None
    attrs["has_active_vehicle"] = bool(active_items)
    attrs["active_unique_count"] = len(attrs["active_car_numbers"])
    attrs["latest_active_vehicle"] = active_items[0] if active_items and isinstance(active_items[0], dict) else None
    attrs["history_periods"] = [
        f"{parent.get('year')}-{int(parent.get('month')):02d}"
        for parent in history
        if isinstance(parent, dict)
        and isinstance(parent.get("year"), int)
        and isinstance(parent.get("month"), int)
    ]
    if isinstance(latest_event, dict):
        latest_item = latest_event.get("item")
        latest_car_no = (
            latest_item.get("carNo")
            if isinstance(latest_item, dict) and isinstance(latest_item.get("carNo"), str)
            else None
        )
        event_type = latest_event.get("type")
        event_at = latest_event.get("at")
        if latest_car_no and isinstance(event_type, str):
            attrs["latest_event_summary"] = (
                f"{event_type} {latest_car_no} @ {event_at}"
                if isinstance(event_at, str) and event_at
                else f"{event_type} {latest_car_no}"
            )
        else:
            attrs["latest_event_summary"] = None
    else:
        attrs["latest_event_summary"] = None
    attrs["remaining_free"] = _guest_parking_remaining_free(payload)
    return attrs


def _parking_discount_attributes(payload: Any) -> dict[str, Any]:
    attrs = _attributes_dict(payload)
    history = _list_or_empty(payload, "historyList")
    amounts = [
        amount
        for item in history
        if isinstance(item, dict)
        and (amount := _parse_int(item.get("amount") or item.get("price"))) is not None
    ]
    latest_history = history[0] if history and isinstance(history[0], dict) else None
    attrs["history_count"] = len(history)
    attrs["latest_history"] = latest_history
    attrs["latest_amount"] = (
        _parse_int(latest_history.get("amount") or latest_history.get("price"))
        if isinstance(latest_history, dict)
        else None
    )
    attrs["total_amount"] = sum(amounts)
    attrs["history_car_numbers"] = _recent_string_values(history, "carNo", "car_no")
    return attrs


def _realtor_attributes(payload: Any) -> dict[str, Any]:
    attrs = _attributes_dict(payload)
    articles = _list_or_empty(payload, "articles")
    attrs["article_count"] = len(articles)
    attrs["latest_article"] = articles[0] if articles and isinstance(articles[0], dict) else None
    return attrs


def _management_fee_value(payload: Any) -> int | None:
    if _error_text(payload):
        return None
    if not isinstance(payload, dict):
        return None

    latest_period = payload.get("latest_period") if isinstance(payload.get("latest_period"), dict) else {}
    details = payload.get("details") if isinstance(payload.get("details"), list) else []

    candidates = [
        latest_period.get("current_fee"),
        latest_period.get("currentFee"),
    ]
    if details and isinstance(details[0], dict):
        candidates.extend(
            [
                details[0].get("currentFee"),
                details[0].get("current_fee"),
            ]
        )

    for value in candidates:
        parsed = _parse_int(value)
        if parsed is not None:
            return parsed
    return None


def _management_fee_period(payload: Any) -> str | None:
    if _error_text(payload):
        return None
    if not isinstance(payload, dict):
        return None
    latest_period = payload.get("latest_period")
    if not isinstance(latest_period, dict):
        return None
    year = latest_period.get("year")
    month = latest_period.get("month")
    if year is None or month is None:
        return None
    return f"{year}-{month:02d}" if isinstance(month, int) else f"{year}-{month}"


def _management_fee_average_value(payload: Any) -> int | None:
    if _error_text(payload):
        return None
    if not isinstance(payload, dict):
        return None
    latest_detail = payload.get("latest_detail")
    if not isinstance(latest_detail, dict):
        return None
    return _parse_int(latest_detail.get("currentFeeAverage"))


def _management_fee_periods(payload: Any) -> list[dict[str, Any]]:
    if not isinstance(payload, dict):
        return []
    periods = payload.get("periods")
    return periods if isinstance(periods, list) else []


def _management_fee_period_item(payload: Any, index: int) -> dict[str, Any] | None:
    periods = _management_fee_periods(payload)
    if 0 <= index < len(periods) and isinstance(periods[index], dict):
        return periods[index]
    return None


def _management_fee_period_string(item: dict[str, Any] | None) -> str | None:
    if not isinstance(item, dict):
        return None
    year = item.get("year")
    month = item.get("month")
    if year is None or month is None:
        return None
    month_text = f"{int(month):02d}" if isinstance(month, (int, str)) and str(month).isdigit() else str(month)
    return f"{year}-{month_text}"


def _management_fee_period_value(payload: Any, index: int) -> int | None:
    if _error_text(payload):
        return None
    item = _management_fee_period_item(payload, index)
    if item is None:
        return None
    for key in ("current_fee", "currentFee"):
        value = _parse_int(item.get(key))
        if value is not None:
            return value
    return None


def _management_fee_period_label(payload: Any, index: int) -> str | None:
    if _error_text(payload):
        return None
    return _management_fee_period_string(_management_fee_period_item(payload, index))


def _management_fee_history_count(payload: Any) -> int | None:
    if _error_text(payload):
        return None
    return len(_management_fee_periods(payload))


def _management_fee_history_summary(payload: Any) -> list[dict[str, Any]]:
    if _error_text(payload):
        return []
    summary: list[dict[str, Any]] = []
    for item in _management_fee_periods(payload):
        if not isinstance(item, dict):
            continue
        summary.append(
            {
                "period": _management_fee_period_string(item),
                "value": _parse_int(item.get("current_fee") or item.get("currentFee")),
                "value_raw": item.get("current_fee") or item.get("currentFee"),
                "id": item.get("id"),
            }
        )
    return summary


def _management_fee_previous_value(payload: Any) -> int | None:
    return _management_fee_period_value(payload, 1)


def _management_fee_previous_period(payload: Any) -> str | None:
    return _management_fee_period_label(payload, 1)


def _management_fee_change_value(payload: Any) -> int | None:
    current_value = _management_fee_value(payload)
    previous_value = _management_fee_previous_value(payload)
    if current_value is None or previous_value is None:
        return None
    return current_value - previous_value


def _management_fee_detail(payload: Any) -> dict[str, Any]:
    if not isinstance(payload, dict):
        return {}
    latest_detail = payload.get("latest_detail")
    return latest_detail if isinstance(latest_detail, dict) else {}


def _split_csv_field(value: Any) -> list[str]:
    if not isinstance(value, str) or not value:
        return []
    return [item.strip() for item in value.split(",")]


def _management_fee_breakdown(payload: Any) -> dict[str, dict[str, Any]]:
    breakdown: dict[str, dict[str, Any]] = {}
    for item in _management_fee_breakdown_items(payload):
        label = item.get("label")
        if not isinstance(label, str):
            continue
        breakdown[label] = {
            "index": item.get("index"),
            "value_raw": item.get("value_raw"),
            "value": item.get("value"),
            "average_raw": item.get("average_raw"),
            "average": item.get("average"),
        }
    return breakdown


def _management_fee_breakdown_items(payload: Any) -> list[dict[str, Any]]:
    detail = _management_fee_detail(payload)
    labels = _split_csv_field(detail.get("etcItem"))
    values = _split_csv_field(detail.get("etcContents"))
    averages = _split_csv_field(detail.get("etcItemAverage"))

    breakdown: list[dict[str, Any]] = []
    for idx, label in enumerate(labels):
        if not label:
            continue
        raw_value = values[idx] if idx < len(values) else None
        raw_average = averages[idx] if idx < len(averages) else None
        breakdown.append(
            {
                "index": idx,
                "label": label,
                "value_raw": raw_value,
                "value": _parse_int(raw_value),
                "average_raw": raw_average,
                "average": _parse_int(raw_average),
            }
        )
    return breakdown


def _management_fee_breakdown_count(payload: Any) -> int | None:
    if _error_text(payload):
        return None
    return len(_management_fee_breakdown_items(payload))


def _management_fee_breakdown_item(payload: Any, index: int) -> dict[str, Any] | None:
    for item in _management_fee_breakdown_items(payload):
        if item.get("index") == index:
            return item
    return None


def _management_fee_text_field(payload: Any, field: str) -> str | None:
    if _error_text(payload):
        return None
    detail = _management_fee_detail(payload)
    value = detail.get(field)
    return value if isinstance(value, str) else None


def _management_fee_money_field(payload: Any, field: str) -> int | None:
    if _error_text(payload):
        return None
    detail = _management_fee_detail(payload)
    return _parse_int(detail.get(field))


def _management_fee_area_float(payload: Any) -> float | None:
    if _error_text(payload):
        return None
    detail = _management_fee_detail(payload)
    return _parse_float(detail.get("area"))


def _management_fee_delta(value: int | None, average: int | None) -> int | None:
    if value is None or average is None:
        return None
    return value - average


def _management_fee_summary(payload: Any) -> dict[str, Any]:
    current_fee = _management_fee_value(payload)
    current_fee_average = _management_fee_average_value(payload)
    previous_fee = _management_fee_previous_value(payload)
    current_late_fee = _management_fee_money_field(payload, "currentLateFee")
    delinquent_fee = _management_fee_money_field(payload, "delinquentFee")
    delinquent_late_fee = _management_fee_money_field(payload, "delinquentLateFee")

    return {
        "period": _management_fee_period(payload),
        "previous_period": _management_fee_previous_period(payload),
        "period_count": _management_fee_history_count(payload),
        "area_square_meter": _management_fee_area_float(payload),
        "current_fee": current_fee,
        "current_fee_average": current_fee_average,
        "current_fee_delta": _management_fee_delta(current_fee, current_fee_average),
        "previous_fee": previous_fee,
        "period_change": _management_fee_change_value(payload),
        "current_late_fee": current_late_fee,
        "delinquent_fee": delinquent_fee,
        "delinquent_late_fee": delinquent_late_fee,
        "total_outstanding": sum(
            value or 0
            for value in (
                current_late_fee,
                delinquent_fee,
                delinquent_late_fee,
            )
        ),
        "history": _management_fee_history_summary(payload),
    }


def _management_fee_entity_items(data: dict[str, Any]) -> list[dict[str, Any]]:
    return _management_fee_breakdown_items(data.get("management_fee"))


def _management_fee_entity_label(item: dict[str, Any], fallback_index: int) -> str:
    label = item.get("label")
    if isinstance(label, str) and label:
        return label
    return f"Breakdown {fallback_index + 1}"


def _management_fee_entity_index(item: dict[str, Any], fallback_index: int) -> int:
    index = item.get("index")
    return index if isinstance(index, int) else fallback_index


def _management_fee_attributes(payload: Any) -> dict[str, Any]:
    if payload is None:
        return {}
    if not isinstance(payload, dict):
        return {"value": payload}

    detail = _management_fee_detail(payload)
    breakdown_items = _management_fee_breakdown_items(payload)
    summary = _management_fee_summary(payload)
    attrs = dict(payload)
    attrs["breakdown"] = _management_fee_breakdown(payload)
    attrs["breakdown_items"] = breakdown_items
    attrs["breakdown_count"] = len(breakdown_items)
    attrs["breakdown_value_total"] = sum(
        item.get("value") or 0
        for item in breakdown_items
        if isinstance(item.get("value"), int)
    )
    attrs["breakdown_average_total"] = sum(
        item.get("average") or 0
        for item in breakdown_items
        if isinstance(item.get("average"), int)
    )
    top_breakdown_item = max(
        breakdown_items,
        key=lambda item: item.get("value") if isinstance(item.get("value"), int) else -1,
        default=None,
    )
    attrs["top_breakdown_item"] = top_breakdown_item
    attrs["top_breakdown_label"] = (
        top_breakdown_item.get("label") if isinstance(top_breakdown_item, dict) else None
    )
    attrs["top_breakdown_value"] = (
        top_breakdown_item.get("value") if isinstance(top_breakdown_item, dict) else None
    )
    attrs["latest_detail"] = detail
    attrs["summary"] = summary
    attrs.update(summary)
    period_change = summary.get("period_change")
    attrs["change_direction"] = (
        "increase"
        if isinstance(period_change, int) and period_change > 0
        else "decrease"
        if isinstance(period_change, int) and period_change < 0
        else "same"
        if period_change == 0
        else None
    )
    attrs["has_outstanding_balance"] = bool(summary.get("total_outstanding"))
    return attrs


def _parse_int(value: Any) -> int | None:
    if isinstance(value, int):
        return value
    if isinstance(value, str):
        digits = re.sub(r"[^0-9]", "", value)
        if digits:
            return int(digits)
    return None


def _parse_float(value: Any) -> float | None:
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        cleaned = re.sub(r"[^0-9.\\-]", "", value)
        if cleaned:
            try:
                return float(cleaned)
            except ValueError:
                return None
    return None


def _fire_status_value(payload: Any) -> str | None:
    if _error_text(payload):
        return None
    if not isinstance(payload, dict):
        return None
    inspection = payload.get("currentInspection") or payload.get("inspection")
    if not isinstance(inspection, dict):
        return "none"
    completed = inspection.get("hasResponse")
    if completed is None:
        completed = inspection.get("isCompleted")
    return "completed" if completed else "open"


def _fire_history_list(payload: Any) -> list[dict[str, Any]]:
    if not isinstance(payload, dict):
        return []
    inspections = payload.get("inspections") or payload.get("data")
    return inspections if isinstance(inspections, list) else []


def _fire_status_attributes(payload: Any) -> dict[str, Any]:
    attrs = _attributes_dict(payload)
    inspection = None
    if isinstance(payload, dict):
        inspection = payload.get("currentInspection") or payload.get("inspection")
    attrs["state"] = _fire_status_value(payload)
    attrs["current_inspection"] = inspection if isinstance(inspection, dict) else None
    attrs["has_active_inspection"] = isinstance(inspection, dict)
    return attrs


def _fire_history_attributes(payload: Any) -> dict[str, Any]:
    attrs = _attributes_dict(payload)
    history = _fire_history_list(payload)
    attrs["history_count"] = len(history)
    attrs["latest_response"] = history[0] if history and isinstance(history[0], dict) else None
    return attrs


def _feature_attributes(payload: Any) -> dict[str, Any]:
    return _attributes_dict(payload)


def _user_attributes(data: dict[str, Any]) -> dict[str, Any]:
    attrs = dict(data.get("user") or {})
    attrs["usage_services"] = data.get("usage_services")
    attrs["metadata"] = data.get("metadata")
    return attrs


def _apartment_phone_value(data: dict[str, Any]) -> str | None:
    apartment = data.get("apartment")
    if not isinstance(apartment, dict):
        return None
    tel = apartment.get("tel")
    return tel if isinstance(tel, str) else None


def _apartment_name_value(data: dict[str, Any]) -> str | None:
    apartment = data.get("apartment")
    if not isinstance(apartment, dict):
        return None
    name = apartment.get("name")
    return name if isinstance(name, str) else None


def _usage_service_count(payload: Any) -> int | None:
    if _error_text(payload):
        return None
    services = _list_or_empty(payload, "services")
    return len(services)


def _primary_contact_value(payload: Any) -> str | None:
    if _error_text(payload):
        return None
    contact = _first_dict_item(payload, "contactList")
    if contact is None:
        return None
    title = contact.get("title")
    tel = contact.get("tel")
    if isinstance(title, str) and isinstance(tel, str):
        return f"{title} ({tel})"
    if isinstance(title, str):
        return title
    if isinstance(tel, str):
        return tel
    return None


def _guest_parking_household_limit(payload: Any) -> int | None:
    if _error_text(payload):
        return None
    if not isinstance(payload, dict):
        return None
    config = payload.get("visitConfig")
    if not isinstance(config, dict):
        return None
    limit = config.get("availableHouseHoldLimit")
    return limit if isinstance(limit, int) else None


def _guest_parking_remaining_free(payload: Any) -> int | None:
    if _error_text(payload):
        return None
    latest = _first_dict_item(payload, "monthlyParkingHistoryList")
    if latest is None:
        return None
    return _parse_int(latest.get("remainedFreeParkingCount"))


def _visit_items(payload: Any) -> list[dict[str, Any]]:
    items = _list_or_empty(payload, "Item")
    if items:
        return items
    return _list_or_empty(payload, "visitList")


def _visit_valid_count(payload: Any) -> int | None:
    if _error_text(payload):
        return None
    count = 0
    for item in _visit_items(payload):
        if item.get("is_valid") == "Y":
            count += 1
    return count


def _visit_valid_items(payload: Any) -> list[dict[str, Any]]:
    if _error_text(payload):
        return []
    return [
        item
        for item in _visit_items(payload)
        if isinstance(item, dict) and item.get("is_valid") == "Y"
    ]


def _parse_visit_date(value: Any) -> date | None:
    if not isinstance(value, str) or not value:
        return None
    for fmt in ("%Y-%m-%d", "%Y%m%d"):
        try:
            return datetime.strptime(value, fmt).date()
        except ValueError:
            continue
    if re.fullmatch(r"\d{4}-\d{2}-\d{2}.*", value):
        try:
            return datetime.strptime(value[:10], "%Y-%m-%d").date()
        except ValueError:
            return None
    compact_match = re.match(r"^(\d{4})(\d{2})(\d{2})", value)
    if compact_match:
        try:
            year = int(compact_match.group(1))
            month = int(compact_match.group(2))
            day = int(compact_match.group(3))
            return date(year, month, day)
        except ValueError:
            return None
    return None


def _visit_next_item(payload: Any) -> dict[str, Any] | None:
    if _error_text(payload):
        return None
    items = _visit_items(payload)
    if items and isinstance(items[0], dict):
        return items[0]
    return None


def _visit_next_date(payload: Any) -> str | None:
    next_item = _visit_next_item(payload)
    if next_item is None:
        return None
    value = next_item.get("visit_date")
    return value if isinstance(value, str) else None


def _visit_next_car_no(payload: Any) -> str | None:
    next_item = _visit_next_item(payload)
    if next_item is None:
        return None
    value = next_item.get("car_no")
    return value if isinstance(value, str) else None


def _visit_next_purpose(payload: Any) -> str | None:
    next_item = _visit_next_item(payload)
    if next_item is None:
        return None
    value = next_item.get("visit_purpose")
    return value if isinstance(value, str) else None


def _visit_today_item(payload: Any) -> dict[str, Any] | None:
    today = date.today()
    for item in _visit_valid_items(payload):
        if _parse_visit_date(item.get("visit_date")) == today:
            return item
    return None


def _visit_today_items(payload: Any) -> list[dict[str, Any]]:
    today = date.today()
    return [
        item
        for item in _visit_valid_items(payload)
        if _parse_visit_date(item.get("visit_date")) == today
    ]


def _visit_usage_attributes(payload: Any) -> dict[str, Any]:
    if payload is None:
        return {}
    if not isinstance(payload, dict):
        return {"value": payload}

    items = _visit_items(payload)
    valid_items = _visit_valid_items(payload)
    today_items = _visit_today_items(payload)
    today_item = today_items[0] if today_items else None
    next_reservation = _visit_next_item(payload)
    next_reservation_date = (
        _parse_visit_date(next_reservation.get("visit_date"))
        if isinstance(next_reservation, dict)
        else None
    )
    attrs = dict(payload)
    attrs["reservation_count"] = len(items)
    attrs["valid_count"] = len(valid_items)
    attrs["expired_count"] = max(len(items) - len(valid_items), 0)
    attrs["valid_reservations"] = valid_items
    attrs["next_reservation"] = next_reservation
    attrs["next_days_until"] = (
        (next_reservation_date - date.today()).days
        if isinstance(next_reservation_date, date)
        else None
    )
    attrs["today_reservation"] = today_item
    attrs["today_reservations"] = today_items
    attrs["today_count"] = len(today_items)
    attrs["has_today_reservation"] = today_item is not None
    attrs["upcoming_dates"] = _recent_string_values(valid_items, "visit_date")
    attrs["upcoming_car_numbers"] = _recent_string_values(valid_items, "car_no")
    return attrs


def _household_member_count(payload: Any) -> int | None:
    if _error_text(payload):
        return None
    return len(_list_or_empty(payload, "householdMemberList"))


def _verified_household_member_count(payload: Any) -> int | None:
    if _error_text(payload):
        return None
    members = _list_or_empty(payload, "householdMemberList")
    count = 0
    for member in members:
        if member.get("verified") or member.get("isResidenceVerified") or member.get("isOwnerVerified"):
            count += 1
    return count


def _household_attributes(payload: Any) -> dict[str, Any]:
    attrs = _attributes_dict(payload)
    members = _list_or_empty(payload, "householdMemberList")
    attrs["member_count"] = _household_member_count(payload)
    attrs["verified_count"] = _verified_household_member_count(payload)
    attrs["verified_members"] = [
        member
        for member in members
        if isinstance(member, dict)
        and (
            member.get("verified")
            or member.get("isResidenceVerified")
            or member.get("isOwnerVerified")
        )
    ]
    attrs["primary_member"] = members[0] if members and isinstance(members[0], dict) else None
    return attrs


def _parking_discount_history_count(payload: Any) -> int | None:
    if _error_text(payload):
        return None
    return len(_list_or_empty(payload, "historyList"))


def _visit_vehicle_usage_count(payload: Any) -> int | None:
    if _error_text(payload):
        return None
    items = _list_or_empty(payload, "Item")
    if items:
        return len(items)
    return len(_list_or_empty(payload, "visitList"))


@dataclass(frozen=True, kw_only=True)
class AptnerSensorDescription(SensorEntityDescription):
    value_fn: Callable[[dict[str, Any]], Any]
    attributes_fn: Callable[[dict[str, Any]], dict[str, Any]] = lambda data: {}

    def __post_init__(self) -> None:
        if self.translation_key is None:
            object.__setattr__(self, "translation_key", self.key)
        object.__setattr__(self, "name", None)


SENSORS: tuple[AptnerSensorDescription, ...] = (
    AptnerSensorDescription(
        key="apartment",
        name="Apartment",
        icon="mdi:office-building",
        value_fn=_apartment_name_value,
        attributes_fn=_user_attributes,
    ),
    AptnerSensorDescription(
        key="apartment_phone",
        name="Apartment Phone",
        icon="mdi:phone",
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=_apartment_phone_value,
        attributes_fn=lambda data: dict(data.get("apartment") or {}),
    ),
    AptnerSensorDescription(
        key="usage_services",
        name="Enabled Usage Services",
        icon="mdi:apps",
        value_fn=lambda data: _usage_service_count(data.get("usage_services")),
        attributes_fn=lambda data: _usage_service_attributes(data.get("usage_services")),
    ),
    AptnerSensorDescription(
        key="notice_count",
        name="Notice Count",
        icon="mdi:bullhorn",
        value_fn=lambda data: _board_count(data.get("board_notice")),
        attributes_fn=lambda data: _board_attributes(data.get("board_notice")),
    ),
    AptnerSensorDescription(
        key="latest_notice_title",
        name="Latest Notice",
        icon="mdi:text-box-outline",
        value_fn=lambda data: _latest_board_title(data.get("board_notice")),
        attributes_fn=lambda data: _board_attributes(data.get("board_notice")),
    ),
    AptnerSensorDescription(
        key="latest_notice_date",
        name="Latest Notice Date",
        icon="mdi:calendar-clock",
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda data: _latest_board_date(data.get("board_notice")),
        attributes_fn=lambda data: _board_attributes(data.get("board_notice")),
    ),
    AptnerSensorDescription(
        key="community_count",
        name="Community Count",
        icon="mdi:account-group",
        value_fn=lambda data: _board_count(data.get("board_community")),
        attributes_fn=lambda data: _board_attributes(data.get("board_community")),
    ),
    AptnerSensorDescription(
        key="latest_community_title",
        name="Latest Community Post",
        icon="mdi:forum-outline",
        value_fn=lambda data: _latest_board_title(data.get("board_community")),
        attributes_fn=lambda data: _board_attributes(data.get("board_community")),
    ),
    AptnerSensorDescription(
        key="complaint_count",
        name="Complaint Count",
        icon="mdi:alert-box-outline",
        value_fn=lambda data: _board_count(data.get("board_complaint")),
        attributes_fn=lambda data: _board_attributes(data.get("board_complaint")),
    ),
    AptnerSensorDescription(
        key="latest_complaint_title",
        name="Latest Complaint",
        icon="mdi:message-alert-outline",
        value_fn=lambda data: _latest_board_title(data.get("board_complaint")),
        attributes_fn=lambda data: _board_attributes(data.get("board_complaint")),
    ),
    AptnerSensorDescription(
        key="latest_complaint_status",
        name="Latest Complaint Status",
        icon="mdi:progress-clock",
        value_fn=lambda data: _latest_board_status(data.get("board_complaint")),
        attributes_fn=lambda data: _board_attributes(data.get("board_complaint")),
    ),
    AptnerSensorDescription(
        key="defect_count",
        name="Defect Count",
        icon="mdi:home-repair-service",
        value_fn=lambda data: _board_count(data.get("board_defect")),
        attributes_fn=lambda data: _board_attributes(data.get("board_defect")),
    ),
    AptnerSensorDescription(
        key="region_count",
        name="Region Board Count",
        icon="mdi:map-marker-radius",
        value_fn=lambda data: _board_count(data.get("board_region")),
        attributes_fn=lambda data: _board_attributes(data.get("board_region")),
    ),
    AptnerSensorDescription(
        key="latest_region_title",
        name="Latest Region Post",
        icon="mdi:map-search-outline",
        value_fn=lambda data: _latest_board_title(data.get("board_region")),
        attributes_fn=lambda data: _board_attributes(data.get("board_region")),
    ),
    AptnerSensorDescription(
        key="schedule_count",
        name="Schedule Count",
        icon="mdi:calendar-month",
        value_fn=lambda data: len(_list_or_empty(data.get("schedule"), "events")) if not _error_text(data.get("schedule")) else None,
        attributes_fn=lambda data: _schedule_attributes(data.get("schedule")),
    ),
    AptnerSensorDescription(
        key="schedule_next_day",
        name="Next Schedule Day",
        icon="mdi:calendar-arrow-right",
        value_fn=lambda data: _schedule_next_day(data.get("schedule")),
        attributes_fn=lambda data: _schedule_attributes(data.get("schedule")),
    ),
    AptnerSensorDescription(
        key="vote_current_count",
        name="Current Vote Count",
        icon="mdi:vote",
        value_fn=lambda data: _vote_count(data.get("vote_current")),
        attributes_fn=lambda data: _vote_attributes(data.get("vote_current")),
    ),
    AptnerSensorDescription(
        key="vote_closed_count",
        name="Closed Vote Count",
        icon="mdi:vote-outline",
        value_fn=lambda data: _vote_count(data.get("vote_closed")),
        attributes_fn=lambda data: _vote_attributes(data.get("vote_closed")),
    ),
    AptnerSensorDescription(
        key="survey_ing_count",
        name="Ongoing Survey Count",
        icon="mdi:clipboard-text-clock",
        value_fn=lambda data: len(_survey_list(data.get("survey_ing"))) if not _error_text(data.get("survey_ing")) else None,
        attributes_fn=lambda data: _survey_attributes(data.get("survey_ing")),
    ),
    AptnerSensorDescription(
        key="survey_done_count",
        name="Completed Survey Count",
        icon="mdi:clipboard-check-outline",
        value_fn=lambda data: len(_survey_list(data.get("survey_done"))) if not _error_text(data.get("survey_done")) else None,
        attributes_fn=lambda data: _survey_attributes(data.get("survey_done")),
    ),
    AptnerSensorDescription(
        key="aptner_notice_count",
        name="Aptner Notice Count",
        icon="mdi:information-outline",
        value_fn=lambda data: _aptner_notice_count(data.get("aptner_notice")),
        attributes_fn=lambda data: _aptner_notice_attributes(data.get("aptner_notice")),
    ),
    AptnerSensorDescription(
        key="aptner_notice_latest_title",
        name="Latest Aptner Notice",
        icon="mdi:message-text-outline",
        value_fn=lambda data: _latest_aptner_notice_title(data.get("aptner_notice")),
        attributes_fn=lambda data: _aptner_notice_attributes(data.get("aptner_notice")),
    ),
    AptnerSensorDescription(
        key="contacts_count",
        name="Contact Count",
        icon="mdi:card-account-phone",
        value_fn=lambda data: len(_list_or_empty(data.get("contacts"), "contactList")) if not _error_text(data.get("contacts")) else None,
        attributes_fn=lambda data: _contacts_attributes(data.get("contacts")),
    ),
    AptnerSensorDescription(
        key="primary_contact",
        name="Primary Contact",
        icon="mdi:phone-in-talk",
        value_fn=lambda data: _primary_contact_value(data.get("contacts")),
        attributes_fn=lambda data: _contacts_attributes(data.get("contacts")),
    ),
    AptnerSensorDescription(
        key="broadcast_count",
        name="Apartment Broadcast Count",
        icon="mdi:bullhorn-variant",
        value_fn=lambda data: _broadcast_count(data.get("broadcast")),
        attributes_fn=lambda data: _broadcast_attributes(data.get("broadcast")),
    ),
    AptnerSensorDescription(
        key="broadcast_latest",
        name="Latest Apartment Broadcast",
        icon="mdi:account-voice",
        value_fn=lambda data: _broadcast_latest_title(data.get("broadcast")),
        attributes_fn=lambda data: _broadcast_attributes(data.get("broadcast")),
    ),
    AptnerSensorDescription(
        key="guest_parking_count",
        name="Guest Parking Count",
        icon="mdi:car-clock",
        value_fn=lambda data: (
            data.get("guest_parking", {}).get("totalReserves")
            if isinstance(data.get("guest_parking"), dict) and isinstance(data.get("guest_parking", {}).get("totalReserves"), int)
            else len(_list_or_empty(data.get("guest_parking"), "reserveList"))
            if not _error_text(data.get("guest_parking"))
            else None
        ),
        attributes_fn=lambda data: _guest_parking_attributes(data.get("guest_parking")),
    ),
    AptnerSensorDescription(
        key="guest_parking_history_count",
        name="Guest Parking History Count",
        icon="mdi:car-search",
        value_fn=lambda data: len(_list_or_empty(data.get("guest_parking_history"), "monthlyParkingHistoryList")) if not _error_text(data.get("guest_parking_history")) else None,
        attributes_fn=lambda data: _guest_parking_history_attributes(data.get("guest_parking_history")),
    ),
    AptnerSensorDescription(
        key="guest_parking_household_limit",
        name="Guest Parking Household Limit",
        icon="mdi:counter",
        value_fn=lambda data: _guest_parking_household_limit(data.get("guest_parking")),
        attributes_fn=lambda data: _guest_parking_attributes(data.get("guest_parking")),
    ),
    AptnerSensorDescription(
        key="guest_parking_remaining_free",
        name="Guest Parking Remaining Free",
        icon="mdi:ticket-percent-outline",
        value_fn=lambda data: _guest_parking_remaining_free(data.get("guest_parking_history")),
        attributes_fn=lambda data: _guest_parking_history_attributes(data.get("guest_parking_history")),
    ),
    AptnerSensorDescription(
        key="parking_discount_history_count",
        name="Parking Payment History Count",
        icon="mdi:cash-clock",
        value_fn=lambda data: _parking_discount_history_count(data.get("parking_discount_history")),
        attributes_fn=lambda data: _parking_discount_attributes(data.get("parking_discount_history")),
    ),
    AptnerSensorDescription(
        key="visit_vehicle_usage_count",
        name="Visit Vehicle Reservation Count",
        icon="mdi:car-multiple",
        value_fn=lambda data: _visit_vehicle_usage_count(data.get("visit_vehicle_usage")),
        attributes_fn=lambda data: _visit_usage_attributes(data.get("visit_vehicle_usage")),
    ),
    AptnerSensorDescription(
        key="visit_vehicle_valid_count",
        name="Valid Visit Vehicle Reservation Count",
        icon="mdi:car-check",
        value_fn=lambda data: _visit_valid_count(data.get("visit_vehicle_usage")),
        attributes_fn=lambda data: _visit_usage_attributes(data.get("visit_vehicle_usage")),
    ),
    AptnerSensorDescription(
        key="visit_vehicle_next_date",
        name="Next Visit Vehicle Date",
        icon="mdi:calendar-car",
        value_fn=lambda data: _visit_next_date(data.get("visit_vehicle_usage")),
        attributes_fn=lambda data: _visit_usage_attributes(data.get("visit_vehicle_usage")),
    ),
    AptnerSensorDescription(
        key="visit_vehicle_next_car_no",
        name="Next Visit Vehicle Car Number",
        icon="mdi:car-info",
        value_fn=lambda data: _visit_next_car_no(data.get("visit_vehicle_usage")),
        attributes_fn=lambda data: _visit_usage_attributes(data.get("visit_vehicle_usage")),
    ),
    AptnerSensorDescription(
        key="visit_vehicle_next_purpose",
        name="Next Visit Vehicle Purpose",
        icon="mdi:clipboard-text-outline",
        value_fn=lambda data: _visit_next_purpose(data.get("visit_vehicle_usage")),
        attributes_fn=lambda data: _visit_usage_attributes(data.get("visit_vehicle_usage")),
    ),
    AptnerSensorDescription(
        key="realtor_count",
        name="Realtor Count",
        icon="mdi:home-city-outline",
        value_fn=lambda data: len(_list_or_empty(data.get("realtor"), "articles")) if not _error_text(data.get("realtor")) else None,
        attributes_fn=lambda data: _realtor_attributes(data.get("realtor")),
    ),
    AptnerSensorDescription(
        key="fire_inspection",
        name="Fire Inspection",
        icon="mdi:fire-alert",
        device_class=SensorDeviceClass.ENUM,
        options=["none", "open", "completed"],
        value_fn=lambda data: _fire_status_value(data.get("fire_inspection_status")),
        attributes_fn=lambda data: _fire_status_attributes(data.get("fire_inspection_status")),
    ),
    AptnerSensorDescription(
        key="fire_inspection_history_count",
        name="Fire Inspection History Count",
        icon="mdi:history",
        value_fn=lambda data: len(_fire_history_list(data.get("fire_inspection_history"))) if not _error_text(data.get("fire_inspection_history")) else None,
        attributes_fn=lambda data: _fire_history_attributes(data.get("fire_inspection_history")),
    ),
    AptnerSensorDescription(
        key="household_member_count",
        name="Household Member Count",
        icon="mdi:home-account",
        value_fn=lambda data: _household_member_count(data.get("household_members")),
        attributes_fn=lambda data: _household_attributes(data.get("household_members")),
    ),
    AptnerSensorDescription(
        key="household_verified_count",
        name="Verified Household Count",
        icon="mdi:account-check-outline",
        value_fn=lambda data: _verified_household_member_count(data.get("household_members")),
        attributes_fn=lambda data: _household_attributes(data.get("household_members")),
    ),
    AptnerSensorDescription(
        key="management_fee",
        name="Management Fee",
        icon="mdi:cash-multiple",
        device_class=SensorDeviceClass.MONETARY,
        native_unit_of_measurement="KRW",
        value_fn=lambda data: _management_fee_value(data.get("management_fee")),
        attributes_fn=lambda data: _management_fee_attributes(data.get("management_fee")),
    ),
    AptnerSensorDescription(
        key="management_fee_period",
        name="Management Fee Period",
        icon="mdi:calendar-range",
        value_fn=lambda data: _management_fee_period(data.get("management_fee")),
        attributes_fn=lambda data: _management_fee_attributes(data.get("management_fee")),
    ),
    AptnerSensorDescription(
        key="management_fee_average",
        name="Management Fee Average",
        icon="mdi:chart-line",
        device_class=SensorDeviceClass.MONETARY,
        native_unit_of_measurement="KRW",
        value_fn=lambda data: _management_fee_average_value(data.get("management_fee")),
        attributes_fn=lambda data: _management_fee_attributes(data.get("management_fee")),
    ),
    AptnerSensorDescription(
        key="management_fee_previous",
        name="Previous Management Fee",
        icon="mdi:cash-minus",
        device_class=SensorDeviceClass.MONETARY,
        native_unit_of_measurement="KRW",
        value_fn=lambda data: _management_fee_previous_value(data.get("management_fee")),
        attributes_fn=lambda data: _management_fee_attributes(data.get("management_fee")),
    ),
    AptnerSensorDescription(
        key="management_fee_previous_period",
        name="Previous Management Fee Period",
        icon="mdi:calendar-previous",
        value_fn=lambda data: _management_fee_previous_period(data.get("management_fee")),
        attributes_fn=lambda data: _management_fee_attributes(data.get("management_fee")),
    ),
    AptnerSensorDescription(
        key="management_fee_change",
        name="Management Fee Change",
        icon="mdi:swap-vertical",
        device_class=SensorDeviceClass.MONETARY,
        native_unit_of_measurement="KRW",
        value_fn=lambda data: _management_fee_change_value(data.get("management_fee")),
        attributes_fn=lambda data: _management_fee_attributes(data.get("management_fee")),
    ),
    AptnerSensorDescription(
        key="management_fee_history_count",
        name="Management Fee History Count",
        icon="mdi:calendar-multiple",
        value_fn=lambda data: _management_fee_history_count(data.get("management_fee")),
        attributes_fn=lambda data: _management_fee_attributes(data.get("management_fee")),
    ),
    AptnerSensorDescription(
        key="management_fee_area",
        name="Management Fee Area",
        icon="mdi:ruler-square",
        suggested_display_precision=2,
        value_fn=lambda data: _management_fee_area_float(data.get("management_fee")),
        attributes_fn=lambda data: _management_fee_attributes(data.get("management_fee")),
    ),
    AptnerSensorDescription(
        key="management_fee_current_late_fee",
        name="Management Fee Current Late Fee",
        icon="mdi:cash-fast",
        device_class=SensorDeviceClass.MONETARY,
        native_unit_of_measurement="KRW",
        value_fn=lambda data: _management_fee_money_field(data.get("management_fee"), "currentLateFee"),
        attributes_fn=lambda data: _management_fee_attributes(data.get("management_fee")),
    ),
    AptnerSensorDescription(
        key="management_fee_delinquent_fee",
        name="Management Fee Delinquent Fee",
        icon="mdi:cash-remove",
        device_class=SensorDeviceClass.MONETARY,
        native_unit_of_measurement="KRW",
        value_fn=lambda data: _management_fee_money_field(data.get("management_fee"), "delinquentFee"),
        attributes_fn=lambda data: _management_fee_attributes(data.get("management_fee")),
    ),
    AptnerSensorDescription(
        key="management_fee_delinquent_late_fee",
        name="Management Fee Delinquent Late Fee",
        icon="mdi:cash-lock",
        device_class=SensorDeviceClass.MONETARY,
        native_unit_of_measurement="KRW",
        value_fn=lambda data: _management_fee_money_field(data.get("management_fee"), "delinquentLateFee"),
        attributes_fn=lambda data: _management_fee_attributes(data.get("management_fee")),
    ),
    AptnerSensorDescription(
        key="management_fee_breakdown_count",
        name="Management Fee Breakdown Count",
        icon="mdi:format-list-bulleted",
        value_fn=lambda data: _management_fee_breakdown_count(data.get("management_fee")),
        attributes_fn=lambda data: _management_fee_attributes(data.get("management_fee")),
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    coordinator: AptnerDataUpdateCoordinator = hass.data[DOMAIN]["entries"][entry.entry_id]
    entities: list[SensorEntity] = [
        AptnerSensor(coordinator, entry, description) for description in SENSORS
    ]
    for fallback_index, item in enumerate(_management_fee_entity_items(coordinator.data)):
        entities.append(
            AptnerFeeBreakdownSensor(
                coordinator,
                entry,
                index=_management_fee_entity_index(item, fallback_index),
                label=_management_fee_entity_label(item, fallback_index),
            )
        )
    async_add_entities(entities)


class AptnerSensor(CoordinatorEntity[AptnerDataUpdateCoordinator], SensorEntity):
    """Representation of an Aptner sensor."""

    _attr_has_entity_name = True

    entity_description: AptnerSensorDescription

    def __init__(
        self,
        coordinator: AptnerDataUpdateCoordinator,
        entry: ConfigEntry,
        description: AptnerSensorDescription,
    ) -> None:
        super().__init__(coordinator)
        self.entity_description = description
        self._entry = entry
        self._attr_unique_id = f"{entry.entry_id}_{description.key}"
        self._attr_icon = description.icon

    @property
    def native_value(self) -> Any:
        return self.entity_description.value_fn(self.coordinator.data)

    @property
    def native_unit_of_measurement(self) -> str | None:
        localized_unit = _localized_sensor_unit(
            self.coordinator.hass,
            self.entity_description.key,
        )
        if localized_unit is not None:
            return localized_unit
        return self.entity_description.native_unit_of_measurement

    @property
    def suggested_display_precision(self) -> int | None:
        if self.entity_description.key in SENSOR_PRECISION_BY_KEY:
            return SENSOR_PRECISION_BY_KEY[self.entity_description.key]
        return self.entity_description.suggested_display_precision

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        return self.entity_description.attributes_fn(self.coordinator.data)

    @property
    def device_info(self) -> DeviceInfo:
        return _device_info_for_key(
            self.coordinator.hass,
            self._entry.entry_id,
            self.coordinator.data,
            self.entity_description.key,
        )


class AptnerFeeBreakdownSensor(CoordinatorEntity[AptnerDataUpdateCoordinator], SensorEntity):
    """Dynamic per-line management fee sensor."""

    _attr_has_entity_name = True
    _attr_device_class = SensorDeviceClass.MONETARY
    _attr_native_unit_of_measurement = "KRW"
    _attr_suggested_display_precision = 0
    _attr_icon = "mdi:receipt-text-outline"

    def __init__(
        self,
        coordinator: AptnerDataUpdateCoordinator,
        entry: ConfigEntry,
        *,
        index: int,
        label: str,
    ) -> None:
        super().__init__(coordinator)
        self._entry = entry
        self._index = index
        self._attr_name = label
        self._attr_unique_id = f"{entry.entry_id}_management_fee_breakdown_{index}"

    @property
    def native_value(self) -> int | None:
        item = _management_fee_breakdown_item(
            self.coordinator.data.get("management_fee"),
            self._index,
        )
        if item is None:
            return None
        value = item.get("value")
        return value if isinstance(value, int) else None

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        payload = self.coordinator.data.get("management_fee")
        item = _management_fee_breakdown_item(payload, self._index)
        attrs: dict[str, Any] = {
            "index": self._index,
            "period": _management_fee_period(payload),
            "area": _management_fee_text_field(payload, "area"),
            "area_square_meter": _management_fee_area_float(payload),
        }
        if item is None:
            return attrs

        attrs.update(item)
        value = item.get("value")
        average = item.get("average")
        if isinstance(value, int) and isinstance(average, int):
            attrs["delta"] = value - average
            attrs["is_above_average"] = value > average
            attrs["is_below_average"] = value < average
            attrs["value_ratio_to_average"] = (
                round(value / average, 3)
                if average != 0
                else None
            )
        else:
            attrs["is_above_average"] = None
            attrs["is_below_average"] = None
            attrs["value_ratio_to_average"] = None
        return attrs

    @property
    def device_info(self) -> DeviceInfo:
        return _device_info_for_key(
            self.coordinator.hass,
            self._entry.entry_id,
            self.coordinator.data,
            "management_fee_breakdown",
        )
