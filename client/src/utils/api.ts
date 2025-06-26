import axios from 'axios';
import { initData } from "@telegram-apps/sdk"

const BASE_API_URL = import.meta.env.VITE_API_URL

const request = async (endpoint: string, method: string = "GET", data?: any) => {
    const url = `${BASE_API_URL}/api/${endpoint}`;
    console.log(`Making request to: ${url}`);
    
    const response = await axios.request({
        url: url,
        method: method,
        headers: {
            initData:`${initData.raw()}`,
            Accept: "application/json",
            "Content-Type": "application/json",
        },
        data: data ? JSON.stringify(data) : undefined,
    })

    return response.data
}

export default request;