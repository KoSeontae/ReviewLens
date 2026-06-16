const SCRIPT_URL =
  "https://script.google.com/macros/s/AKfycbzhymcjzxvWHpm0teJwIT3pXTS5pMW5knGCtwAPNZp09i2VVyPZhESTTzj8QkDrbPcW/exec";

function getCookieValue(name: string): string | null {
  const m = document.cookie.match(new RegExp(`(?:^|; )${name}=([^;]*)`));
  return m ? decodeURIComponent(m[1]) : null;
}

function setCookieValue(name: string, value: string, days: number) {
  const expires = new Date(Date.now() + days * 864e5).toUTCString();
  document.cookie = `${name}=${encodeURIComponent(value)}; expires=${expires}; path=/`;
}

function getOrCreateUserId(): string {
  const KEY = "_rl_uid";
  let id = getCookieValue(KEY);
  if (!id) {
    id = Math.random().toString(36).slice(2, 8);
    setCookieValue(KEY, id, 180);
  }
  return id;
}

function getDevice(): string {
  return /Mobi|Android|iPhone|iPad/i.test(navigator.userAgent) ? "mobile" : "desktop";
}

function getUtm(): string {
  const p = new URLSearchParams(window.location.search);
  return ["utm_source", "utm_medium", "utm_campaign", "utm_content"]
    .filter((k) => p.has(k))
    .map((k) => `${k}=${p.get(k)}`)
    .join("&");
}

function localTimestamp(): string {
  const d = new Date();
  const local = new Date(d.getTime() - d.getTimezoneOffset() * 60000);
  return local.toISOString().replace("T", " ").replace("Z", "");
}

async function fetchIP(): Promise<string> {
  try {
    const res = await fetch("https://api.ipify.org?format=json");
    const json = await res.json();
    return json.ip ?? "";
  } catch {
    return "";
  }
}

async function send(table: string, data: Record<string, string>) {
  const url = `${SCRIPT_URL}?action=insert&table=${table}&data=${encodeURIComponent(JSON.stringify(data))}`;
  try {
    await fetch(url, { mode: "no-cors" });
  } catch {
    // fire-and-forget
  }
}

export async function logVisit() {
  const ip = await fetchIP();
  await send("visitors_final", {
    id: getOrCreateUserId(),
    landingUrl: window.location.href,
    ip,
    referer: document.referrer,
    time_stamp: localTimestamp(),
    utm: getUtm(),
    device: getDevice(),
    email: "",
    advice: "",
  });
}

export async function submitFeedback(email: string, advice: string, productUrl = "") {
  const ip = await fetchIP();
  await send("feedback_final", {
    id: getOrCreateUserId(),
    landingUrl: productUrl,
    ip,
    referer: "",
    time_stamp: localTimestamp(),
    utm: "",
    device: getDevice(),
    email,
    advice,
  });
}
