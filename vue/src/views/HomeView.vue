<template>
  <div class="home-container">
    <div class="main-element">
      <div class="main-container">
        <div class="main-content">
          <div class="header">
            <div class="process">
              <div class="icon-x">
                <!-- <IconX/> -->
              </div>
              <div class="progress-tool">
                <div class="progress-container">
                  <div class="progress-bar" :style="{ width: progress + '%', height: '100%', position: 'absolute'}"></div>
                </div>
              </div>
            </div>
          </div>
          <!-- <p>READ THE SENTENCES ALOUD</p> -->
          <div class="content">
            <div id="sentence">
              <span v-for="(wordObj, index) in coloredWords" :key="index" :class="wordObj.color">
                {{ wordObj.word }}
                <span v-if="index !== coloredWords.length - 1">&nbsp;</span>
              </span>
            </div>
            <!--transcription-->
            <div id="sentence">
              <span v-for="(word, index) in current_ipa_text.split(' ')" :key="index">
                {{ word }}
                <span v-if="index !== current_ipa_text.split(' ').length - 1">&nbsp;</span>
              </span>
            </div>
            <div id="ipa-result" :style="{ display: display_words, fontSize: size_words + 'px', 'margin-top': topmr + 'px' }">
              <span v-for="(charObj, index) in color_ipa" :key="index" :class="charObj.color">
                {{ charObj.char }}
              </span>
            </div>
            <div id="ipa-result" :style="{ display: display_words, fontSize: size_words + 'px', 'margin-top': topmr + 'px' }">
              <span >
                {{ prediction }}
              </span>
            </div>
            <!-- <div id="pred">
              prediction.value
            </div> -->
            <!-- <div id="ipa-pred" :style="{ display: display_words, fontSize: size_words + 'px', 'margin-top': topmr + 'px' }">
              {{ prediction.value }}
            </div>             -->
          </div>
          <audio ref="audioPlayer" controls style="display: none;"></audio>
          <div id="waveform"></div>
          <div class="icon-container">
            <div id="play_user_record_btn" class="button volume" @click="playRecordedAudio">
              <IconVolume />
            </div>
            <div id="record-button" class="button icon-mic" @click="startRecording">
              <IconMic />
            </div>
            <div id="stop-button" class="button stop-mic" style="display: none;"  @click="stopRecording">
              <IconStop />
            </div>
            <div id="play_sample_record_btn" class="button ear" @click="playSampleAudio">
              <IconEar />
            </div>
          </div>
        </div>
      </div>
      <div class="display-result">
        <div class="score-result">
          <div class="circle" :style="{ '--percentage': percentage + '%' }">
            <div class="circle-inner">
              <span class="score">{{ score }}%</span>
            </div>
          </div>
        </div>
      </div>
    </div>
    <div class="footer">
      <div class="divider"></div>
      <div class="button-container">
        <button @click="previousSentence">PREVIOUS</button>
        <button @click="nextSentence">NEXT</button>
      </div>
    </div>
  </div>
</template>
<script setup>
import { ref, computed, onMounted, onBeforeUnmount, watch } from 'vue';
import axios from 'axios';
import WaveSurfer from 'wavesurfer.js';
import IconMic from '@/components/icons/IconMic.vue';
import IconStop from '@/components/icons/IconStop.vue';
import IconEar from '@/components/icons/IconEar.vue';
import IconVolume from '@/components/icons/IconVolume.vue';

const apiData = ref([]);
const text_list = ref([]);
const ipa_text_list = ref([]);
const audio_list = ref([]);
const currentIndex = ref(0);
const progress = ref(0);
const isRecording = ref(false);
const recordedAudio = ref(null);
const mediaRecorder = ref(null);
const recordedChunks = ref([]);
const audioSaved = ref(false);
const activeButton = ref(null);
const getalldata = ref(false);
const length_data = ref(0);
const wavesurfer = ref(null);
const animationFrameId = ref(null);

const score = ref(0);
const percentage = ref(0);
const sentence = ref('');
const coloredWords = ref([]);
const words_scores = ref([]);
const check_words = ref(false);
const display_words = ref('none');
const size_words = ref(25);
const topmr = ref(20);
const error_char_indexes = ref([])
const color_ipa = ref([]);

