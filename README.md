# Aptner Home Assistant Custom Integration

[아파트너 App Store](https://apps.apple.com/kr/app/%EC%95%84%ED%8C%8C%ED%8A%B8%EB%84%88-no-1-%EC%95%84%ED%8C%8C%ED%8A%B8%EC%95%B1/id1243505765)

## 설치

`custom_components/aptner` 폴더를 Home Assistant의 `config/custom_components/aptner` 아래에 복사한 뒤, Home Assistant를 재시작하고 통합 추가 화면에서 아파트너 계정으로 로그인하면 됩니다.

## 화면 예시

메인

![Aptner Main](images/P.MAIN.png)

홈

![Aptner Home](images/P.HOME.png)

커뮤니티

![Aptner Community](images/P.COMM.png)

관리비

![Aptner Billing](images/P.BILL.png)

주차

![Aptner Parking](images/P.PARK.png)

## 생성 엔티티

아래 엔티티 키는 고정이며, 실제 `entity_id`는 Home Assistant 엔티티 레지스트리 규칙에 따라 생성됩니다.

### 1. 기본 정보

- `apartment`: 아파트 이름
- `apartment_phone`: 대표 전화번호
- `usage_services`: 활성화된 사용 서비스 수

### 2. 공지 / 커뮤니티 / 민원

- `notice_count`, `latest_notice_title`, `latest_notice_date`
- `community_count`, `latest_community_title`
- `complaint_count`, `latest_complaint_title`, `latest_complaint_status`
- `defect_count`
- `region_count`, `latest_region_title`
- `aptner_notice_count`, `aptner_notice_latest_title`

### 3. 일정 / 투표 / 설문

- `schedule_count`, `schedule_next_day`
- `vote_current_count`, `vote_closed_count`
- `survey_ing_count`, `survey_done_count`

### 4. 연락처 / 방송

- `contacts_count`, `primary_contact`
- `broadcast_count`, `broadcast_latest`

### 5. 주차 / 방문차량

- `guest_parking_count`
- `guest_parking_history_count`
- `guest_parking_household_limit`
- `guest_parking_remaining_free`
- `parking_discount_history_count`
- `parking_vehicle_last_entry_at`: 방문차량 기준 최근 입차 시각
- `parking_vehicle_last_exit_at`: 방문차량 기준 최근 출차 시각
- `parking_vehicle_last_entry_at_all`: 우리집 차량 포함 최근 입차 시각
- `parking_vehicle_last_exit_at_all`: 우리집 차량 포함 최근 출차 시각
- `visit_vehicle_usage_count`
- `visit_vehicle_valid_count`
- `visit_vehicle_next_date`
- `visit_vehicle_next_car_no`
- `visit_vehicle_next_purpose`

### 6. 부동산 / 안전 / 세대

- `realtor_count`
- `fire_inspection`
- `fire_inspection_history_count`
- `household_member_count`
- `household_verified_count`

### 7. 관리비

- `management_fee`
- `management_fee_period`
- `management_fee_average`
- `management_fee_previous`
- `management_fee_previous_period`
- `management_fee_change`
- `management_fee_history_count`
- `management_fee_area`
- `management_fee_current_late_fee`
- `management_fee_delinquent_fee`
- `management_fee_delinquent_late_fee`
- `management_fee_breakdown_*`: 관리비 세부 항목별 자동 생성 센서

## 생성 바이너리 센서

### 1. 주차 입출차

- `parking_vehicle_inside`: 방문차량 기준 현재 미출차 차량 존재 여부
- `parking_vehicle_last_event_entry`: 방문차량 기준 마지막 주차 이벤트가 입차인지 여부
- `parking_vehicle_last_event_exit`: 방문차량 기준 마지막 주차 이벤트가 출차인지 여부
- `parking_vehicle_inside_all`: 우리집 차량 포함 기준 현재 미출차 차량 존재 여부
- `parking_vehicle_last_event_entry_all`: 우리집 차량 포함 기준 마지막 주차 이벤트가 입차인지 여부
- `parking_vehicle_last_event_exit_all`: 우리집 차량 포함 기준 마지막 주차 이벤트가 출차인지 여부

### 2. 방문차량

- `visit_vehicle_alert`: 유효한 방문차량 예약 존재 여부
- `visit_vehicle_today`: 오늘 방문차량 예약 존재 여부

## 엔티티별 주요 속성

대부분의 센서에는 원본 응답 외에 바로 자동화에 쓸 수 있는 요약 속성이 같이 붙습니다.

- 게시판/공지: `article_count`, `latest_title`, `latest_date`, `recent_titles`
- 일정: `next_event`, `next_event_title`, `today_event_count`, `today_events`
- 투표/설문: `latest_title`, `vote_ids`, `survey_ids`
- 연락처/방송: `primary_contact_data`, `contact_numbers`, `recent_titles`
- 방문차량: `valid_count`, `expired_count`, `next_reservation`, `next_days_until`, `today_count`, `today_reservations`
- 주차 이력: `scope`, `total_history_item_count`, `resident_history_item_count`, `visitor_history_item_count`, `active_parking_count`, `active_car_numbers`, `latest_event`, `latest_event_summary`, `latest_entry_at`, `latest_exit_at`
- 주차 결제: `latest_amount`, `total_amount`
- 관리비: 엔티티별로 `summary`, `breakdown_items`, `top_breakdown_item`, `previous_breakdown_items`, `change_direction` 등이 제공됨
- 관리비 세부 항목 센서: `delta`, `is_above_average`, `is_below_average`, `value_ratio_to_average`

### 관리비 속성 상세

`management_fee` 계열 센서는 엔티티 성격에 따라 속성이 다르게 붙습니다.

공통 속성(대부분 `management_fee*` 센서에 제공):

- `summary`: 관리비 요약 객체
- `period`: 당월 기준월 (`YYYY-MM`)
- `previous_period`: 전월 기준월 (`YYYY-MM`)
- `period_count`: 조회 가능한 관리비 기간 수
- `history`: 기간별 요약 목록 (`period`, `value`, `id`)
- `current_fee`, `current_fee_average`, `current_fee_delta`: 당월 관리비/평균/차이
- `previous_fee`, `period_change`: 전월 관리비/전월 대비 증감
- `current_late_fee`, `delinquent_fee`, `delinquent_late_fee`, `total_outstanding`: 연체/미납 관련 금액
- `change_direction`: 증감 방향 (`increase`, `decrease`, `same`)
- `has_outstanding_balance`: 미납/연체 잔액 존재 여부

현재 기준 엔티티 (`management_fee`, `management_fee_period`, `management_fee_average`, `management_fee_area`, `management_fee_current_late_fee`, `management_fee_delinquent_fee`, `management_fee_delinquent_late_fee`, `management_fee_breakdown_count`):

- `period_scope`: `current`
- `detail`: 당월 상세 원본 (`latest_detail`와 동일 의미)
- `breakdown`, `breakdown_items`, `breakdown_count`: 당월 세부 항목 맵/목록/개수
- `breakdown_value_total`, `breakdown_average_total`: 당월 세부 항목 합계/평균 합계
- `top_breakdown_item`, `top_breakdown_label`, `top_breakdown_value`: 당월 최대 항목 정보

전월 기준 엔티티 (`management_fee_previous`, `management_fee_previous_period`):

- `period_scope`: `previous`
- `detail`: 전월 상세 원본
- `breakdown`, `breakdown_items`, `breakdown_count`: 전월 세부 항목 맵/목록/개수
- `breakdown_value_total`, `breakdown_average_total`: 전월 세부 항목 합계/평균 합계
- `top_breakdown_item`, `top_breakdown_label`, `top_breakdown_value`: 전월 최대 항목 정보

비교 엔티티 (`management_fee_change`):

- 현재 기준 속성(`detail`, `breakdown*`, `top_breakdown*`) + 전월 기준 호환 키(`previous_detail`, `previous_breakdown*`, `previous_top_breakdown*`)
- `comparison_scope`: `current_vs_previous`

요약 전용 엔티티 (`management_fee_history_count`)는 공통 속성 위주로 제공됩니다.

`management_fee_breakdown_*` 동적 센서는 각 세부 항목(예: 일반관리비, 청소비)을 개별 엔티티로 만들며 다음 속성을 가집니다.

- `index`, `label`: 세부 항목 인덱스/이름
- `period`, `previous_period`, `area`, `area_square_meter`: 당월/전월 기준월 및 면적 정보
- `value`, `average`: 항목 금액/평균 금액
- `delta`: 항목 금액 - 평균 금액
- `is_above_average`, `is_below_average`: 평균 대비 상태
- `value_ratio_to_average`: 평균 대비 비율
- `previous_item`, `previous_value`, `previous_average`, `previous_delta_to_average`: 전월 동일 항목 정보
- `change_from_previous`, `change_rate_from_previous`: 전월 대비 증감 금액/증감률
- `has_previous_value`, `is_increase_from_previous`, `is_decrease_from_previous`: 전월 비교 가능 여부/증감 방향

### 주차/방문차량 속성 상세

`guest_parking_*` 센서(`guest_parking_count`, `guest_parking_household_limit`, `guest_parking_remaining_free`)는 공통으로 아래 예약 속성을 가집니다.

- `reservation_count`: 방문주차 예약 수
- `latest_reservation`, `next_reservation`: 최신/다음 예약 객체
- `reservation_dates`: 예약 일자 목록
- `reserved_car_numbers`: 예약 차량번호 목록
- `visit_config`: 방문주차 설정 원본
- `household_limit`, `car_limit`: 세대/차량 기준 제한값
- `exit_camera_exists`: 출차 카메라 존재 여부

`parking_vehicle_*` 센서(`parking_vehicle_last_entry_at*`, `parking_vehicle_last_exit_at*`)와 주차 바이너리 센서는 공통으로 아래 이력 속성을 가집니다.

- `scope`: 조회 범위 (`visitor_only`, `all_vehicles`)
- `include_resident`, `resident_only`: 우리집 차량 포함 여부
- `total_history_item_count`, `resident_history_item_count`, `visitor_history_item_count`: 이력 집계
- `history_count`, `history_item_count`, `history_periods`: 이력 개수/기간 정보
- `active_parking_count`, `active_vehicles`, `active_car_numbers`, `active_unique_count`: 현재 미출차 차량 정보
- `latest_event`, `latest_event_type`, `latest_event_at`, `latest_event_item`, `latest_event_summary`: 최신 입출차 이벤트 정보
- `latest_entry`, `latest_entry_at`, `latest_entry_car_no`: 최신 입차 정보
- `latest_exit`, `latest_exit_at`, `latest_exit_car_no`: 최신 출차 정보
- `has_active_vehicle`, `latest_active_vehicle`: 현재 주차 여부/최근 미출차 차량
- `remaining_free`: 남은 무료 방문주차 횟수

주차 바이너리 센서(`parking_vehicle_inside*`, `parking_vehicle_last_event_entry*`, `parking_vehicle_last_event_exit*`)에는 아래 속성이 추가됩니다.

- `current_parked_vehicles`, `current_parked_count`, `current_parked_unique_count`: 현재 주차중 차량 요약
- `latest_event_car_no`: 최신 이벤트 차량번호

`visit_vehicle_*` 센서(`visit_vehicle_usage_count`, `visit_vehicle_valid_count`, `visit_vehicle_next_*`)와 방문차량 바이너리 센서는 공통으로 아래 예약 속성을 가집니다.

- `reservation_count`, `valid_count`, `expired_count`: 전체/유효/만료 예약 수
- `valid_reservations`: 유효 예약 목록
- `next_reservation`, `next_days_until`: 다음 예약 정보/남은 일수
- `today_reservation`, `today_reservations`, `today_count`: 오늘 예약 정보
- `has_today_reservation`: 오늘 예약 존재 여부
- `upcoming_dates`, `upcoming_car_numbers`: 예정 일자/차량번호 목록

`visit_vehicle_alert` 바이너리 센서에는 `alert_date`(평가 기준일, `YYYY-MM-DD`)가 추가됩니다.

## 제공 서비스

- `aptner.refresh_data`: 즉시 새로고침
- `aptner.submit_vote`: 투표 제출
- `aptner.submit_survey`: 설문 제출
- `aptner.register_visit_vehicle`: 방문차량 등록
- `aptner.cancel_visit_vehicle`: 방문차량 예약 취소
