declare const __CRUNCHY_REST__: string | undefined;

export const getBaseURL = () => {
  const envBase =
    typeof __CRUNCHY_REST__ !== "undefined" && __CRUNCHY_REST__
      ? __CRUNCHY_REST__
      : undefined;

  if (envBase) {
    return envBase;
  }

  if (typeof window !== "undefined") {
    return `http://${window.location.hostname}:8001`;
  }

  return process.env.CRUNCHY_REST ?? "http://localhost:8001";
};