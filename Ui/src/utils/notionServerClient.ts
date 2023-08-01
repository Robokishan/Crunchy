import axios, { AxiosError, AxiosRequestConfig } from "axios";

const notionClient = axios.create();

// eslint-disable-next-line @typescript-eslint/no-explicit-any
const parseErrorCodeV1 = (error: AxiosError) => {
  return Promise.reject(error);
};

// Request parsing interceptor
const notionRequestInterceptor = (
  config: AxiosRequestConfig
): AxiosRequestConfig => {
  config.baseURL = "https://api.notion.com";
  config.headers = {
    ...config.headers,
    Authorization: "Bearer " + process.env.NOTION_CLIENT_SECRET,
    "Notion-Version": "2021-08-16",
  };
  return config;
};

// Request parsing interceptor
notionClient.interceptors.request.use(notionRequestInterceptor, (error) => {
  console.error("[REQUEST_ERROR]", error);
  return Promise.reject(error);
});

// Response parsing interceptor
notionClient.interceptors.response.use(
  (response) => response,
  (error) => {
    return parseErrorCodeV1(error);
  }
);
export default notionClient;
