-- 코드 작성 과정 기록 기능용 컬럼 추가 (Supabase SQL Editor에서 한 번 실행)
alter table submissions add column if not exists init_code text;
alter table submissions add column if not exists edit_log jsonb;
