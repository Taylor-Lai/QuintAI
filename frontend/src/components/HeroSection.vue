<template>
  <section class="carousel-section">
    <div class="container">
      <!-- 顶部文案区 -->
      <div class="hero-copy">
        <h1 class="hero-title">{{ settings.siteName || '让复杂文档处理变得简单高效' }}</h1>
        <p class="hero-desc">
          {{ settings.siteSubtitle || '智汇文枢聚焦文档理解、信息提取、表格填写与在线编辑，帮助你快速完成从识别、分析到处理的全流程任务。' }}
        </p>

        <div class="hero-divider">
          <span class="hero-divider-line"></span>
        </div>
      </div>

      <div
        ref="shellRef"
        class="carousel-shell"
        @mouseenter="pauseAutoPlay"
        @mouseleave="startAutoPlay"
        @mousedown="onDragStart"
        @touchstart="onDragStart"
        @mousemove="onDragMove"
        @touchmove="onDragMove"
        @mouseup="onDragEnd"
        @mouseleave.self="onDragEnd"
        @touchend="onDragEnd"
        @touchcancel="onDragEnd"
      >
        <div class="carousel-viewport">
          <div class="carousel-track">
            <div
              v-for="(item, index) in banners"
              :key="item.id"
              class="carousel-card"
              :class="[getCardClass(index), { lifted: hoveredIndex === index }]"
              @click="handleCardClick(index)"
              @mouseenter="hoveredIndex = index"
              @mouseleave="hoveredIndex = null"
            >
              <div class="card-inner">
                <img :src="item.image" :alt="item.title" class="card-image" />
                <div class="card-shade"></div>
                <div class="card-glow"></div>
                <div class="edge-vignette"></div>

                <div class="card-content">
                  <div class="card-badge">{{ item.badge }}</div>

                  <h2 class="card-title">
                    <span
                      v-for="(char, charIndex) in splitTitle(item.title)"
                      :key="`${item.id}-${charIndex}-${char}`"
                      class="title-char"
                      :class="{ active: index === currentIndex }"
                      :style="{ animationDelay: `${charIndex * 60}ms` }"
                    >
                      {{ char === ' ' ? '\u00A0' : char }}
                    </span>
                  </h2>

                  <p class="card-desc">{{ item.desc }}</p>

                  <div class="card-actions">
                    <button
                      class="primary-btn"
                      :class="{ glowing: index === currentIndex }"
                      @click.stop="goAuth(item)"
                    >
                      点击立即体验
                    </button>
                  </div>
                </div>
              </div>
            </div>
          </div>

          <button class="nav-btn prev-btn" @click="prevSlide">
            <span class="arrow arrow-left"></span>
          </button>

          <button class="nav-btn next-btn" @click="nextSlide">
            <span class="arrow arrow-right"></span>
          </button>

          <div class="bottom-bar">
            <div class="indicator-wrap">
              <span
                v-for="(item, index) in banners"
                :key="item.id"
                class="indicator"
                :class="{ active: index === currentIndex }"
                @click="goTo(index)"
              >
                <span class="indicator-inner"></span>
              </span>
            </div>
          </div>
        </div>
      </div>
    </div>
  </section>
</template>

