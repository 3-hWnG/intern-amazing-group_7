/* Quản lý Bộ nhớ dài hạn của Trợ lý (ChatGPT-style Memory System) & Onboarding */
window.Memory = (function () {
  const $ = (id) => document.getElementById(id);
  const PROVINCES = [
    "An Giang", "Bà Rịa - Vũng Tàu", "Bắc Giang", "Bắc Kạn", "Bạc Liêu", "Bắc Ninh",
    "Bến Tre", "Bình Định", "Bình Dương", "Bình Phước", "Bình Thuận", "Cà Mau",
    "Cần Thơ", "Cao Bằng", "Đà Nẵng", "Đắk Lắk", "Đắk Nông", "Điện Biên", "Đồng Nai",
    "Đồng Tháp", "Gia Lai", "Hà Giang", "Hà Nam", "Hà Nội", "Hà Tĩnh", "Hải Dương",
    "Hải Phòng", "Hậu Giang", "Hòa Bình", "Hưng Yên", "Khánh Hòa", "Kiên Giang",
    "Kon Tum", "Lai Châu", "Lâm Đồng", "Lạng Sơn", "Lào Cai", "Long An", "Nam Định",
    "Nghệ An", "Ninh Bình", "Ninh Thuận", "Phú Thọ", "Phú Yên", "Quảng Bình",
    "Quảng Nam", "Quảng Ngãi", "Quảng Ninh", "Quảng Trị", "Sóc Trăng", "Sơn La",
    "Tây Ninh", "Thái Bình", "Thái Nguyên", "Thanh Hóa", "Thừa Thiên Huế", "Tiền Giang",
    "TP. Hồ Chí Minh", "Trà Vinh", "Tuyên Quang", "Vĩnh Long", "Vĩnh Phúc", "Yên Bái"
  ];

  let currentData = { profile: {}, mcq_items: [], labels: {} };
  let addOptions = null;        // {axis: {question, values[]}} — lấy từ /api/mcq-memory/options

  async function loadAddOptions() {
    const sel = $("mem-add-axis");
    if (!sel) return;
    try {
      if (!addOptions) addOptions = (await API.get("/api/mcq-memory/options")).axes || {};
    } catch (_) { addOptions = {}; }
    const prev = sel.value;
    sel.innerHTML = "";
    Object.entries(addOptions).forEach(([axis, info]) => {
      const o = document.createElement("option");
      o.value = axis;
      o.textContent = info.question || axis;
      sel.appendChild(o);
    });
    if (prev && addOptions[prev]) sel.value = prev;
    fillAddValues();
  }

  function fillAddValues() {
    const dl = $("mem-add-values");
    const axis = $("mem-add-axis") ? $("mem-add-axis").value : "";
    if (!dl) return;
    dl.innerHTML = "";
    ((addOptions && addOptions[axis] && addOptions[axis].values) || []).forEach((v) => {
      const o = document.createElement("option");
      o.value = v;
      dl.appendChild(o);
    });
  }

  async function addMcq() {
    const axis = $("mem-add-axis").value;
    const input = $("mem-add-value");
    const value = input.value.trim();
    const status = $("mem-add-status");
    if (!axis || !value) { status.textContent = "Hãy chọn loại và nhập giá trị cần nhớ."; return; }
    status.textContent = "Đang lưu…";
    try {
      await API.post("/api/mcq-memory", { axis, value });   // máy chủ kiểm giá trị hợp lệ theo CSDL
      input.value = "";
      status.textContent = "✓ Đã thêm.";
      await loadData();
      renderMcqList();
      setTimeout(() => { status.textContent = ""; }, 2500);
    } catch (err) {
      status.textContent = "Lỗi: " + err.message;
    }
  }

  function renderSidebarBadge() {
    const host = $("memory");
    if (!host) return;
    const p = currentData.profile || {};
    const mcqCount = (currentData.mcq_items || []).length;
    const bits = [p.province, p.ward].filter(Boolean);
    host.innerHTML = "";

    const btn = document.createElement("button");
    btn.type = "button";
    btn.className = "memory-pill-btn";
    btn.title = "Bấm để xem và quản lý bộ nhớ trợ lý";
    
    let summaryText = "🧠 Trí nhớ AI";
    if (bits.length) {
      summaryText += ": " + bits.join(" · ");
    }
    if (mcqCount > 0) {
      summaryText += ` (${mcqCount} mục)`;
    }
    btn.textContent = summaryText;
    btn.onclick = () => openModal();
    host.appendChild(btn);
    host.hidden = false;
  }

  async function loadData() {
    try {
      currentData = await API.get("/api/memory");
    } catch (_) {
      try {
        const profRes = await API.get("/api/profile");
        const mcqRes = await API.get("/api/mcq-memory");
        currentData = {
          profile: profRes.profile || {},
          mcq_items: mcqRes.items || [],
          labels: mcqRes.labels || {}
        };
      } catch (e) {
        currentData = { profile: {}, mcq_items: [], labels: {} };
      }
    }
    renderSidebarBadge();
    return currentData;
  }

  function openModal() {
    const modal = $("memory-modal");
    const backdrop = $("mem-modal-backdrop");
    if (!modal) return;
    modal.removeAttribute("hidden");
    modal.classList.add("open");
    modal.setAttribute("aria-hidden", "false");
    if (backdrop) backdrop.classList.add("open");
    renderModalContent();
    loadAddOptions();
  }

  function closeModal() {
    const modal = $("memory-modal");
    const backdrop = $("mem-modal-backdrop");
    if (!modal) return;
    modal.setAttribute("hidden", "");
    modal.classList.remove("open");
    modal.setAttribute("aria-hidden", "true");
    if (backdrop) backdrop.classList.remove("open");
  }

  function renderModalContent() {
    const p = currentData.profile || {};
    const provSelect = $("mem-prov-select");
    if (provSelect) {
      provSelect.innerHTML = '<option value="">-- Chưa chọn Tỉnh/Thành phố --</option>';
      PROVINCES.forEach((prov) => {
        const opt = document.createElement("option");
        opt.value = prov;
        opt.textContent = prov;
        if (p.province === prov) opt.selected = true;
        provSelect.appendChild(opt);
      });
    }

    if ($("mem-ward-input")) $("mem-ward-input").value = p.ward || "";
    if ($("mem-notes-input")) $("mem-notes-input").value = p.notes || "";

    renderMcqList();
  }

  function renderMcqList() {
    const listEl = $("mem-mcq-list");
    if (!listEl) return;
    listEl.innerHTML = "";
    const items = currentData.mcq_items || [];
    if (!items.length) {
      listEl.innerHTML = '<p class="muted small text-center" style="padding:20px 0;">Chưa có lựa chọn nào được ghi nhớ. Khi làm thủ tục, tick "Nhớ lựa chọn này" để lưu vào đây.</p>';
      return;
    }

    items.forEach((item) => {
      const row = document.createElement("div");
      row.className = "mem-mcq-item";

      const info = document.createElement("div");
      info.className = "mem-mcq-info";
      const qText = currentData.labels[item.axis] || ("Trục: " + item.axis);
      const h = (v) => String(v == null ? "" : v).replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/"/g, "&quot;");
      info.innerHTML = `<strong>${h(qText)}</strong><div class="mem-mcq-val">Đang nhớ: <span class="val-text">${h(item.value)}</span></div><small class="muted">Đã tự chọn hộ: ${Number(item.n_used) || 0} lần</small>`;

      const actions = document.createElement("div");
      actions.className = "mem-mcq-actions";

      const editBtn = document.createElement("button");
      editBtn.type = "button";
      editBtn.className = "link small";
      editBtn.textContent = "Sửa";
      editBtn.onclick = async () => {
        const valSpan = info.querySelector(".val-text");
        const curVal = valSpan.textContent;
        const input = document.createElement("input");
        input.type = "text";
        input.className = "mem-inline-edit";
        input.value = curVal;
        // Máy chủ chỉ nhận giá trị có trong CSDL -> gợi ý đúng danh sách đó khi sửa.
        try {
          if (!addOptions) addOptions = (await API.get("/api/mcq-memory/options")).axes || {};
        } catch (_) { addOptions = addOptions || {}; }
        const dlId = "mem-edit-values-" + item.axis;
        let dl = document.getElementById(dlId);
        if (!dl) {
          dl = document.createElement("datalist");
          dl.id = dlId;
          document.body.appendChild(dl);
        }
        dl.innerHTML = "";
        ((addOptions[item.axis] && addOptions[item.axis].values) || []).forEach((v) => {
          const o = document.createElement("option");
          o.value = v;
          dl.appendChild(o);
        });
        input.setAttribute("list", dlId);
        valSpan.replaceWith(input);
        input.focus();

        editBtn.textContent = "Lưu";
        editBtn.onclick = async () => {
          const newVal = input.value.trim();
          if (!newVal) return;
          try {
            await API.put(`/api/mcq-memory/${encodeURIComponent(item.axis)}`, { value: newVal });
            item.value = newVal;
            renderSidebarBadge();
            renderMcqList();
          } catch (err) {
            alert("Lỗi cập nhật: " + err.message);
          }
        };
      };

      const delBtn = document.createElement("button");
      delBtn.type = "button";
      delBtn.className = "link small danger";
      delBtn.textContent = "Xóa";
      delBtn.onclick = async () => {
        if (!confirm(`Xóa trí nhớ về "${item.value}"?`)) return;
        try {
          await API.del(`/api/mcq-memory?axis=${encodeURIComponent(item.axis)}`);
          currentData.mcq_items = currentData.mcq_items.filter((x) => x.axis !== item.axis);
          renderSidebarBadge();
          renderMcqList();
        } catch (err) {
          alert("Lỗi xóa: " + err.message);
        }
      };

      actions.append(editBtn, delBtn);
      row.append(info, actions);
      listEl.appendChild(row);
    });
  }

  async function saveProfile() {
    const province = $("mem-prov-select") ? $("mem-prov-select").value.trim() : "";
    const ward = $("mem-ward-input") ? $("mem-ward-input").value.trim() : "";
    const notes = $("mem-notes-input") ? $("mem-notes-input").value.trim() : "";

    const statusEl = $("mem-profile-status");
    if (statusEl) statusEl.textContent = "Đang lưu...";
    try {
      const res = await API.post("/api/profile", { province, ward, notes });
      currentData.profile = res.profile || { province, ward, notes };
      renderSidebarBadge();
      if (statusEl) {
        statusEl.textContent = "✓ Đã lưu thành công!";
        setTimeout(() => { statusEl.textContent = ""; }, 2500);
      }
    } catch (err) {
      if (statusEl) statusEl.textContent = "Lỗi: " + err.message;
    }
  }

  async function clearProfile() {
    if (!confirm("Bạn có chắc muốn xóa toàn bộ thông tin địa bàn và ghi chú cá nhân?")) return;
    try {
      await API.del("/api/profile");
      currentData.profile = {};
      renderSidebarBadge();
      renderModalContent();
    } catch (err) {
      alert("Lỗi: " + err.message);
    }
  }

  async function clearAllMcq() {
    if (!confirm("Bạn có chắc muốn xóa tất cả lựa chọn MCQ đã ghi nhớ?")) return;
    try {
      await API.del("/api/mcq-memory");
      currentData.mcq_items = [];
      renderSidebarBadge();
      renderMcqList();
    } catch (err) {
      alert("Lỗi: " + err.message);
    }
  }

  /* Onboarding Banner / Dialog */
  function checkOnboarding() {
    const p = currentData.profile || {};
    if (p.province) return; // Đã có địa bàn -> không cần onboarding
    if (sessionStorage.getItem("onboarding_dismissed")) return;

    const onb = $("onboarding-modal");
    if (!onb) return;

    const select = $("onb-prov-select");
    if (select) {
      select.innerHTML = '<option value="">-- Chọn Tỉnh / Thành phố --</option>';
      PROVINCES.forEach((prov) => {
        const opt = document.createElement("option");
        opt.value = prov;
        opt.textContent = prov;
        select.appendChild(opt);
      });
    }

    onb.removeAttribute("hidden");
    onb.classList.add("open");
    onb.setAttribute("aria-hidden", "false");
    const backdrop = $("mem-modal-backdrop");
    if (backdrop) backdrop.classList.add("open");
  }

  function closeOnboarding() {
    const onb = $("onboarding-modal");
    if (onb) {
      onb.setAttribute("hidden", "");
      onb.classList.remove("open");
      onb.setAttribute("aria-hidden", "true");
    }
    const backdrop = $("mem-modal-backdrop");
    if (backdrop) backdrop.classList.remove("open");
    sessionStorage.setItem("onboarding_dismissed", "true");
  }

  async function saveOnboarding() {
    const select = $("onb-prov-select");
    const prov = select ? select.value.trim() : "";
    if (!prov) {
      alert("Vui lòng chọn Tỉnh/Thành phố của bạn.");
      return;
    }
    try {
      const res = await API.post("/api/profile", { province: prov });
      currentData.profile = res.profile || { province: prov };
      renderSidebarBadge();
      closeOnboarding();
    } catch (err) {
      alert("Lỗi lưu thông tin: " + err.message);
    }
  }

  function init() {
    // Tab switching in Memory Modal
    const tabs = document.querySelectorAll(".mem-tab-btn");
    tabs.forEach((tab) => {
      tab.onclick = () => {
        tabs.forEach((t) => t.classList.remove("active"));
        tab.classList.add("active");
        const target = tab.dataset.tab;
        document.querySelectorAll(".mem-tab-panel").forEach((panel) => {
          panel.hidden = panel.id !== target;
        });
      };
    });

    if ($("mem-save-profile")) $("mem-save-profile").onclick = saveProfile;
    if ($("mem-clear-profile")) $("mem-clear-profile").onclick = clearProfile;
    if ($("mem-clear-mcq")) $("mem-clear-mcq").onclick = clearAllMcq;
    if ($("mem-add-btn")) $("mem-add-btn").onclick = addMcq;
    if ($("mem-add-axis")) $("mem-add-axis").onchange = fillAddValues;
    if ($("mem-add-value")) $("mem-add-value").onkeydown = (e) => { if (e.key === "Enter") { e.preventDefault(); addMcq(); } };
    if ($("mem-modal-close")) $("mem-modal-close").onclick = closeModal;
    if ($("mem-modal-backdrop")) $("mem-modal-backdrop").onclick = closeModal;

    if ($("onb-save-btn")) $("onb-save-btn").onclick = saveOnboarding;
    if ($("onb-skip-btn")) $("onb-skip-btn").onclick = closeOnboarding;
  }

  return {
    init,
    loadData,
    openModal,
    closeModal,
    checkOnboarding,
    renderSidebarBadge,
    get current() { return currentData; }
  };
})();
