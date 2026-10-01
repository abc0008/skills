export function log(level, message, fields = {}) {
  const payload = {
    ts: new Date().toISOString(),
    level,
    message,
    ...fields
  };
  process.stdout.write(JSON.stringify(payload) + "\n");
}

export function info(message, fields) {
  log("info", message, fields);
}

export function warn(message, fields) {
  log("warn", message, fields);
}

export function error(message, fields) {
  log("error", message, fields);
}
