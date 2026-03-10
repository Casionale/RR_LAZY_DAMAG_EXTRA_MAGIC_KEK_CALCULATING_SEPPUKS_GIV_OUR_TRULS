const REQUIRED = ["PHPSESSID", "rr", "rr_add", "rr_f", "rr_id"];

async function getCookie(domain, name) {
  const url = `https://${domain}/`;
  const c = await browser.cookies.get({ url, name });
  return c ? c.value : null;
}

async function collectCookies() {
  const domains = ["rivalregions.com", "rivalka.ru"];
  for (const domain of domains) {
    const values = {};
    let okCount = 0;
    for (const key of REQUIRED) {
      const v = await getCookie(domain, key);
      if (v) {
        values[key] = v;
        okCount += 1;
      }
    }
    if (okCount >= 3) {
      return { domain, cookies: values };
    }
  }
  throw new Error("Не удалось получить cookies. Откройте игру в Firefox и попробуйте снова.");
}

async function sendCookies() {
  const backend = document.getElementById("backend").value.trim().replace(/\/$/, "");
  const client = document.getElementById("client").value.trim();
  const msg = document.getElementById("msg");
  msg.textContent = "Собираю cookies...";

  try {
    const payload = await collectCookies();
    payload.client = client;

    msg.textContent = "Отправляю на backend...";
    const res = await fetch(`${backend}/api/session/import-cookies`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      credentials: "include",
      body: JSON.stringify(payload)
    });
    const data = await res.json();
    if (!res.ok || !data.ok) {
      throw new Error(data.error || "Ошибка backend");
    }

    await browser.storage.local.set({ backend, client, lastDomain: payload.domain });
    msg.textContent = `Готово ✅\nДомен: ${payload.domain}`;
  } catch (e) {
    msg.textContent = `Ошибка: ${e.message}`;
  }
}

(async function init() {
  const saved = await browser.storage.local.get(["backend", "client"]);
  if (saved.backend) document.getElementById("backend").value = saved.backend;
  if (saved.client) document.getElementById("client").value = saved.client;
})();

document.getElementById("send").addEventListener("click", sendCookies);
