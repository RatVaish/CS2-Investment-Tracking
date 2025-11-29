import axios from "axios";

const API_BASE_URL = 'http://192.168.1.233:8000/app/v1';

const apiClient = axios.create({
    baseURL: API_BASE_URL,
    headers: {
        "Content-Type": "application/json",
    },
});

export default apiClient;
