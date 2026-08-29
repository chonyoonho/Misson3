// ==========================================================================
// 3.8 아카이브 - 공통 스크립트
// 모든 페이지에서 <script src="js/main.js" defer></script>로 불러옵니다.
// 페이지별 기능(갤러리 라이트박스, 챗봇 등)은 해당 요소가 있을 때만 동작하도록
// 존재 여부를 먼저 확인합니다. 그래야 이 파일 하나로 4개 페이지를 공유할 수 있습니다.
// ==========================================================================

document.addEventListener("DOMContentLoaded", () => {
  initNavToggle();
  initGalleryLightbox();
  initVideoFileProtocolNotice();
  initChat();
});

/* --------------------------------------------------------------------------
 * 1. 모바일 내비게이션 토글 (모든 페이지 공통 헤더)
 * ------------------------------------------------------------------------ */
function initNavToggle() {
  const toggleBtn = document.querySelector(".nav-toggle");
  const nav = document.querySelector(".main-nav");
  if (!toggleBtn || !nav) return;

  toggleBtn.addEventListener("click", () => {
    const isOpen = nav.classList.toggle("is-open");
    toggleBtn.setAttribute("aria-expanded", String(isOpen));
  });

  // 메뉴 항목을 클릭해서 다른 페이지로 이동할 때 메뉴가 열린 채로 남지 않도록 정리
  nav.querySelectorAll("a").forEach((link) => {
    link.addEventListener("click", () => {
      nav.classList.remove("is-open");
      toggleBtn.setAttribute("aria-expanded", "false");
    });
  });
}

/* --------------------------------------------------------------------------
 * 2. 갤러리 라이트박스 (gallery.html 전용, 해당 요소가 없으면 그냥 종료)
 * ------------------------------------------------------------------------ */
function initGalleryLightbox() {
  const grid = document.querySelector("[data-gallery]");
  const lightbox = document.querySelector("[data-lightbox]");
  if (!grid || !lightbox) return;

  const lightboxImg = lightbox.querySelector("[data-lightbox-img]");
  const lightboxCaption = lightbox.querySelector("[data-lightbox-caption]");
  const closeBtn = lightbox.querySelector("[data-lightbox-close]");

  grid.querySelectorAll("[data-gallery-item]").forEach((item) => {
    item.addEventListener("click", () => {
      const img = item.querySelector("img");
      if (!img) return;
      lightboxImg.src = img.src;
      lightboxImg.alt = img.alt;
      lightboxCaption.textContent = img.alt || "";
      lightbox.classList.add("is-open");
      document.body.style.overflow = "hidden"; // 라이트박스가 열려있는 동안 배경 스크롤 방지
    });
  });

  function closeLightbox() {
    lightbox.classList.remove("is-open");
    document.body.style.overflow = "";
  }

  closeBtn?.addEventListener("click", closeLightbox);

  // 어두운 배경(오버레이) 클릭 시에도 닫히도록 처리
  lightbox.addEventListener("click", (e) => {
    if (e.target === lightbox) closeLightbox();
  });

  document.addEventListener("keydown", (e) => {
    if (e.key === "Escape") closeLightbox();
  });
}

/* --------------------------------------------------------------------------
 * 3. 유튜브 임베드 file:// 안내 (gallery.html 전용)
 * file://로 직접 열면 유튜브 iframe이 origin 검증 실패로 재생되지 않으므로,
 * 그 경우에만 안내 오버레이를 보여줌. 서버(http/https)로 열었을 때는 그대로 재생.
 * ------------------------------------------------------------------------ */
function initVideoFileProtocolNotice() {
  if (window.location.protocol !== "file:") return;

  document.querySelectorAll("[data-video-notice]").forEach((notice) => {
    notice.hidden = false;
  });
}

/* --------------------------------------------------------------------------
 * 4. AI 챗봇 (chat.html 전용, 해당 요소가 없으면 그냥 종료)
 * ------------------------------------------------------------------------ */
function initChat() {
  const form = document.querySelector("[data-chat-form]");
  if (!form) return;

  const input = form.querySelector("[data-chat-input]");
  const sendBtn = form.querySelector("[data-chat-send]");
  const log = document.querySelector("[data-chat-log]");

  form.addEventListener("submit", async (e) => {
    e.preventDefault();

    const question = input.value.trim();

    // 실패 처리 1: 빈 질문 입력 시 안내만 하고 서버에 요청을 보내지 않음
    if (!question) {
      appendMessage("bot", "질문을 입력해주세요.", true);
      return;
    }

    appendMessage("user", question);
    input.value = "";
    setFormBusy(true);

    // 실패 처리 3: 응답을 기다리는 동안 "답변 생성 중..." 표시
    const loadingEl = appendMessage("bot", "답변 생성 중...", false, true);

    try {
      const res = await fetch("/api/ask", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ question }),
      });

      // 실패 처리 2: API가 4xx/5xx를 반환한 경우
      if (!res.ok) {
        throw new Error(`HTTP ${res.status}`);
      }

      const data = await res.json();
      loadingEl.remove();

      if (data.answer) {
        appendMessage("bot", data.answer);
      } else {
        appendMessage("bot", "오류가 발생했습니다. 잠시 후 다시 시도해주세요.", true);
      }
    } catch (err) {
      loadingEl.remove();
      appendMessage("bot", "오류가 발생했습니다. 잠시 후 다시 시도해주세요.", true);
    } finally {
      setFormBusy(false);
    }
  });

  function setFormBusy(isBusy) {
    input.disabled = isBusy;
    sendBtn.disabled = isBusy;
  }

  function appendMessage(role, text, isNotice = false, isLoading = false) {
    const bubble = document.createElement("div");
    bubble.className = `chat-bubble chat-bubble--${role}${isNotice ? " chat-bubble--notice" : ""}${
      isLoading ? " chat-bubble--loading" : ""
    }`;
    bubble.textContent = text;
    log.appendChild(bubble);
    log.scrollTop = log.scrollHeight;
    return bubble;
  }
}
