export function sleep(ms) {
  return new Promise((r) => setTimeout(r, ms));
}

export async function withRetry(fn, options = {}) {
  const {
    retries = 3,
    baseDelayMs = 250,
    maxDelayMs = 3000,
    jitter = true,
    shouldRetry = (err) => true
  } = options;

  let attempt = 0;
  // eslint-disable-next-line no-constant-condition
  while (true) {
    try {
      return await fn({ attempt });
    } catch (err) {
      attempt += 1;
      if (attempt > retries || !shouldRetry(err)) throw err;

      let delay = Math.min(maxDelayMs, baseDelayMs * 2 ** (attempt - 1));
      if (jitter) delay = Math.floor(delay * (0.5 + Math.random()));

      await sleep(delay);
    }
  }
}
