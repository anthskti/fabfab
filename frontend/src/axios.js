import axios from "axios";

const userApi = axios.create({
  baseURL: process.env.USER_API_BASE_URL,
  headers: {
    "Content-Type": "application/json",
  },
});

export default userApi;