<script setup>
import { onBeforeUnmount, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { useUserStore } from '../stores/user'

import banner1 from '../assets/banner-1.webp'
import banner2 from '../assets/banner-2.webp'
import banner3 from '../assets/banner-3.webp'

const router = useRouter()
const userStore = useUserStore()

const autoplayDelay = 5000
const currentIndex = ref(0)
const hoveredIndex = ref(null)
const shellRef = ref(null)

const settings = ref({
  siteName: '让复杂文档处理变得简单高效',
  siteSubtitle:
    '聚焦文档理解、信息提取、表格填写与在线编辑，帮助你快速完成从识别、分析到处理的全流程任务。'
})

let timer = null

const isDragging = ref(false)
const dragStartX = ref(0)
const dragCurrentX = ref(0)
const dragThreshold = 60

const banners = ref([
  {
    id: 1,
    image: banner1,
    badge: '智能文档交互',
    title: '文档智能操作交互',
    desc: '围绕文档理解、问答、摘要与隐私内容处理，构建更自然的智能交互体验',
    path: '/feature/doc-chat'
  },
  {
    id: 2,
    image: banner2,
    badge: '信息提取引擎',
    title: '非结构化文档信息提取',
    desc: '针对合同、报告、说明书等非结构化文件，提取关键字段并完成结构化输出',
    path: '/feature/doc-extract'
  },
  {
    id: 3,
    image: banner3,
    badge: '表格智能处理',
    title: '表格自定义数据填写',
    desc: '支持按规则进行表格数据填充、批量处理与业务模板生成，提升表单处理效率',
    path: '/feature/table-fill'
  }
])

const splitTitle = (title) => title.split('')

const loadSettings = () => {
  const saved = localStorage.getItem('system_settings')
  if (!saved) return

  try {
    const parsed = JSON.parse(saved)
    settings.value = {
      siteName: parsed.siteName || '让复杂文档处理变得简单高效',
      siteSubtitle:
        parsed.siteSubtitle ||
        '聚焦文档理解、信息提取、表格填写与在线编辑，帮助你快速完成从识别、分析到处理的全流程任务。'
    }
  } catch (error) {
    console.error('读取系统设置失败：', error)
  }
}

const goAuth = (item) => {
  if (userStore.isLogin) {
    router.push(item.path)
  } else {
    router.push('/auth')
  }
}

const prevSlide = () => {
  currentIndex.value =
    (currentIndex.value - 1 + banners.value.length) % banners.value.length
  restartAutoPlay()
}

const nextSlide = () => {
  currentIndex.value = (currentIndex.value + 1) % banners.value.length
  restartAutoPlay()
}

const goTo = (index) => {
  currentIndex.value = index
  restartAutoPlay()
}

const handleCardClick = (index) => {
  if (index !== currentIndex.value) {
    currentIndex.value = index
    restartAutoPlay()
  }
}

const getCardClass = (index) => {
  const total = banners.value.length
  const diff = (index - currentIndex.value + total) % total

  if (diff === 0) return 'is-active'
  if (diff === 1) return 'is-right'
  if (diff === total - 1) return 'is-left'
  return 'is-hidden'
}

const startAutoPlay = () => {
  clearInterval(timer)
  timer = setInterval(() => {
    currentIndex.value = (currentIndex.value + 1) % banners.value.length
  }, autoplayDelay)
}

const pauseAutoPlay = () => {
  clearInterval(timer)
}

const restartAutoPlay = () => {
  pauseAutoPlay()
  startAutoPlay()
}

const getClientX = (event) => {
  if (event.touches && event.touches.length > 0) {
    return event.touches[0].clientX
  }
  if (event.changedTouches && event.changedTouches.length > 0) {
    return event.changedTouches[0].clientX
  }
  return event.clientX
}

const onDragStart = (event) => {
  isDragging.value = true
  dragStartX.value = getClientX(event)
  dragCurrentX.value = dragStartX.value
  pauseAutoPlay()
}

const onDragMove = (event) => {
  if (!isDragging.value) return
  dragCurrentX.value = getClientX(event)
}

const onDragEnd = () => {
  if (!isDragging.value) return

  const deltaX = dragCurrentX.value - dragStartX.value

  if (Math.abs(deltaX) > dragThreshold) {
    if (deltaX > 0) {
      currentIndex.value =
        (currentIndex.value - 1 + banners.value.length) % banners.value.length
    } else {
      currentIndex.value = (currentIndex.value + 1) % banners.value.length
    }
  }

  isDragging.value = false
  startAutoPlay()
}

onMounted(() => {
  loadSettings()
  startAutoPlay()
})

onBeforeUnmount(() => {
  clearInterval(timer)
})
</script>

<style scoped>
.carousel-section {
  padding: 34px 0 14px;
  background: #ececec;
}

.container {
  width: 1200px;
  max-width: calc(100% - 48px);
  margin: 0 auto;
}

.hero-copy {
  max-width: 860px;
  margin: 0 auto 10px;
  text-align: center;
}

.hero-title {
  margin: 0 0 10px;
  font-size: 36px;
  line-height: 1.18;
  font-weight: 800;
  color: #2d2d2d;
  letter-spacing: -0.5px;
  font-family: serif;
}

.hero-desc {
  margin: 0;
  font-size: 22px;
  line-height: 1.82;
  color: #68645d;
  font-family: serif;
}

.hero-divider {
  display: flex;
  justify-content: center;
  align-items: center;
  margin-top: 10px;
  margin-bottom: 0;
}

.hero-divider-line {
  width: 220px;
  max-width: 42%;
  height: 1px;
  border-radius: 999px;
  background: linear-gradient(
    90deg,
    rgba(213, 176, 118, 0),
    rgba(213, 176, 118, 0.14),
    rgba(213, 176, 118, 0.28),
    rgba(213, 176, 118, 0.14),
    rgba(213, 176, 118, 0)
  );
  box-shadow:
    0 0 10px rgba(213, 176, 118, 0.06),
    0 0 18px rgba(213, 176, 118, 0.03);
}

.carousel-shell {
  position: relative;
  height: 620px;
  margin-top: -44px;
  border-radius: 28px;
  overflow: visible;
  background: transparent;
  user-select: none;
}

.carousel-viewport {
  position: relative;
  width: 100%;
  height: 100%;
  perspective: 1800px;
  transform-style: preserve-3d;
}

.carousel-track {
  position: relative;
  width: 100%;
  height: 100%;
}

.carousel-card {
  position: absolute;
  top: 50%;
  left: 50%;
  width: 72%;
  height: 460px;
  border-radius: 28px;
  overflow: visible;
  transform-style: preserve-3d;
  transition:
    transform 0.8s cubic-bezier(0.22, 1, 0.36, 1),
    opacity 0.8s ease,
    filter 0.8s ease;
  cursor: pointer;
  will-change: transform, opacity, filter;
  backface-visibility: hidden;
  -webkit-backface-visibility: hidden;
  transform-origin: center center;
}

.carousel-card.is-active {
  --rx: 0deg;
  --ry: 0deg;
}

.carousel-card.lifted.is-active {
  transform:
    translate3d(-50%, -54%, 0)
    rotateX(var(--rx))
    rotateY(var(--ry))
    scale(1.02);
}

.carousel-card.lifted.is-left {
  transform: translate3d(-88%, -50%, 0) rotateY(26deg) scale(0.87);
}

.carousel-card.lifted.is-right {
  transform: translate3d(-12%, -50%, 0) rotateY(-26deg) scale(0.87);
}

.carousel-card.is-active:hover {
  transform:
    translate3d(-50%, -54%, 0)
    rotateX(var(--rx, -2deg))
    rotateY(var(--ry, 2deg))
    scale(1.025);
}

.card-inner {
  position: relative;
  width: 100%;
  height: 100%;
  border-radius: 28px;
  overflow: hidden;
  background: #ddd;
  border: 1px solid rgba(255, 255, 255, 0.06);
  box-shadow:
    0 10px 30px rgba(0, 0, 0, 0.06),
    0 1px 0 rgba(255, 255, 255, 0.04) inset;
  transform-style: preserve-3d;
  transition:
    box-shadow 0.35s ease,
    transform 0.35s ease;
  isolation: isolate;
  backface-visibility: hidden;
  -webkit-backface-visibility: hidden;
}

.carousel-card.is-active:hover .card-inner {
  box-shadow:
    0 16px 40px rgba(0, 0, 0, 0.1),
    0 1px 0 rgba(255, 255, 255, 0.05) inset;
}

.card-image {
  width: 100%;
  height: 100%;
  object-fit: cover;
  display: block;
  transform: scale(1.02) translateZ(0);
  transition: transform 0.45s ease;
  backface-visibility: hidden;
  -webkit-backface-visibility: hidden;
}

.carousel-card.is-active:hover .card-image {
  transform: scale(1.04) translateZ(0);
}

.card-shade {
  position: absolute;
  inset: 0;
  background: linear-gradient(
    95deg,
    rgba(0, 0, 0, 0.35) 0%,
    rgba(0, 0, 0, 0.18) 30%,
    rgba(0, 0, 0, 0.06) 60%,
    rgba(0, 0, 0, 0.08) 100%
  );
  pointer-events: none;
}

.card-glow {
  position: absolute;
  inset: 0;
  background:
    radial-gradient(circle at 18% 18%, rgba(255, 255, 255, 0.04), transparent 18%),
    radial-gradient(circle at 82% 82%, rgba(255, 255, 255, 0.025), transparent 20%);
  pointer-events: none;
  transition: opacity 0.35s ease;
  opacity: 0.8;
}

.carousel-card.is-active:hover .card-glow {
  opacity: 1;
}

.edge-vignette {
  position: absolute;
  inset: 0;
  pointer-events: none;
  background:
    linear-gradient(
      90deg,
      rgba(0, 0, 0, 0.14) 0%,
      rgba(0, 0, 0, 0.05) 5%,
      transparent 12%,
      transparent 88%,
      rgba(0, 0, 0, 0.05) 95%,
      rgba(0, 0, 0, 0.14) 100%
    ),
    linear-gradient(
      180deg,
      rgba(0, 0, 0, 0.08) 0%,
      transparent 12%,
      transparent 88%,
      rgba(0, 0, 0, 0.08) 100%
    );
}

.card-content {
  position: absolute;
  left: 52px;
  top: 54px;
  max-width: 450px;
  z-index: 3;
  color: #fff;
  transform: translateZ(42px);
  transition: transform 0.35s ease;
}

.carousel-card.is-active:hover .card-content {
  transform: translateZ(58px);
}

.card-badge {
  display: inline-flex;
  align-items: center;
  height: 36px;
  padding: 0 14px;
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.14);
  border: 1px solid rgba(255, 255, 255, 0.16);
  backdrop-filter: blur(8px);
  font-size: 13px;
  margin-bottom: 18px;
  transform: translateZ(26px);
  font-family: serif;
}

