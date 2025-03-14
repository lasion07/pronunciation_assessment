// MicrophoneIcon.vue
<template>
    <svg  
    xmlns="http://www.w3.org/2000/svg"  
    width="50"  
    height="50"  
    viewBox="0 0 24 24"  
    fill="none"  
    stroke="currentColor"  
    stroke-width="1"  
    stroke-linecap="round"  
    stroke-linejoin="round"  
    :class='iconClass'>
    <path stroke="none" d="M0 0h24v24H0z" fill="none"/>
    <path d="M3 19a9 9 0 0 1 9 0a9 9 0 0 1 9 0" />
    <path d="M3 6a9 9 0 0 1 9 0a9 9 0 0 1 9 0" />
    <path d="M3 6l0 13" />
    <path d="M12 6l0 13" />
    <path d="M21 6l0 13" /></svg>
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
      return 'icon icon-tabler icons-tabler-outline icon-tabler-book';
    }
  }
};
</script>

<style scoped>

</style>