var synth = window.speechSynthesis;
let prediction = ref('');
const fetchData = async () => {
  try {
    const response = await axios.get('/api/getData');
    text_list.value = response.data.text_list;
    ipa_text_list.value = response.data.ipa_text_list;

  } catch (error) {
    console.error('Lỗi khi lấy dữ liệu:', error);
  }
};

const currentSentence = computed(() => {
  return text_list.value[currentIndex.value] || '';
});

const current_ipa_text = computed(() => {
  return ipa_text_list.value[currentIndex.value] || '';
});
function generateColoredWords() {
  const words = currentSentence.value.split(' ');
  coloredWords.value = []; // Đặt lại mảng coloredWords trước khi thêm các từ mới
  if (check_words.value)
  {
    for (let i = 0; i < words.length; i++) {
      // const score = Math.random();
      let color;
      if (words_scores.value[i] >= 0.8) {
        color = 'green';
      } else if (words_scores.value[i] < 0.5) {
        color = 'red';
      } else {
        color = 'yellow';
      }
      coloredWords.value.push({ word: words[i], color: color });
    }
  }else{
    for (let i = 0; i < words.length; i++) {
      coloredWords.value.push({ word: words[i], color: "black" });
    }
  }
}

function generateColorIPA_text(){
  const ipa_text = current_ipa_text.value.split('');
  color_ipa.value = [];
  let color = 'black';
  let ipa_count = 0;
  for (let i = 0; i < ipa_text.length; i++) {
      if (ipa_text[i] !== ' ' && ipa_text[i] !== 'ˈ' && ipa_text[i] !== 'ˌ') {
        if (error_char_indexes.value[ipa_count] == false) {
          color = 'red';
        } else {
          color = 'green';
        }
        ipa_count++;
      }
    color_ipa.value.push({ char: ipa_text[i], color: color });
  }
  
  }

  function check(){
    if (check_words){
      generateColorIPA_text();
    }
  }


const animateScore = (start, end, duration) => {
  const stepTime = Math.abs(Math.floor(duration / (end - start + 0.001)));
  let current = start;
  const increment = end > start ? 1 : -1;
  const timer = setInterval(() => {
    current += increment;
    percentage.value = current;
    if (current === end) {
      clearInterval(timer);
    }
  }, stepTime);
};

watch(currentSentence, (newValue) => {
  sentence.value = newValue;
  generateColoredWords(); // Cập nhật colored words mỗi khi câu thay đổi
});

// ============================================
const initWaveSurfer = () => {
  wavesurfer.value = WaveSurfer.create({
    container: '#waveform',
    waveColor: 'red',
    progressColor: '#58cc02',
    cursorWidth: 0,
    height: 100,
    responsive: true,
    backend: 'WebAudio',
  });

  wavesurfer.value.on('ready', () => {
    console.log('WaveSurfer is ready');
  });
  wavesurfer.value.on('error', (e) => {
    console.error(e);
  });
};

const setActive = (button) => {
  activeButton.value = button;
};

const playRecordedAudio = () => {
  if (recordedChunks.value.length > 0 && !wavesurfer.value.isPlaying()) {
    let recordedBlob = new Blob(recordedChunks.value, { type: 'audio/ogg' });
    const audioUrl = URL.createObjectURL(recordedBlob);
    const audioPlayer = new Audio(audioUrl);
    audioPlayer.play();
    wavesurfer.value.load(audioUrl);
    wavesurfer.value.on('ready', () => {
      wavesurfer.value.play();
      startAnimation();
    });

    wavesurfer.value.on('finish', () => {
      stopAnimation();
    });
  } else {
    console.error('Không có file âm thanh được ghi.');
  }
};

const playSampleAudio = () => {
  playWithMozillaApi(text_list.value[currentIndex.value]);
};

const playWithMozillaApi = (text) => {
  var utterThis = new SpeechSynthesisUtterance(text);
      utterThis.voice = null;
      utterThis.rate = 0.7;
      utterThis.onend = function (event) {
          // unblockUI();
      }
      synth.speak(utterThis);
}