.card-title {
  margin: 0 0 16px;
  font-size: 42px;
  line-height: 1.15;
  font-weight: 800;
  min-height: 96px;
  text-shadow: 0 8px 28px rgba(0, 0, 0, 0.16);
  transform: translateZ(32px);
  font-family: serif;
}

.title-char {
  display: inline-block;
  opacity: 0.2;
  transform: translateY(8px);
}

.is-active .title-char.active {
  animation: charReveal 0.65s ease forwards;
}

@keyframes charReveal {
  from {
    opacity: 0;
    transform: translateY(14px);
    filter: blur(4px);
  }

  to {
    opacity: 1;
    transform: translateY(0);
    filter: blur(0);
  }
}

.card-desc {
  margin: 0 0 28px;
  font-size: 18px;
  line-height: 1.9;
  color: rgba(255, 255, 255, 0.9);
  text-shadow: 0 4px 16px rgba(0, 0, 0, 0.12);
  transform: translateZ(24px);
  font-family: serif;
}

.card-actions {
  display: flex;
  gap: 14px;
  flex-wrap: wrap;
  transform: translateZ(36px);
}

.primary-btn {
  min-width: 156px;
  height: 46px;
  border-radius: 24px;
  border: none;
  background: #d5b076;
  color: #fff;
  font-size: 15px;
  font-weight: 700;
  cursor: pointer;
  box-shadow: 0 8px 18px rgba(213, 176, 118, 0.2);
  font-family: serif;
  transition:
    transform 0.22s ease,
    opacity 0.22s ease,
    box-shadow 0.22s ease;
}

