<template>
  <div class="container">
    <canvas ref="canvasRef"></canvas>
    <div class="login-box">
      <h2>Chatbot Login</h2>
      <input
        type="text"
        placeholder="Username"
        v-model="username"
        @keydown.enter="handleLogin"
      />
      <input
        type="password"
        placeholder="Password"
        v-model="password"
        @keydown.enter="handleLogin"
      />
      <button @click="handleLogin">Login</button>
    </div>
  </div>
</template>
<script setup>
import { onMounted, ref } from "vue";
import { useRouter } from "vue-router";

const username = ref("");
const password = ref("");
const canvasRef = ref(null);
const router = useRouter(); // Importa el router

const handleLogin = () => {
  if (username.value === "minda" && password.value === "letmein") {
    console.log("Logging in with", username.value, password.value);
    router.push("/promptGPT"); // Redirige a /promptGPT
  } else {
    alert("Please enter both username and password.");
  }
};

onMounted(() => {
  const canvas = canvasRef.value;
  const ctx = canvas.getContext("2d");

  canvas.width = window.innerWidth;
  canvas.height = window.innerHeight;

  const letters = "0123456789ABCDEF";
  const fontSize = 16;
  const columns = canvas.width / fontSize;
  const drops = Array.from({ length: columns }).map(
    () => Math.random() * canvas.height
  );

  function drawMatrix() {
    ctx.fillStyle = "rgba(0, 0, 0, 0.1)";
    ctx.fillRect(0, 0, canvas.width, canvas.height);

    ctx.fillStyle = "#0f0";
    ctx.font = `${fontSize}px monospace`;

    drops.forEach((y, i) => {
      const text = letters[Math.floor(Math.random() * letters.length)];
      const x = i * fontSize;
      ctx.fillText(text, x, y);
      drops[i] = y > canvas.height || Math.random() > 0.975 ? 0 : y + fontSize;
    });
  }

  setInterval(drawMatrix, 50);

  // Handle window resize
  window.addEventListener("resize", () => {
    canvas.width = window.innerWidth;
    canvas.height = window.innerHeight;
  });
});
</script>

<style scoped>
.container {
  position: relative;
  width: 100vw;
  height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background-color: black;
  overflow: hidden;
}

canvas {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  z-index: 1;
}

.login-box {
  position: relative;
  z-index: 2;
  width: 320px;
  padding: 30px;
  background-color: rgba(0, 0, 0, 0.8);
  border: 1px solid #00ff00;
  border-radius: 8px;
  box-shadow: 0 0 20px rgba(0, 255, 0, 0.3);
  text-align: center;
}

h2 {
  margin-bottom: 20px;
  color: #00ff00;
  font-size: 24px;
  font-family: monospace;
}

input {
  width: 100%;
  padding: 10px;
  margin-bottom: 15px;
  background-color: transparent;
  border: 1px solid #00ff00;
  color: #00ff00;
  outline: none;
  font-family: monospace;
}

input::placeholder {
  color: #00aa00;
}

input:focus {
  box-shadow: 0 0 5px #00ff00;
}

button {
  width: 100%;
  padding: 10px;
  background-color: #00ff00;
  color: black;
  border: none;
  border-radius: 4px;
  font-weight: bold;
  cursor: pointer;
  font-family: monospace;
  transition: background-color 0.3s;
}

button:hover {
  background-color: #00cc00;
}
</style>
