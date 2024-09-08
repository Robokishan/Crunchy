/* eslint-disable @typescript-eslint/no-unsafe-argument */
import axios, { type AxiosError, type InternalAxiosRequestConfig } from "axios";
import { getBaseURL } from "./baseUrl";

const CrunchyClient = axios.create();

// eslint-disable-next-line @typescript-eslint/no-explicit-any
const parseErrorCodeV1 = (error: AxiosError) => {
  return Promise.reject(error);
};

// Request parsing interceptor
const crunchyRequestInterceptor = (
  config: InternalAxiosRequestConfig
): InternalAxiosRequestConfig => {
  config.baseURL = getBaseURL();
  return config;
};

// Request parsing interceptor
CrunchyClient.interceptors.request.use(crunchyRequestInterceptor, (error) => {
  console.error("[REQUEST_ERROR]", error);
  return Promise.reject(error);
});

// Response parsing interceptor
CrunchyClient.interceptors.response.use(
  (response) => response,
  (error) => {
    return parseErrorCodeV1(error);
  }
);
export default CrunchyClient;
