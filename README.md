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
- `parking_vehicle_last_entry_at`
- `parking_vehicle_last_exit_at`
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

- `parking_vehicle_inside`: 현재 미출차 차량 존재 여부
- `parking_vehicle_last_event_entry`: 마지막 주차 이벤트가 입차인지 여부
- `parking_vehicle_last_event_exit`: 마지막 주차 이벤트가 출차인지 여부

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
- 주차 이력: `active_parking_count`, `active_car_numbers`, `latest_event`, `latest_event_summary`, `latest_entry_at`, `latest_exit_at`
- 주차 결제: `latest_amount`, `total_amount`
- 관리비: `summary`, `breakdown_items`, `top_breakdown_item`, `change_direction`, `has_outstanding_balance`
- 관리비 세부 항목 센서: `delta`, `is_above_average`, `is_below_average`, `value_ratio_to_average`

## 제공 서비스

- `aptner.refresh_data`: 즉시 새로고침
- `aptner.submit_vote`: 투표 제출
- `aptner.submit_survey`: 설문 제출
- `aptner.register_visit_vehicle`: 방문차량 등록
- `aptner.cancel_visit_vehicle`: 방문차량 예약 취소
