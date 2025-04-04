import { createRouter, createWebHistory } from "vue-router";
import LoginPage from "./components/LoginPage.vue";
import PromptToGPT from "./components/PromptToGPT.vue";

const routes = [
  { path: "/", component: LoginPage },
  { path: "/promptGPT", component: PromptToGPT },
];

const router = createRouter({ history: createWebHistory(), routes });

export default router;
