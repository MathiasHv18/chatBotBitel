import axios from "axios";

const instance=axios.create({
    // baseURL: '',
    baseURL: 'http://127.0.0.1:8000/api/table_names',
    withCredentials:true
})

export default instance;