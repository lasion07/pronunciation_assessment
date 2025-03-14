<template>
  <div class="main">
    <section class="section easy">
      <h2>Dễ</h2>
      <div>
        <p v-for="(sentence, index) in easySentences" :key="index">{{ sentence }}</p>
      </div>
    </section>
    <section class="section medium">
      <h2>Trung bình</h2>
      <div>
        <p v-for="(sentence, index) in mediumSentences" :key="index">{{ sentence }}</p>
      </div>
    </section>
    <section class="section hard">
      <h2>Khó</h2>
      <div>
        <p v-for="(sentence, index) in hardSentences" :key="index">{{ sentence }}</p>
      </div>
    </section>
  </div>
</template>

<script>
export default {
  data() {
    return {
      easySentences: [
        "Hello, how are you?",
        "It's a beautiful day.",
        "I like apples."
      ],
      mediumSentences: [
        "The quick brown fox jumps over the lazy dog.",
        "Can you help me with this problem?",
        "She enjoys reading books in her free time."
      ],
      hardSentences: [
        "To be, or not to be, that is the question.",
        "It is a truth universally acknowledged, that a single man in possession of a good fortune, must be in want of a wife.",
        "In the end, we will remember not the words of our enemies, but the silence of our friends."
      ]
    };
  }
};
</script>

<style scoped>
.main{
  display: flex;
  flex-direction: row;
}
.section {
  margin-bottom: 20px;
}
.section h2 {
  margin-bottom: 10px;
}
.easy h2 {
  color: green;
}
.medium h2 {
  color: orange;
}
.hard h2 {
  color: red;
}
.section p {
  background-color: #f9f9f9;
  padding: 10px;
  border-radius: 5px;
  margin-bottom: 10px;
}
</style>
