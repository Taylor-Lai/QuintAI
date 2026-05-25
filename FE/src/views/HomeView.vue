<template>
  <div class="home-page">
    <AppHeader />
    <HeroSection />
    <SummarySection />
  </div>
</template>

<script setup>
import AppHeader from '../components/AppHeader.vue'
import HeroSection from '../components/HeroSection.vue'
import SummarySection from '../components/SummarySection.vue'
</script>

<style scoped>
.home-page {
  min-height: 100vh;
  background: #ececec;
}
</style>