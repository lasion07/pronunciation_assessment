<template>
  <svg xmlns="http://www.w3.org/2000/svg" 
    width="50"
    height="50"
    viewBox="0 0 448 512"
    fill="none"
    stroke="rgb(255, 255, 255)"
    stroke-width="50"
    stroke-linecap="round"
    stroke-linejoin="round"><path d="M400 32H48C21.5 32 0 53.5 0 80v352c0 26.5 21.5 48 48 48h352c26.5 0 48-21.5 48-48V80c0-26.5-21.5-48-48-48z"/></svg>
</template>

<script>
export default {
  props: {
    size: {
      type: String,
      default: '24px'
    },
    color: {
      type: String,
      default: 'currentColor'
    }
  },
  computed: {
    iconClass() {
      return 'icon icon-tabler icons-tabler-outline icon-tabler-microphone';
    }
  },
  isRecording: {
      type: Boolean,
      required: true,
    },
};
</script>

<style scoped>
/* Các style cho icon */
  
</style>
