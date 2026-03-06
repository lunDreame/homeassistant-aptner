# Aptner Home Assistant Custom Integration

[아파트너 App Store](https://apps.apple.com/kr/app/%EC%95%84%ED%8C%8C%ED%8A%B8%EB%84%88-no-1-%EC%95%84%ED%8C%8C%ED%8A%B8%EC%95%B1/id1243505765)

## 설치

`custom_components/aptner` 폴더를 Home Assistant의 `config/custom_components/aptner` 아래에 복사한 뒤, Home Assistant를 재시작하고 통합 추가 화면에서 아파트너 계정으로 로그인하면 됩니다.

## 화면 예시

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
- `management_fee_breakdown_count`
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

## 제공 서비스

- `aptner.refresh_data`: 즉시 새로고침
- `aptner.submit_vote`: 투표 제출
- `aptner.submit_survey`: 설문 제출
- `aptner.register_visit_vehicle`: 방문차량 등록
- `aptner.cancel_visit_vehicle`: 방문차량 예약 취소