.primary-btn:hover {
  transform: translateY(-2px);
}

.primary-btn.glowing {
  animation: pulseGlow 1.8s ease-in-out infinite;
}

@keyframes pulseGlow {
  0% {
    box-shadow:
      0 0 0 rgba(213, 176, 118, 0.08),
      0 8px 18px rgba(213, 176, 118, 0.18);
  }

  50% {
    box-shadow:
      0 0 18px rgba(213, 176, 118, 0.24),
      0 8px 24px rgba(213, 176, 118, 0.24);
  }

  100% {
    box-shadow:
      0 0 0 rgba(213, 176, 118, 0.08),
      0 8px 18px rgba(213, 176, 118, 0.18);
  }
}

.is-active {
  opacity: 1;
  z-index: 4;
  transform:
    translate3d(-50%, -52%, 0)
    rotateX(var(--rx))
    rotateY(var(--ry))
    scale(1);
  filter: none;
}

.is-left {
  opacity: 0.76;
  z-index: 3;
  transform: translate3d(-88%, -48%, 0) rotateY(26deg) scale(0.84);
  filter: brightness(0.9) saturate(0.94);
}

.is-right {
  opacity: 0.76;
  z-index: 3;
  transform: translate3d(-12%, -48%, 0) rotateY(-26deg) scale(0.84);
  filter: brightness(0.9) saturate(0.94);
}

.is-hidden {
  opacity: 0;
  z-index: 1;
  transform: translate3d(-50%, -50%, 0) scale(0.72);
  pointer-events: none;
}

