import axios from "axios";

const instance=axios.create({
    // baseURL: '',
    baseURL: 'http://localhost:5000/api/chat',
    withCredentials:false
})

export default instance;