const startRecording = () => {
  document.getElementById("record-button").style.display = "none";
  document.getElementById("stop-button").style.display = "flex";

  navigator.mediaDevices.getUserMedia({ audio: true })
    .then(stream => {
      mediaRecorder.value = new MediaRecorder(stream);
      recordedChunks.value = [];

      mediaRecorder.value.ondataavailable = event => {
        recordedChunks.value.push(event.data);
      };

      mediaRecorder.value.onstop = async () => { sendAudio() };

      mediaRecorder.value.start();

      setTimeout(() => {
        stopRecording();
      }, 5000);
    })
    .catch(error => {
      console.error('Lỗi truy cập microphone:', error);
    });
};

const stopRecording = () => {
  document.getElementById("record-button").style.display = "flex";
  document.getElementById("stop-button").style.display = "none";

  if (mediaRecorder.value && mediaRecorder.value.state !== 'inactive') {
    mediaRecorder.value.stop();
  }

  // clearTimeout(timeout);
};

const sendAudio = async () => {
  const convertBlobToBase64 = async (blob) => {
    return await blobToBase64(blob);
  };

  const blobToBase64 = blob => new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.readAsDataURL(blob);
    reader.onload = () => resolve(reader.result);
    reader.onerror = error => reject(error);
  });

  if (recordedChunks.value.length > 0) {
    let audioBlob = new Blob(recordedChunks.value, { type: 'audio/ogg' });
    let audioBase64 = await convertBlobToBase64(audioBlob);

    let minimumAllowedLength = 6;
    if (audioBase64.length < minimumAllowedLength) {
      setTimeout(() => { console.error('File audio quá ngắn.'); }, 50);
      return;
    }

    try {
      const response = await axios.post('/api/GetAccuracyFromRecordedAudio', JSON.stringify({ "title": text_list.value[currentIndex.value], "base64Audio": audioBase64 }), {
        headers: {
          'Content-Type': 'multipart/form-data'
        }
      });
      console.log('File âm thanh đã được gửi thành công.', response);
      score.value = await response.data.score*100;
      percentage.value = await response.data.score*100;
      animateScore(0, score.value, 600);
      words_scores.value = await response.data.word_scores;
      check_words.value = true;
      generateColoredWords();
      display_words.value = 'block';
      console.log('word_scores',words_scores.value);
      error_char_indexes.value = await response.data.error_char_indexes;
      // current_ipa_text.value = await response.data.label_string;
      prediction.value = await response.data.pred_string;
      // console.log(prediction.value);
      check();
     

    } catch (error) {
      console.error('Lỗi khi gửi file âm thanh:', error);
    }
  } else {
    console.error('Không gửi được file âm thanh.');
  }
};

const nextSentence = () => {
  if (currentIndex.value < text_list.value.length - 1) {
    currentIndex.value++;
    progress.value = (currentIndex.value / (text_list.value.length - 1)) * 100;
    check_words.value = false;
    generateColoredWords();
    display_words.value = 'none';
    score.value = 0;
    percentage.value = 0;
  }
};

const previousSentence = () => {
  if (currentIndex.value > 0) {
    currentIndex.value--;
    progress.value = (currentIndex.value / (text_list.value.length - 1)) * 100;
    check_words.value = false;
    generateColoredWords();
    display_words.value = 'none';
    score.value = 0;
    percentage.value = 0;
    }
};

const updateProgress = () => {
  const currentTime = wavesurfer.value.getCurrentTime();
  const duration = wavesurfer.value.getDuration();
};

const startAnimation = () => {
  const animate = () => {
    updateProgress();
    animationFrameId.value = requestAnimationFrame(animate);
  };
  animationFrameId.value = requestAnimationFrame(animate);
};

const stopAnimation = () => {
  if (animationFrameId.value) {
    cancelAnimationFrame(animationFrameId.value);
    animationFrameId.value = null;
  }
};

onMounted(() => {
  fetchData();
  initWaveSurfer();
  generateColoredWords();
});

onBeforeUnmount(() => {
  if (wavesurfer.value) {
    wavesurfer.value.destroy();
  }
  stopAnimation();
});
</script>

<style scoped>
@import './../assets/home.css';
</style>
