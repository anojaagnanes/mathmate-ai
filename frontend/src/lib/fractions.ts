/** Mistake-driven fraction bars: model the student's own addends, discover the common denominator. */

const VULGAR: Record<string, string> = {'¼': '1/4', '½': '1/2', '¾': '3/4', '⅐': '1/7', '⅑': '1/9', '⅒': '1/10', '⅓': '1/3', '⅔': '2/3', '⅕': '1/5', '⅖': '2/5', '⅗': '3/5', '⅘': '4/5', '⅙': '1/6', '⅚': '5/6', '⅛': '1/8', '⅜': '3/8', '⅝': '5/8', '⅞': '7/8'};

export function vulgarToAscii(text: string): string {
  return text.replace(/[¼½¾⅐⅑⅒⅓⅔⅕⅖⅗⅘⅙⅚⅛⅜⅝⅞]/g, c => VULGAR[c] || c);
}

export type Addend = [number, number];

/** First two a/b fractions in the text (unicode or ascii), else null. */
export function parseAddends(text: string): [Addend, Addend] | null {
  const found = [...vulgarToAscii(text).matchAll(/(\d+)\s*\/\s*(\d+)/g)]
    .map(m => [Number(m[1]), Number(m[2])] as Addend)
    .filter(([n, d]) => n >= 0 && d >= 2 && d <= 24 && n <= 2 * d);
  return found.length >= 2 ? [found[0], found[1]] : null;
}

export function gcd(a: number, b: number): number {
  return b === 0 ? Math.abs(a) : gcd(b, a % b);
}

export function lcm(a: number, b: number): number {
  return Math.abs(a * b) / gcd(a, b);
}

export type LabModel = {lcm: number; needA: number; needB: number; sumN: number; sumD: number};

export function labModel(a: Addend, b: Addend): LabModel {
  const common = lcm(a[1], b[1]);
  const needA = a[0] * (common / a[1]);
  const needB = b[0] * (common / b[1]);
  const total = needA + needB;
  const divisor = total === 0 ? 1 : gcd(total, common);
  return {lcm: common, needA, needB, sumN: total / divisor, sumD: common / divisor};
}

const PRETTY: Record<string, string> = {'1/2': '½', '1/3': '⅓', '2/3': '⅔', '1/4': '¼', '3/4': '¾', '1/5': '⅕', '2/5': '⅖', '3/5': '⅗', '4/5': '⅘', '1/6': '⅙', '5/6': '⅚', '1/8': '⅛', '3/8': '⅜', '5/8': '⅝', '7/8': '⅞', '1/10': '⅒'};

export function vulgar(n: number, d: number): string {
  return PRETTY[`${n}/${d}`] || `${n}/${d}`;
}
