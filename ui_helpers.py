"""여러 페이지에서 같이 쓰는 화면 요소."""
import json

import streamlit.components.v1 as components

# 부모 페이지에서 실행할 코드. 컴포넌트 iframe은 페이지를 옮기면 없어지므로,
# 버튼 동작을 iframe이 아니라 부모 페이지 쪽에 심어 둠 (한 번만).
_SCROLL_TOP_PARENT_JS = r"""
(function () {
  if (document.getElementById("scroll-top-btn")) return;
  var btn = document.createElement("button");
  btn.id = "scroll-top-btn";
  btn.type = "button";
  btn.title = "맨 위로";
  btn.setAttribute("aria-label", "맨 위로 이동");
  btn.textContent = "↑";
  // 오른쪽 아래 Streamlit 배지와 겹치지 않게 조금 위에 둠
  btn.style.cssText = "position:fixed;right:24px;bottom:88px;z-index:999990;width:48px;height:48px;"
    + "border:none;border-radius:50%;background:linear-gradient(135deg,#4f46e5,#7c3aed);color:#fff;"
    + "font-size:22px;font-weight:700;line-height:1;cursor:pointer;box-shadow:0 4px 12px rgba(79,70,229,.35);"
    + "opacity:0;visibility:hidden;transition:opacity .2s,visibility .2s;";
  document.body.appendChild(btn);

  // Streamlit은 버전에 따라 stMain 또는 문서 전체가 스크롤됨
  function scrollers() {
    return [document.querySelector('[data-testid="stMain"]'), document.scrollingElement].filter(Boolean);
  }
  function update() {
    var y = Math.max.apply(null, scrollers().map(function (s) { return s.scrollTop; }));
    btn.style.opacity = y > 300 ? "1" : "0";
    btn.style.visibility = y > 300 ? "visible" : "hidden";
  }
  document.addEventListener("scroll", update, true);  // 어느 요소가 스크롤돼도 잡음
  btn.addEventListener("click", function () {
    scrollers().forEach(function (s) { s.scrollTo({ top: 0, behavior: "smooth" }); });
  });
  update();
})();
"""

_INJECT_HTML = """<script>
(function () {
  var doc = window.parent.document;
  if (doc.getElementById("scroll-top-script")) return;
  var s = doc.createElement("script");
  s.id = "scroll-top-script";
  s.textContent = %s;
  doc.head.appendChild(s);
})();
</script>""" % json.dumps(_SCROLL_TOP_PARENT_JS).replace("</", "<\\/")


def scroll_to_top_button():
    """스크롤을 내리면 오른쪽 아래에 '맨 위로' 버튼을 띄움."""
    components.html(_INJECT_HTML, height=0)
