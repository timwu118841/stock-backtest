import { ref, watchEffect } from 'vue'

const THEME_KEY = 'stock-app-theme'
const isDark = ref(localStorage.getItem(THEME_KEY) === 'dark')

export function useTheme() {
  const toggleTheme = () => {
    isDark.value = !isDark.value
  }

  watchEffect(() => {
    const htmlEl = document.documentElement
    if (isDark.value) {
      htmlEl.classList.add('dark')
      localStorage.setItem(THEME_KEY, 'dark')
    } else {
      htmlEl.classList.remove('dark')
      localStorage.setItem(THEME_KEY, 'light')
    }
  })

  return {
    isDark,
    toggleTheme
  }
}
