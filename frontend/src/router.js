import { createRouter, createWebHistory } from "vue-router";
import DatabaseTableSelector from "./components/DatabaseTableSelector.vue";
import PromptToGPT from "./components/PromptToGPT.vue";

const routes = [
  { path: "/", component: DatabaseTableSelector },
  { path: "/prompt", component: PromptToGPT },
];

const router = createRouter({ history: createWebHistory(), routes });

export default router;
