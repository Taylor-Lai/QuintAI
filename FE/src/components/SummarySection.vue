<template>
  <section class="summary-section">
    <!-- 顶部雾化层 -->
    <div class="top-fog"></div>

    <!-- 网格 -->
    <div class="grid"></div>

    <!-- 金色光晕 -->
    <div class="glow glow1"></div>
    <div class="glow glow2"></div>

    <!-- 扫光 -->
    <div class="scan"></div>

    <!-- 粒子 -->
    <div class="particles">
      <span v-for="n in 28" :key="`p-${n}`" class="particle"></span>
    </div>

    <!-- 星点 -->
    <div class="stars">
      <span v-for="n in 20" :key="`s-${n}`" class="star"></span>
    </div>

    <!-- AI 网络线 -->
    <svg class="network" viewBox="0 0 1200 200" preserveAspectRatio="none">
      <line x1="0" y1="120" x2="300" y2="80" />
      <line x1="300" y1="80" x2="600" y2="140" />
      <line x1="600" y1="140" x2="900" y2="90" />
      <line x1="900" y1="90" x2="1200" y2="130" />
    </svg>

    <!-- 内容层 -->
    <div class="container content-layer">
      <div class="feature-grid">
        <div class="feature-card">
          <div class="feature-index">01</div>
          <div class="feature-name">智能理解</div>
          <div class="feature-text">
            支持文档问答、摘要生成与重点定位，帮助你快速掌握文档核心内容。
          </div>
        </div>

        <div class="feature-card">
          <div class="feature-index">02</div>
          <div class="feature-name">精准提取</div>
          <div class="feature-text">
            面向合同、报告、说明书等非结构化文档，抽取关键字段并结构化输出。
          </div>
        </div>

        <div class="feature-card">
          <div class="feature-index">03</div>
          <div class="feature-name">高效处理</div>
          <div class="feature-text">
            结合模板填写与在线编辑能力，提升日常文档流转和业务处理效率。
          </div>
        </div>
      </div>

      <div class="action-row">
        <button class="primary-btn" @click="handleStart">
          立即开始体验
        </button>
        <button class="secondary-btn" @click="goGuide">
          查看上手指南
        </button>
      </div>

      <div class="footer-note">
        © 2026 智汇文枢 · 智能文档处理平台
      </div>
    </div>
  </section>
</template>

<script setup>
import { useRouter } from 'vue-router'
import { useUserStore } from '../store/modules/user'

const router = useRouter()
const userStore = useUserStore()

const handleStart = () => {
  if (userStore.isLogin) {
    router.push('/feature/doc-chat')
  } else {
    router.push('/auth')
  }
}

const goGuide = () => {
  router.push('/guide')
}
</script>

<style scoped>
.summary-section {
  position: relative;
  overflow: hidden;
  min-height: 285px;
  padding: 24px 0 20px;
  background: linear-gradient(
    180deg,
    #ececec 0%,
    #e8e5df 42%,
    #e3dfd6 100%
  );
}

.container {
  width: 1200px;
  max-width: calc(100% - 48px);
  margin: 0 auto;
  position: relative;
  z-index: 10;
}

/* 顶部雾化 */
.top-fog {
  position: absolute;
  top: -36px;
  left: -10%;
  width: 120%;
  height: 110px;
  background: radial-gradient(
    ellipse at center,
    rgba(236, 236, 236, 0.94) 0%,
    rgba(236, 236, 236, 0.7) 32%,
    rgba(236, 236, 236, 0.28) 62%,
    rgba(236, 236, 236, 0) 100%
  );
  filter: blur(22px);
  z-index: 8;
}

/* 网格 */
.grid {
  position: absolute;
  inset: 0;
  background-image:
    linear-gradient(rgba(184, 140, 71, 0.05) 1px, transparent 1px),
    linear-gradient(90deg, rgba(184, 140, 71, 0.05) 1px, transparent 1px);
  background-size: 36px 36px;
  mask-image: linear-gradient(180deg, transparent 0%, black 20%, black 100%);
}

/* 光晕 */
.glow {
  position: absolute;
  border-radius: 50%;
  filter: blur(18px);
  animation: float 12s ease-in-out infinite;
}

.glow1 {
  width: 160px;
  height: 160px;
  left: 5%;
  top: 48px;
  background: radial-gradient(
    circle,
    rgba(213, 176, 118, 0.18),
    rgba(213, 176, 118, 0.02) 72%
  );
}

