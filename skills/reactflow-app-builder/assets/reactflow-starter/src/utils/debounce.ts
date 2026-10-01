export function debounce<T extends (...args: any[]) => void>(fn: T, ms: number): T {
  let t: number | undefined;
  return ((...args: any[]) => {
    if (t) window.clearTimeout(t);
    t = window.setTimeout(() => fn(...args), ms);
  }) as T;
}
