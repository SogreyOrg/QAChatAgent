<script setup>
import MainLayout from '@/components/layout/MainLayout.vue'
</script>

<template>
  <MainLayout>
    <router-view />
  </MainLayout>
</template>

<style>
#app {
  height: 100vh;
  width: 100vw;
  overflow: hidden;
}
</style>
