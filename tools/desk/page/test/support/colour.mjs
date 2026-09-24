// How well one colour can be read on another, by the formula of the Web
// Content Accessibility Guidelines. It takes `#rrggbb` and `hsl(h s% l%)`.

function fromHsl(h, s, l) {
  const sat = s / 100;
  const light = l / 100;
  const a = sat * Math.min(light, 1 - light);
  const f = (n) => {
    const k = (n + h / 30) % 12;
    return light - a * Math.max(-1, Math.min(k - 3, 9 - k, 1));
  };
  return [f(0), f(8), f(4)];
}

export function rgbOf(colour) {
  const text = String(colour).trim();
  const hex = /^#([0-9a-f]{6})$/i.exec(text);
  if (hex) return [0, 2, 4].map((i) => parseInt(hex[1].slice(i, i + 2), 16) / 255);
  const short = /^#([0-9a-f]{3})$/i.exec(text);
  if (short) return [...short[1]].map((c) => parseInt(c + c, 16) / 255);
  const hsl = /^hsl\(\s*([\d.]+)(?:deg)?[\s,]+([\d.]+)%[\s,]+([\d.]+)%\s*\)$/i.exec(text);
  if (hsl) return fromHsl(Number(hsl[1]), Number(hsl[2]), Number(hsl[3]));
  throw new Error(`not a colour this test can read: ${colour}`);
}

function light(colour) {
  const [r, g, b] = rgbOf(colour).map((c) => (c <= 0.03928 ? c / 12.92 : ((c + 0.055) / 1.055) ** 2.4));
  return 0.2126 * r + 0.7152 * g + 0.0722 * b;
}

export function contrast(one, other) {
  const a = light(one);
  const b = light(other);
  return (Math.max(a, b) + 0.05) / (Math.min(a, b) + 0.05);
}
