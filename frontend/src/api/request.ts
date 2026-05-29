import axios from "axios";
import { message } from "antd";
import type { ApiResponse } from "../types/sql";

const request = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || "",
  timeout: 20000
});

request.interceptors.response.use(
  (response) => {
    const body = response.data as ApiResponse<unknown>;
    if (body.code !== 0) {
      message.error(body.message || "请求失败");
      return Promise.reject(new Error(body.message || "请求失败"));
    }
    return response;
  },
  (error) => {
    message.error(error?.response?.data?.message || error.message || "网络异常");
    return Promise.reject(error);
  }
);

export default request;
