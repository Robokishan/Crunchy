import { isServer } from "./serverSide/isServer";

export const getBaseURL = () =>
  isServer()
    ? process.env.CRUNCHY_REST
    : `http://${window.location.hostname}:8001`;
