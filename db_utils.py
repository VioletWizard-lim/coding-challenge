"""Supabase 조회 헬퍼."""


def fetch_all(make_query, page_size: int = 1000) -> list:
    """조건에 맞는 행을 모두 가져옴.

    Supabase API는 한 번에 최대 1000행(프로젝트 설정 'Max rows')만 돌려줘서,
    그냥 execute()하면 1000건 넘는 데이터가 조용히 잘림. 페이지를 나눠 끝까지 받음.

    make_query: 호출할 때마다 새 조회를 만들어 돌려주는 함수.
        같은 조회에 range()를 여러 번 붙이면 조건이 겹쳐 쌓이므로 매번 새로 만들어야 함.
        페이지가 어긋나지 않도록 정렬(마지막에 id 포함)을 넣어 둘 것.
    """
    rows, start = [], 0
    while True:
        page = make_query().range(start, start + page_size - 1).execute().data or []
        if not page:
            return rows
        rows.extend(page)
        start += len(page)  # 서버 최대 행 수가 page_size보다 작아도 빠짐없이 이어서 받음
