<template>
  <div class="login-page">
    <div class="login-container">
      <div class="brand-panel">
        <div class="brand-header">
          <img src="/logo.svg" alt="Northstar One" class="logo" />
          <div>
            <h1 class="title">Northstar One</h1>
            <p class="subtitle">A mission-control terminal for personal investing</p>
          </div>
        </div>
        <div class="brand-points">
          <div class="point-item">
            <span class="dot"></span>
            多智能体协作分析，一次生成完整投研链路
          </div>
          <div class="point-item">
            <span class="dot"></span>
            研究、风控、执行建议同屏输出
          </div>
          <div class="point-item">
            <span class="dot"></span>
            面向个人投资者的极简任务编排
          </div>
        </div>
      </div>
      <el-card class="login-card" shadow="always">
        <div class="form-head">
          <h2>欢迎进入终端</h2>
          <p>登录后继续你的研究任务流</p>
        </div>
        <el-form
          :model="loginForm"
          :rules="loginRules"
          ref="loginFormRef"
          label-position="top"
          size="large"
        >
          <el-form-item label="用户名" prop="username">
            <el-input
              v-model="loginForm.username"
              placeholder="请输入用户名"
              prefix-icon="User"
            />
          </el-form-item>

          <el-form-item label="密码" prop="password">
            <el-input
              v-model="loginForm.password"
              type="password"
              placeholder="请输入密码"
              prefix-icon="Lock"
              show-password
              @keyup.enter="handleLogin"
            />
          </el-form-item>

          <el-form-item>
            <div class="form-options">
              <el-checkbox v-model="loginForm.rememberMe">
                记住我
              </el-checkbox>
            </div>
          </el-form-item>

          <el-form-item>
            <el-button
              type="primary"
              size="large"
              style="width: 100%"
              :loading="loginLoading"
              @click="handleLogin"
            >
              进入指挥台
            </el-button>
          </el-form-item>

          <el-form-item>
            <div class="login-tip">
              <el-text type="info" size="small">
                开源版默认账号：admin / admin123
              </el-text>
            </div>
          </el-form-item>
        </el-form>
      </el-card>
    </div>

    <div class="login-footer">
      <p>&copy; 2025 Northstar One. All rights reserved.</p>
      <p class="disclaimer">
        Northstar One 是一个 AI 多智能体投研平台。平台中的分析结论、观点和“投资建议”均由 AI 自动生成，仅用于学习、研究与交流，不构成任何形式的投资建议或承诺。用户据此进行的任何投资行为及其产生的风险与后果，均由用户自行承担。市场有风险，入市需谨慎。
      </p>
    </div>
  </div>
</template>