.glow2 {
  width: 200px;
  height: 200px;
  right: 7%;
  top: 54px;
  background: radial-gradient(
    circle,
    rgba(255, 255, 255, 0.38),
    rgba(255, 255, 255, 0.03) 72%
  );
  animation-delay: -6s;
}

/* 扫光 */
.scan {
  position: absolute;
  width: 35%;
  height: 180%;
  top: -42%;
  background: linear-gradient(
    90deg,
    transparent,
    rgba(230, 197, 140, 0.14),
    transparent
  );
  filter: blur(10px);
  transform: rotate(18deg);
  animation: scanMove 11s linear infinite;
}

.particles,
.stars {
  position: absolute;
  inset: 0;
  pointer-events: none;
}

/* 粒子 */
.particle {
  position: absolute;
  width: 3px;
  height: 3px;
  background: #cda76b;
  border-radius: 50%;
  box-shadow: 0 0 6px rgba(213, 176, 118, 0.42);
  animation: particle 16s linear infinite;
}

.particle:nth-child(1) { left: 6%; top: 78%; }
.particle:nth-child(2) { left: 12%; top: 82%; }
.particle:nth-child(3) { left: 18%; top: 72%; }
.particle:nth-child(4) { left: 24%; top: 88%; }
.particle:nth-child(5) { left: 30%; top: 76%; }
.particle:nth-child(6) { left: 36%; top: 86%; }
.particle:nth-child(7) { left: 42%; top: 74%; }
.particle:nth-child(8) { left: 48%; top: 84%; }
.particle:nth-child(9) { left: 54%; top: 78%; }
.particle:nth-child(10) { left: 60%; top: 87%; }
.particle:nth-child(11) { left: 66%; top: 74%; }
.particle:nth-child(12) { left: 72%; top: 82%; }
.particle:nth-child(13) { left: 78%; top: 76%; }
.particle:nth-child(14) { left: 84%; top: 88%; }
.particle:nth-child(15) { left: 90%; top: 79%; }
.particle:nth-child(16) { left: 10%; top: 68%; }
.particle:nth-child(17) { left: 20%; top: 63%; }
.particle:nth-child(18) { left: 28%; top: 66%; }
.particle:nth-child(19) { left: 38%; top: 62%; }
.particle:nth-child(20) { left: 46%; top: 67%; }
.particle:nth-child(21) { left: 58%; top: 64%; }
.particle:nth-child(22) { left: 68%; top: 66%; }
.particle:nth-child(23) { left: 76%; top: 62%; }
.particle:nth-child(24) { left: 86%; top: 67%; }
.particle:nth-child(25) { left: 15%; top: 90%; }
.particle:nth-child(26) { left: 35%; top: 91%; }
.particle:nth-child(27) { left: 62%; top: 92%; }
.particle:nth-child(28) { left: 82%; top: 90%; }

.particle:nth-child(odd) {
  animation-duration: 20s;
}

.particle:nth-child(even) {
  animation-duration: 14s;
}

/* 星点 */
.star {
  position: absolute;
  width: 2px;
  height: 2px;
  border-radius: 50%;
  background: white;
  box-shadow:
    0 0 6px rgba(255, 255, 255, 0.65),
    0 0 12px rgba(213, 176, 118, 0.32);
  animation: star 4s ease-in-out infinite;
}

.star:nth-child(1) { left: 8%; top: 18%; }
.star:nth-child(2) { left: 16%; top: 28%; }
.star:nth-child(3) { left: 22%; top: 16%; }
.star:nth-child(4) { left: 30%; top: 24%; }
.star:nth-child(5) { left: 38%; top: 14%; }
.star:nth-child(6) { left: 44%; top: 28%; }
.star:nth-child(7) { left: 52%; top: 18%; }
.star:nth-child(8) { left: 58%; top: 26%; }
.star:nth-child(9) { left: 66%; top: 16%; }
.star:nth-child(10) { left: 74%; top: 22%; }
.star:nth-child(11) { left: 82%; top: 16%; }
.star:nth-child(12) { left: 88%; top: 28%; }
.star:nth-child(13) { left: 12%; top: 40%; }
.star:nth-child(14) { left: 26%; top: 42%; }
.star:nth-child(15) { left: 40%; top: 38%; }
.star:nth-child(16) { left: 56%; top: 40%; }
.star:nth-child(17) { left: 70%; top: 38%; }
.star:nth-child(18) { left: 80%; top: 42%; }
.star:nth-child(19) { left: 92%; top: 36%; }
.star:nth-child(20) { left: 48%; top: 12%; }

.star:nth-child(odd) {
  animation-delay: -2s;
}

