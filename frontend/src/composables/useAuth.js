import { ref, computed } from 'vue'
import api from '@/api'

const user = ref(null)
const isLoading = ref(false)
const isAuthenticated = computed(() => !!user.value)

export function useAuth() {
  const checkAuth = async () => {
    isLoading.value = true
    try {
      const response = await api.checkAuth()
      if (response.data.authenticated) {
        user.value = response.data.user
      } else {
        user.value = null
      }
    } catch (error) {
      user.value = null
    } finally {
      isLoading.value = false
    }
    return isAuthenticated.value
  }

  const loginWithGoogle = () => {
    const apiBaseUrl = import.meta.env.VITE_API_BASE_URL || '/api'
    window.location.href = apiBaseUrl + '/auth/google'
  }

  const logout = async () => {
    try {
      await api.logout()
    } catch (error) {
      console.error('Logout error:', error)
    } finally {
      user.value = null
    }
  }

  return {
    user,
    isLoading,
    isAuthenticated,
    checkAuth,
    loginWithGoogle,
    logout
  }
}
