<template>
  <div class="ui-page">
    <header v-if="showHeader" class="ui-header">
      <div v-if="container" class="ui-container">
        <div class="ui-header-inner">
          <div class="ui-header-left">
            <button
              v-if="showBack"
              class="ui-btn ui-btn-secondary"
              type="button"
              @click="onBack"
            >
              <slot name="back">
                <span>←</span>
                <span>{{ backText }}</span>
              </slot>
            </button>

            <div style="min-width: 0;">
              <h1 class="ui-title">{{ title }}</h1>
              <div v-if="subtitle" class="ui-subtitle">{{ subtitle }}</div>
            </div>
          </div>

          <div class="ui-header-right">
            <slot name="right" />
          </div>
        </div>
      </div>
      <div v-else>
        <div class="ui-header-inner">
          <div class="ui-header-left">
            <button
              v-if="showBack"
              class="ui-btn ui-btn-secondary"
              type="button"
              @click="onBack"
            >
              <slot name="back">
                <span>←</span>
                <span>{{ backText }}</span>
              </slot>
            </button>

            <div style="min-width: 0;">
              <h1 class="ui-title">{{ title }}</h1>
              <div v-if="subtitle" class="ui-subtitle">{{ subtitle }}</div>
            </div>
          </div>

          <div class="ui-header-right">
            <slot name="right" />
          </div>
        </div>
      </div>
    </header>

    <main :class="padded ? 'ui-main' : ''">
      <div v-if="container" class="ui-container">
        <slot />
      </div>
      <slot v-else />
    </main>
  </div>
</template>

<script setup>
import { useRouter } from 'vue-router'

const props = defineProps({
  title: { type: String, default: '' },
  subtitle: { type: String, default: '' },
  showHeader: { type: Boolean, default: true },
  container: { type: Boolean, default: true },
  padded: { type: Boolean, default: true },
  showBack: { type: Boolean, default: false },
  backText: { type: String, default: '返回' },
  backTo: { type: [String, Object], default: '' }
})

const router = useRouter()

const onBack = () => {
  if (props.backTo) {
    router.push(props.backTo)
    return
  }

  if (window.history.length > 1) {
    router.back()
    return
  }

  router.push('/home')
}
</script>