<script setup lang="ts">
import { reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { useAuthStore } from '@/stores/auth'

const router = useRouter()
const authStore = useAuthStore()

const loginFormRef = ref()
const loginLoading = ref(false)

const loginForm = reactive({
  username: '',
  password: '',
  rememberMe: false
})

const loginRules = {
  username: [
    { required: true, message: '请输入用户名', trigger: 'blur' }
  ],
  password: [
    { required: true, message: '请输入密码', trigger: 'blur' },
    { min: 6, message: '密码长度不能少于6位', trigger: 'blur' }
  ]
}

const handleLogin = async () => {
  // 防止重复提交
  if (loginLoading.value) {
    console.log('⏭️ 登录请求进行中，跳过重复点击')
    return
  }

  try {
    await loginFormRef.value.validate()

    loginLoading.value = true
    console.log('🔐 开始登录流程...')

    // 调用真实的登录API
    const success = await authStore.login({
      username: loginForm.username,
      password: loginForm.password
    })

    if (success) {
      console.log('✅ 登录成功')
      ElMessage.success('登录成功')

      // 跳转到重定向路径或仪表板
      const redirectPath = authStore.getAndClearRedirectPath()
      console.log('🔄 重定向到:', redirectPath)
      router.push(redirectPath)
    } else {
      ElMessage.error('用户名或密码错误')
    }

  } catch (error) {
    console.error('登录失败:', error)
    // 只有在不是表单验证错误时才显示错误消息
    if (error.message && !error.message.includes('validate')) {
      ElMessage.error('登录失败，请重试')
    }
  } finally {
    loginLoading.value = false
  }
}


</script>

<style lang="scss" scoped>
.login-page {
  min-height: 100vh;
  background:
    radial-gradient(circle at 14% 16%, rgba(22, 146, 158, 0.15), transparent 35%),
    radial-gradient(circle at 92% 8%, rgba(215, 137, 69, 0.18), transparent 28%),
    linear-gradient(145deg, #f2f6fb 0%, #eef4f9 55%, #f7fafc 100%);
  display: grid;
  grid-template-rows: 1fr auto;
  align-items: center;
  justify-items: center;
  padding: 24px;
}

.login-container {
  width: 100%;
  max-width: 980px;
  display: grid;
  grid-template-columns: 1.1fr 0.9fr;
  gap: 20px;
  align-items: stretch;
}

.brand-panel {
  background: linear-gradient(145deg, #0f2f45 0%, #0f4458 42%, #13606b 100%);
  border-radius: 22px;
  padding: 32px 30px;
  color: #eff8ff;
  box-shadow: 0 24px 44px rgba(12, 40, 60, 0.25);
  display: flex;
  flex-direction: column;
  justify-content: space-between;

  .brand-header {
    display: flex;
    align-items: center;
    gap: 14px;
  }

  .title {
    font-size: 36px;
    font-weight: 700;
    margin: 0 0 8px 0;
    letter-spacing: -0.02em;
  }

  .subtitle {
    font-size: 14px;
    opacity: 0.88;
    margin: 0;
  }

  .logo {
    width: 64px;
    height: 64px;
    filter: drop-shadow(0 8px 20px rgba(11, 25, 39, 0.4));
  }

  .brand-points {
    margin-top: 28px;
    display: flex;
    flex-direction: column;
    gap: 16px;
  }

  .point-item {
    display: flex;
    align-items: center;
    gap: 10px;
    font-size: 14px;
    color: rgba(235, 246, 255, 0.94);
  }

  .dot {
    width: 8px;
    height: 8px;
    border-radius: 50%;
    background: #6fdbd1;
    box-shadow: 0 0 0 5px rgba(111, 219, 209, 0.18);
  }
}

.login-card {
  border: 1px solid rgba(141, 170, 198, 0.34);
  border-radius: 20px;
  backdrop-filter: blur(12px);
  box-shadow: 0 24px 44px rgba(27, 52, 74, 0.13);

  :deep(.el-card__body) {
    padding: 28px 26px 22px;
  }

  .form-head {
    margin-bottom: 12px;

    h2 {
      margin: 0;
      font-size: 24px;
      color: #18304a;
      font-family: var(--app-title-font);
    }

    p {
      margin: 6px 0 0;
      color: #6a7f96;
      font-size: 13px;
    }
  }

  .form-options {
    display: flex;
    justify-content: space-between;
    align-items: center;
    width: 100%;
  }

  .login-tip {
    text-align: center;
    width: 100%;
    color: var(--el-text-color-regular);
  }
}

.login-footer {
  text-align: center;
  margin-top: 18px;
  color: #4f6076;
  opacity: 0.95;

  p {
    margin: 0;
    font-size: 14px;
  }

  .disclaimer {
    margin-top: 10px;
    font-size: 12px;
    line-height: 1.6;
    max-width: 920px;
    margin-left: auto;
    margin-right: auto;
    color: #61738a;
    opacity: 0.95;
  }
}

@media (max-width: 900px) {
  .login-container {
    grid-template-columns: 1fr;
    max-width: 480px;
  }

  .brand-panel {
    padding: 22px;
  }
}
</style>