.nav-btn {
  position: absolute;
  top: 50%;
  transform: translateY(-50%);
  width: 44px;
  height: 44px;
  border: none;
  background: transparent;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 10;
  cursor: pointer;
  opacity: 0;
  transition: opacity 0.25s ease;
}

.carousel-shell:hover .nav-btn {
  opacity: 0.35;
}

.nav-btn:hover {
  opacity: 1;
}

.prev-btn {
  left: -26px;
}

.next-btn {
  right: -26px;
}

.arrow {
  width: 10px;
  height: 10px;
  border-top: 2px solid rgba(255, 255, 255, 0.88);
  border-right: 2px solid rgba(255, 255, 255, 0.88);
}

.arrow-left {
  transform: rotate(-135deg);
}

.arrow-right {
  transform: rotate(45deg);
}

.bottom-bar {
  position: absolute;
  left: 0;
  right: 0;
  bottom: 30px;
  display: flex;
  justify-content: center;
  z-index: 6;
}

.indicator-wrap {
  display: flex;
  gap: 12px;
}

.indicator {
  width: 38px;
  height: 6px;
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.24);
  overflow: hidden;
  cursor: pointer;
  position: relative;
}

.indicator-inner {
  position: absolute;
  inset: 0;
  background: linear-gradient(90deg, #e2c595, #d5b076);
  transform: scaleX(0);
  transform-origin: left center;
  transition: transform 0.35s ease;
}

.indicator.active .indicator-inner {
  transform: scaleX(1);
}

@media (max-width: 1100px) {
  .carousel-section {
    padding-top: 28px;
  }

  .hero-copy {
    max-width: 760px;
    margin-bottom: 8px;
  }

  .hero-title {
    font-size: 32px;
  }

  .hero-desc {
    font-size: 14px;
  }

  .hero-divider {
    margin-top: 8px;
  }

  .hero-divider-line {
    width: 190px;
  }

  .carousel-shell {
    height: 600px;
    margin-top: -28px;
  }

  .carousel-card {
    width: 82%;
    height: 410px;
  }

  .card-content {
    left: 34px;
    top: 34px;
    max-width: 380px;
  }

  .card-title {
    font-size: 34px;
    min-height: 82px;
  }

  .is-left {
    transform: translate3d(-86%, -48%, 0) rotateY(22deg) scale(0.84);
  }

  .is-right {
    transform: translate3d(-14%, -48%, 0) rotateY(-22deg) scale(0.84);
  }

  .prev-btn {
    left: -18px;
  }

  .next-btn {
    right: -18px;
  }
}

@media (max-width: 768px) {
  .carousel-section {
    padding-top: 24px;
    padding-bottom: 10px;
  }

  .container {
    max-width: calc(100% - 24px);
  }

  .hero-copy {
    margin-bottom: 8px;
  }

  .hero-title {
    font-size: 26px;
    line-height: 1.24;
    margin-bottom: 8px;
  }

  .hero-desc {
    font-size: 13px;
    line-height: 1.76;
  }

  .hero-divider {
    margin-top: 8px;
  }

  .hero-divider-line {
    width: 150px;
    max-width: 52%;
  }

  .carousel-shell {
    height: 430px;
    margin-top: -14px;
  }

  .carousel-viewport {
    perspective: 1200px;
  }

  .carousel-card {
    width: 100%;
    height: 320px;
  }

  .is-active {
    transform: translate3d(-50%, -50%, 0) scale(1);
  }

  .is-left,
  .is-right {
    opacity: 0;
    pointer-events: none;
    transform: translate3d(-50%, -50%, 0) scale(0.92);
  }

  .card-content {
    left: 22px;
    top: 22px;
    right: 22px;
    max-width: none;
  }

  .card-badge {
    height: 30px;
    padding: 0 12px;
    font-size: 12px;
    margin-bottom: 12px;
  }

  .card-title {
    font-size: 26px;
    min-height: auto;
    margin-bottom: 12px;
  }

  .card-desc {
    font-size: 14px;
    line-height: 1.7;
    margin-bottom: 20px;
  }

  .primary-btn {
    min-width: 132px;
    height: 40px;
    font-size: 14px;
  }

  .bottom-bar {
    bottom: 16px;
  }

  .nav-btn {
    display: none;
  }
}
</style>