/* AI 网络 */
.network {
  position: absolute;
  bottom: 0;
  width: 100%;
  height: 100%;
  stroke: rgba(184, 140, 71, 0.18);
  stroke-width: 1;
  fill: none;
  animation: network 12s ease-in-out infinite;
}

/* 内容层 */
.content-layer {
  display: flex;
  flex-direction: column;
  align-items: center;
  text-align: center;
  padding-top: 14px;
}

.feature-grid {
  width: 100%;
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 14px;
  margin-bottom: 16px;
}

.feature-card {
  position: relative;
  padding: 16px 16px 14px;
  border-radius: 16px;
  text-align: left;
  background: rgba(255, 255, 255, 0.44);
  border: 1px solid rgba(213, 176, 118, 0.12);
  box-shadow: 0 6px 18px rgba(0, 0, 0, 0.03);
  backdrop-filter: blur(8px);
  transition:
    transform 0.22s ease,
    box-shadow 0.22s ease,
    border-color 0.22s ease;
}

.feature-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 10px 22px rgba(0, 0, 0, 0.045);
  border-color: rgba(213, 176, 118, 0.22);
}

.feature-index {
  font-size: 12px;
  font-weight: 700;
  color: #b48742;
  margin-bottom: 6px;
  letter-spacing: 1px;
  font-family: serif;
}

.feature-name {
  font-size: 17px;
  font-weight: 700;
  color: #2d2d2d;
  margin-bottom: 6px;
  font-family: serif;
}

.feature-text {
  font-size: 13px;
  line-height: 1.75;
  color: #666;
  font-family: serif;
}

.action-row {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 10px;
  flex-wrap: wrap;
  margin-bottom: 12px;
}

.primary-btn,
.secondary-btn {
  min-width: 138px;
  height: 38px;
  padding: 0 18px;
  border-radius: 20px;
  font-size: 14px;
  font-weight: 700;
  cursor: pointer;
  font-family: serif;
  transition:
    transform 0.2s ease,
    box-shadow 0.2s ease,
    background 0.2s ease;
}

.primary-btn {
  border: none;
  background: #d5b076;
  color: #fff;
  box-shadow: 0 6px 16px rgba(213, 176, 118, 0.16);
}

.primary-btn:hover {
  transform: translateY(-1px);
  background: #c79d62;
}

.secondary-btn {
  border: 1px solid rgba(213, 176, 118, 0.24);
  background: rgba(255, 255, 255, 0.58);
  color: #8c672f;
  backdrop-filter: blur(8px);
}

.secondary-btn:hover {
  transform: translateY(-1px);
  background: rgba(255, 255, 255, 0.82);
}

.footer-note {
  font-size: 14px;
  color: #8c857b;
  letter-spacing: 0.2px;
  font-family: serif;
}

/* 动画 */
@keyframes float {
  0% { transform: translateY(0); }
  50% { transform: translateY(-8px); }
  100% { transform: translateY(0); }
}

@keyframes scanMove {
  0% { transform: translateX(-200%) rotate(18deg); }
  100% { transform: translateX(400%) rotate(18deg); }
}

@keyframes particle {
  0% {
    transform: translateY(0);
    opacity: 0;
  }
  10% {
    opacity: 1;
  }
  100% {
    transform: translateY(-100px);
    opacity: 0;
  }
}

@keyframes star {
  0%, 100% {
    opacity: 0.3;
    transform: scale(0.8);
  }
  50% {
    opacity: 1;
    transform: scale(1.5);
  }
}

@keyframes network {
  0%, 100% {
    opacity: 0.18;
  }
  50% {
    opacity: 0.4;
  }
}

@media (max-width: 992px) {
  .summary-section {
    min-height: auto;
    padding: 20px 0 16px;
  }

  .feature-grid {
    grid-template-columns: 1fr;
    gap: 10px;
  }

  .content-layer {
    padding-top: 10px;
  }

  .container {
    max-width: calc(100% - 24px);
  }
}

@media (max-width: 768px) {
  .summary-section {
    padding: 18px 0 14px;
  }

  .content-layer {
    padding-top: 8px;
  }

  .feature-grid {
    margin-bottom: 14px;
  }

  .feature-card {
    padding: 14px 14px 12px;
  }

  .feature-name {
    font-size: 16px;
  }

  .feature-text {
    font-size: 12px;
    line-height: 1.7;
  }

  .action-row {
    width: 100%;
    flex-direction: column;
    gap: 8px;
    margin-bottom: 10px;
  }

  .primary-btn,
  .secondary-btn {
    width: 100%;
  }

  .footer-note {
    text-align: center;
    line-height: 1.6;
  }
}
</style>